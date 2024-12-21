from typing import Dict, Any, Optional, List
import json
import io
import os
import base64
import queue
import threading
import time
import asyncio
from getpass import getpass
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException, Depends, File, UploadFile, Form, Request, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# 导入 Agent 类
from agents.teacher_agent import TeacherAgent
from agents.student_agent import StudentAgent
from agents.knowledge_crawler_agent import KnowledgeCrawlerAgent
from agents.faq_generator_agent import FAQGeneratorAgent
from agents.quiz_generator_agent import QuizGeneratorAgent
from agents.admin_agent import AdminAgent
# from agents.multimodal_agent import MultimodalAgent # 可选：如果你需要处理多模态问题

# 导入工具类
from tools.duckduckgo_search import DuckDuckGoSearchTool
from tools.web_scraper import WebScraperTool

from camel.messages import BaseMessage
from camel.configs import QwenConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.utils.commons import build_tool_reponse
from camel.loaders import ChunkrReader, Firecrawl, load_yaml

import requests
from bs4 import BeautifulSoup
from io import BytesIO
import requests
from PIL import Image

# ===================== 数据库模型 =====================
Base = declarative_base()

class StudyRecord(Base):
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    content = Column(String)
    response = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# ===================== 数据库操作 =====================
DATABASE_URL = "sqlite:///./study_records.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================== Pydantic 模型 =====================
class AskRequest(BaseModel):
    student_id: str
    question: str
    agent_name: str
    topic: Optional[str] = None

class ToolRequest(BaseModel):
    tool_name: str
    tool_params: str

class TextToSpeechRequest(BaseModel):
    text: str
    model_id: Optional[str] = "zh-CN-XiaoxiaoNeural"

class SpeechToTextRequest(BaseModel):
    audio_file: str

class AdminRequest(BaseModel):
    action: str
    params: Optional[Dict] = None

class StudentInteractRequest(BaseModel):
    sender_id: str
    receiver_id: str
    action: str
    content: Optional[str] = None

class ChunkrUploadRequest(BaseModel):
    file: UploadFile = File(...)

class FirecrawlScrapeRequest(BaseModel):
    url: str
    response_format: Dict = None

class FirecrawlMapRequest(BaseModel):
    url: str

class MultimodalRequest(BaseModel):
    question: str
    image: str  # Base64 encoded image

# ===================== 全局消息队列 =====================
message_queue = queue.Queue()
MAX_MESSAGES = 100  # 最多保存的消息数量

# ===================== WebSocket 管理 =====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 发送所有 Agent 的初始状态
        await self.broadcast_agent_status()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_agent_status(self):
        """广播所有 Agent 的状态"""
        status_data = {
            "type": "agent_status",
            "data": {
                agent_name: agent.status for agent_name, agent in agents.items()
            }
        }
        await self.broadcast(json.dumps(status_data))

manager = ConnectionManager()

# ===================== FastAPI 应用 =====================
app = FastAPI()

# CORS 设置
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://your-vercel-app.vercel.app",  # 替换为你的 Vercel 前端地址
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 实例化 Agent =====================
# 创建一个字典来存储 Agent 实例
agents: Dict[str, Any] = {}

# 实例化 Agent 并添加到字典中
agents["teacher_agent"] = TeacherAgent()
agents["student_agent_1"] = StudentAgent("student_agent_1", "Alice", "Visual", "Low", "student_agent_2")
agents["student_agent_2"] = StudentAgent("student_agent_2", "Bob", "Auditory", "Medium", "student_agent_1")
agents["knowledge_crawler_agent"] = KnowledgeCrawlerAgent()
agents["faq_generator_agent"] = FAQGeneratorAgent()
agents["quiz_generator_agent"] = QuizGeneratorAgent()
agents["admin_agent"] = AdminAgent()
# agents["multimodal_agent"] = MultimodalAgent()  # 可选

# 设置 Agent 之间的关联
agents["teacher_agent"].set_knowledge_crawler_agent(agents["knowledge_crawler_agent"])
agents["teacher_agent"].set_faq_generator_agent(agents["faq_generator_agent"])
agents["teacher_agent"].set_quiz_generator_agent(agents["quiz_generator_agent"])

# ===================== API 接口 =====================

@app.get("/api/messages")
async def get_messages(db: Session = Depends(get_db)):
    """获取所有消息."""
    db_messages = db.query(Message).order_by(Message.timestamp.desc()).all()
    messages = [
        {
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        } for msg in db_messages
    ]
    return messages

@app.post("/api/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """学生提问接口."""
    # 根据 agent_name 选择对应的 Agent
    agent = agents.get(request.agent_name)
    if agent is None:
        raise HTTPException(status_code=400, detail=f"Invalid agent name: {request.agent_name}")

    # 记录学生的问题
    student_message = Message(
        sender="Student",
        content=request.question,
        timestamp=datetime.now()
    )
    db.add(student_message)
    db.commit()

    # 调用 Agent 的 step 方法处理问题
    student_msg = BaseMessage(role_name="Student", role_type="USER", meta_dict=None, content=request.question)

    if isinstance(agent, TeacherAgent):
        teacher_response = agent.step(student_msg, request.topic)
        response_content = teacher_response.content

        # 记录学习记录
        study_record = StudyRecord(
            student_id=request.student_id,
            content=request.question,
            response=response_content,
            timestamp=datetime.now()
        )
        db.add(study_record)

        # 记录教师回复
        teacher_message = Message(
            sender=request.agent_name,
            content=response_content,
            timestamp=datetime.now()
        )
        db.add(teacher_message)
        db.commit()

    elif isinstance(agent, StudentAgent):
        teacher_agent = agents.get("teacher_agent")
        if teacher_agent is None:
            raise HTTPException(status_code=500, detail="Teacher agent not found.")

        teacher_response = teacher_agent.generate_response(student_msg, request.topic)
        student_response = agent.step(teacher_response)
        response_content = student_response.content

        # 记录学生回复
        response_message = Message(
            sender=request.agent_name,
            content=response_content,
            timestamp=datetime.now()
        )
        db.add(response_message)
        db.commit()

    else:
        response = agent.step(student_msg)
        response_content = response.content
        
        # 记录 Agent 回复
        response_message = Message(
            sender=request.agent_name,
            content=response_content,
            timestamp=datetime.now()
        )
        db.add(response_message)
        db.commit()

    # 广播消息到 WebSocket 连接
    await manager.broadcast(json.dumps({
        "type": "message",
        "data": {
            "sender": request.agent_name,
            "content": response_content,
            "timestamp": datetime.now().isoformat()
        }
    }))

    return {"answer": response_content}

@app.post("/api/interact")
async def student_interact(request: StudentInteractRequest, db: Session = Depends(get_db)):
    """学生互动接口."""
    sender = agents.get(request.sender_id)
    receiver = agents.get(request.receiver_id)

    if sender is None or receiver is None:
        raise HTTPException(status_code=400, detail="Invalid sender or receiver ID.")

    if not isinstance(sender, StudentAgent) or not isinstance(receiver, StudentAgent):
        raise HTTPException(status_code=400, detail="Sender and receiver must be Student Agents.")

    # 记录互动消息到数据库
    interaction_message = Message(
        sender=sender.name,
        content=request.content,
        timestamp=datetime.now()
    )
    db.add(interaction_message)
    db.commit()

    # 将互动消息放入队列
    message_queue.put({
        "agent": sender,
        "message": BaseMessage(
            role_name=sender.name,
            role_type="USER",
            meta_dict=None,
            content=json.dumps({
                'action': request.action,
                'content': request.content,
                'receiver': request.receiver_id
            })
        ),
        "topic": None
    })

    # 广播消息到 WebSocket 连接
    await manager.broadcast(json.dumps({
        "type": "message",
        "data": {
            "sender": sender.name,
            "content": request.content,
            "timestamp": interaction_message.timestamp.isoformat()
        }
    }))

    return {"message": "Interaction message added to queue and database."}

@app.post("/api/tools/search")
async def use_search_tool(request: ToolRequest):
    """使用 DuckDuckGo 搜索工具."""
    teacher_agent = agents.get("teacher_agent")
    result = teacher_agent.use_tool("DuckDuckGoSearchTool", request.tool_params)
    return {"result": result}

@app.post("/api/tools/scrape")
async def use_scrape_tool(request: ToolRequest):
    """使用网页抓取工具."""
    teacher_agent = agents.get("teacher_agent")
    result = teacher_agent.use_tool("WebScraperTool", request.tool_params)
    return {"result": result}

@app.post("/api/admin")
async def admin_action(request: AdminRequest):
    """管理员操作接口."""
    admin_agent = agents.get("admin_agent")
    if admin_agent is None:
        raise HTTPException(status_code=500, detail="Admin agent not found.")

    response = admin_agent.step(BaseMessage(role_name="Admin", role_type="USER", meta_dict=None, content=json.dumps({
        'action': request.action,
        'params': request.params
    })))
    return {"result": response.content}

@app.post("/api/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件并使用 Chunkr 处理."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    # 使用临时文件存储上传的 PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(await file.read())
        pdf_path = tmp_file.name

    # 使用 ChunkrReader 处理 PDF
    chunkr_reader = ChunkrReader()
    chunkr_reader.submit_task(file_path=pdf_path)
    
    # 获取任务 ID 并返回 (这里需要根据你的 Chunkr 使用方式进行调整)
    task_id = chunkr_reader.get_task_id(file_path=pdf_path) #你需要实现 get_task_id 这个函数

    # 删除临时文件
    os.remove(pdf_path)

    return {"task_id": task_id, "message": "PDF uploaded and processing started."}

@app.post("/api/scrape_structured")
async def scrape_structured(request: FirecrawlScrapeRequest):
    """使用 Firecrawl 进行结构化抓取."""
    firecrawl = Firecrawl()
    try:
        response = firecrawl.structured_scrape(
            url=request.url,
            response_format=request.response_format
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firecrawl structured scrape error: {e}")

@app.post("/api/map_site")
async def map_site(request: FirecrawlMapRequest):
    """使用 Firecrawl 抓取网站地图."""
    firecrawl = Firecrawl()
    try:
        response = firecrawl.map_site(url=request.url)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firecrawl map site error: {e}")

@app.post("/api/multimodal")
async def handle_multimodal_question(request: MultimodalRequest):
    """处理包含图片的多模态问题."""
    try:
        # 解码 base64 图片
        image_data = base64.b64decode(request.image)
        img = Image.open(io.BytesIO(image_data))
    
        # 创建 Qwen-VL 模型实例
        qwen_vl_model = ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_VL_PLUS,
            model_config_dict=QwenConfig(temperature=0.2).as_dict(),
        )
    
        # 创建 Multimodal Agent 实例（如果尚不存在）
        if "multimodal_agent" not in agents:
            agents["multimodal_agent"] = MultimodalAgent(qwen_vl_model)
    
        # 构建消息
        user_msg = BaseMessage.make_user_message(
            role_name="User", content=request.question, image_list=[img]
        )
    
        # 获取回答
        response = agents["multimodal_agent"].step(user_msg)
        return {"answer": response.msgs[0].content}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multimodal processing error: {e}")

@app.get("/test_model")
async def test_model():
    teacher_agent = agents.get("teacher_agent")
    test_message = BaseMessage(role_name="Test", role_type="USER", meta_dict=None, content="What is the capital of France?")
    response = teacher_agent.generate_response(test_message, None)
    return {"response": response.content}

@app.get("/records", response_model=List[Dict])
async def get_records(db: Session = Depends(get_db)):
    records = db.query(StudyRecord).all()
    return [
        {
            "id": record.id,
            "student_id": record.student_id,
            "content": record.content,
            "response": record.response,
            "timestamp": record.timestamp.isoformat(),
        }
        for record in records
    ]

@app.post("/api/text_to_speech")
async def text_to_speech(request: TextToSpeechRequest):
    """文本转语音接口."""
    try:
        fish_audio_api_url = os.environ.get("FISH_AUDIO_API")
        fish_audio_api_key = os.environ.get("FISH_AUDIO_API_KEY")
        headers = {
            "Authorization": f"Bearer {fish_audio_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": request.text,
            "speaker_id": request.model_id,  # 使用预设的模型 ID
            "speed": 1.0, # 语速
        }
        response = requests.post(fish_audio_api_url, headers=headers, json=payload)
        response.raise_for_status()
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")

        return {"audio_data": audio_base64}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # 发送现有消息历史
        await websocket.send_text(json.dumps({
            "type": "history",
            "messages": await get_messages()
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                print(f"Received message over WebSocket: {message_data}")
                # 这里可以根据需要处理接收到的消息
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# 启动命令: uvicorn main:app --reload --port 8000

# ===================== Agent 线程 =====================
def agent_task(agent, message_queue):
    while True:
        try:
            task = message_queue.get(timeout=1)
        except queue.Empty:
            continue

        agent = task["agent"]
        message = task["message"]
        topic = task["topic"]

        if message.content == "INTERRUPT":
            print(f"Interrupt signal received for {agent.role_name}. Stopping current operation.")
            agent.reset()
            # 广播状态更新
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(manager.broadcast_agent_status())
            finally:
                loop.close()
            continue

        try:
            if isinstance(agent, TeacherAgent):
                response = agent.step(message, topic)
            elif isinstance(agent, StudentAgent):
                try:
                    msg_content = json.loads(message.content)
                    action = msg_content.get("action")
                    content = msg_content.get("content")
                    receiver_id = msg_content.get("receiver")
                    if action and receiver_id:
                        receiver = agents.get(receiver_id)
                        if action == "ask_question":
                            agent.interact_with_peer(receiver, "ask_question", content)
                            response = BaseMessage(role_name=agent.name, role_type="USER", meta_dict=None, content="你的问题已发送")
                        elif action == "send_message":
                            agent.interact_with_peer(receiver, "send_message", content)
                            response = BaseMessage(role_name=agent.name, role_type="USER", meta_dict=None, content="你的消息已发送")
                        elif action == "test":
                            agent.interact_with_peer(receiver, "test", content)
                            response = BaseMessage(role_name=agent.name, role_type="USER", meta_dict=None, content="已发起测试")
                        elif action == "check_records":
                            agent.interact_with_peer(receiver, "check_records")
                            response = BaseMessage(role_name=agent.name, role_type="USER", meta_dict=None, content="已查看对方记录")
                        else:
                            response = BaseMessage(role_name=agent.name, role_type="USER", meta_dict=None, content="未知互动类型")
                    else:
                        response = agent.step(message)
                except:
                    response = agent.step(message)
            else:
                response = agent.step(message)

            # 获取数据库会话
            db = SessionLocal()
            try:
                # 记录 Agent 响应到数据库
                db_message = Message(
                    sender=agent.system_message.role_name,
                    content=response.content,
                    timestamp=datetime.now()
                )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)

                # 创建事件循环来发送 WebSocket 消息
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 发送消息和状态更新
                    loop.run_until_complete(asyncio.gather(
                        manager.broadcast(json.dumps({
                            "type": "message",
                            "data": {
                                "sender": agent.system_message.role_name,
                                "content": response.content,
                                "timestamp": db_message.timestamp.isoformat()
                            }
                        })),
                        manager.broadcast_agent_status()
                    ))
                except Exception as e:
                    print(f"Error broadcasting message: {e}")
                finally:
                    loop.close()
            except Exception as e:
                print(f"Error saving message to database: {e}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            print(f"Error in agent task: {e}")
            if hasattr(agent, 'set_status'):
                agent.set_status(AgentStatus.ERROR, str(e))
                # 广播错误状态
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(manager.broadcast_agent_status())
                finally:
                    loop.close()

        message_queue.task_done()

# 创建并启动 Agent 线程
for agent_name, agent in agents.items():
    thread = threading.Thread(target=agent_task, args=(agent, message_queue))
    thread.daemon = True
    thread.start()