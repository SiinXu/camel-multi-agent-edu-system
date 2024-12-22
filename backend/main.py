from datetime import datetime
import json
import os
import asyncio
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from models import Base, Message, StudyRecord
from schemas import (
    AskRequest, StudentInteractRequest, ToolRequest, TextToSpeechRequest,
    AdminRequest, FirecrawlScrapeRequest, FirecrawlMapRequest,
    MultimodalRequest, MessageSchema, StudySession, ChatMessage
)
from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
from agents.knowledge_crawler_agent import KnowledgeCrawlerAgent
from agents.faq_generator_agent import FAQGeneratorAgent
from agents.quiz_generator_agent import QuizGeneratorAgent
from agents.coordinator_agent import CoordinatorAgent
from core.blackboard import Blackboard

# 创建异步数据库引擎
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建异步会话工厂
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 创建数据库会话依赖
async def get_db():
    async with SessionLocal() as session:
        yield session

# 创建数据库表
async def init_db():
    async with engine.begin() as conn:
        # 删除所有表
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

# 全局变量
agents = {}
connected_clients = set()

# FastAPI 应用
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== 智能教育系统后端服务器 ===")
    print("* 数据库初始化完成")
    print("* CORS 中间件配置完成")
    print("* WebSocket 管理器初始化完成")
    
    # 初始化数据库
    await init_db()
    
    # ===================== 初始化 Agent =====================
    from agents.teacher_agent import TeacherAgent
    from agents.knowledge_crawler_agent import KnowledgeCrawlerAgent
    from agents.faq_generator_agent import FAQGeneratorAgent
    from agents.quiz_generator_agent import QuizGeneratorAgent
    from agents.coordinator_agent import CoordinatorAgent
    from core.blackboard import Blackboard

    # 创建共享黑板
    blackboard = Blackboard()

    # 初始化协调者 Agent
    coordinator = CoordinatorAgent("coordinator", blackboard)
    
    # 初始化其他 Agents
    agents_to_register = {
        "teacher_agent": TeacherAgent(blackboard=blackboard, agent_id="teacher_agent"),
        "knowledge_crawler": KnowledgeCrawlerAgent(blackboard=blackboard, agent_id="knowledge_crawler"),
        "faq_generator": FAQGeneratorAgent(blackboard=blackboard, agent_id="faq_generator"),
        "quiz_generator": QuizGeneratorAgent(blackboard=blackboard, agent_id="quiz_generator")
    }

    # 注册所有 Agent
    global agents
    agents = {"coordinator": coordinator}
    for agent_id, agent in agents_to_register.items():
        print(f"* 注册 Agent: {agent_id}")
        await coordinator.register_agent(agent)
        agents[agent_id] = agent

    # 启动所有 Agent
    for agent_id, agent in agents.items():
        print(f"* 启动 Agent: {agent_id}")
        await agent.start()

    print("* 所有代理初始化完成")
    print(f"服务器运行在: http://localhost:8002")
    print(f"API 文档地址: http://localhost:8002/docs")
    print("==============================")
    yield
    print("正在关闭服务器...")

app = FastAPI(lifespan=lifespan)

# ===================== API 路由 =====================
@app.post("/api/ask")
async def ask_question(request: AskRequest, db: AsyncSession = Depends(get_db)):
    """处理用户的问题请求."""
    try:
        # 记录学生的问题
        print(f"Received request: student_id={request.student_id}, question={request.question}, agent_name={request.agent_name}")
        
        # 保存学生消息
        message = Message(
            student_id=request.student_id,
            content=request.question,
            sender=request.student_id,
            role="user",
            timestamp=datetime.now()
        )
        db.add(message)
        await db.commit()
        print(f"Saved student message: {request.question}")
        
        # 获取指定的 Agent
        agent = agents.get(request.agent_name)
        if not agent:
            return {"status": "error", "message": f"Agent {request.agent_name} not found"}
        print(f"Found agent: {request.agent_name}")
        
        # 构造任务
        task = {
            "student_id": request.student_id,
            "question": request.question,
            "topic": request.topic,
            "timestamp": datetime.now().isoformat()
        }
        
        # 让 Agent 处理问题
        response = await agent.process_message(task)
        print(f"Agent response: {response}")
        
        # 保存 Agent 的回复
        if response:
            message = Message(
                student_id=request.student_id,
                content=response.get("content", str(response)),
                sender=request.agent_name,
                role="assistant",
                timestamp=datetime.now()
            )
            db.add(message)
            await db.commit()
            print(f"Saved agent message: {response.get('content', str(response))}")
        
        return {"status": "success", "message": response.get("content", str(response)), "agent_id": request.agent_name}
        
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
async def get_agents_status():
    """获取所有 Agent 的状态."""
    try:
        coordinator = agents.get("coordinator")
        if not coordinator:
            raise HTTPException(status_code=404, detail="Coordinator agent not found")

        response = await coordinator.process_message({"type": "status"})
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get agent status")

        return response

    except Exception as e:
        print(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages")
async def get_messages():
    """获取所有消息."""
    db = SessionLocal()
    try:
        messages = db.query(Message).order_by(Message.timestamp.asc()).all()
        return {"messages": messages}
    finally:
        db.close()

@app.get("/api/agents")
async def list_agents():
    """列出所有可用的 Agents."""
    return {
        "agents": [
            {"id": "teacher_agent", "name": "教师助手"},
            {"id": "knowledge_crawler", "name": "知识爬虫"},
            {"id": "faq_generator", "name": "FAQ 生成器"},
            {"id": "quiz_generator", "name": "测验生成器"}
        ]
    }

@app.get("/api/history/{student_id}")
async def get_history(student_id: str):
    """获取学生的对话历史."""
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(
            Message.student_id == student_id
        ).order_by(Message.timestamp.asc()).all()
        return {"messages": messages}
    finally:
        db.close()

@app.post("/api/student/interact")
async def student_interact(request: StudentInteractRequest):
    """学生互动接口."""
    db = SessionLocal()
    try:
        # 获取或创建学生 Agent
        student_agent = get_or_create_student_agent(request.sender_id)

        # 处理互动
        response = student_agent.handle_interaction(request.action, request.content)

        # 记录互动
        message = Message(
            student_id=request.sender_id,
            content=f"{request.action}: {request.content}",
            message_type="student",
            timestamp=datetime.now()
        )
        db.add(message)

        # 记录回复
        reply = Message(
            student_id=request.sender_id,
            content=response,
            message_type="assistant",
            timestamp=datetime.now()
        )
        db.add(reply)
        await db.commit()

        return {
            "status": "success",
            "response": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/tools/search")
async def use_search_tool(request: ToolRequest):
    """使用 DuckDuckGo 搜索工具."""
    try:
        tool = DuckDuckGoSearchTool()
        result = tool.search(request.params.get("query", ""))
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tools/scrape")
async def use_scrape_tool(request: ToolRequest):
    """使用网页抓取工具."""
    try:
        tool = WebScraperTool()
        result = tool.scrape(request.params.get("url", ""))
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/action")
async def admin_action(request: AdminRequest):
    """管理员操作接口."""
    try:
        # 获取 Admin Agent
        admin_agent = agents.get("admin_agent")
        if not admin_agent:
            raise HTTPException(status_code=404, detail="Admin agent not found")

        # 执行操作
        result = admin_agent.execute_action(request.action, request.params)
        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件并使用 Chunkr 处理."""
    try:
        # 保存文件
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 使用 Chunkr 处理
        # TODO: 添加实际的 Chunkr 处理逻辑

        return {
            "status": "success",
            "message": "File uploaded and processed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/firecrawl/scrape")
async def scrape_structured(request: FirecrawlScrapeRequest):
    """使用 Firecrawl 进行结构化抓取."""
    try:
        # TODO: 添加实际的 Firecrawl 抓取逻辑
        return {
            "status": "success",
            "data": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/firecrawl/map")
async def map_site(request: FirecrawlMapRequest):
    """使用 Firecrawl 抓取网站地图."""
    try:
        # TODO: 添加实际的网站地图抓取逻辑
        return {
            "status": "success",
            "sitemap": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/multimodal/ask")
async def handle_multimodal_question(request: MultimodalRequest):
    """处理包含图片的多模态问题."""
    try:
        # 如果有图片，先处理图片
        image_data = None
        if request.image:
            # 解码 Base64 图片
            image_bytes = base64.b64decode(request.image)
            image = Image.open(BytesIO(image_bytes))
            # TODO: 处理图片

        # 获取教师 Agent
        teacher_agent = agents.get("teacher_agent")
        if not teacher_agent:
            raise HTTPException(status_code=404, detail="Teacher agent not found")

        # 处理问题
        response = teacher_agent.handle_multimodal_question(
            question=request.question,
            image=image_data
        )

        return {
            "status": "success",
            "answer": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test")
async def test_model():
    """测试接口."""
    try:
        return {
            "status": "success",
            "message": "API is working"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/records")
async def get_records():
    """获取所有学习记录."""
    db = SessionLocal()
    try:
        records = db.query(StudyRecord).order_by(StudyRecord.timestamp.desc()).all()
        return {
            "status": "success",
            "records": records
        }
    finally:
        db.close()

@app.post("/api/tts")
async def text_to_speech(request: TextToSpeechRequest):
    """文本转语音接口."""
    try:
        # TODO: 添加实际的文本转语音逻辑
        audio_data = None  # 这里应该是实际的音频数据

        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        return {
            "status": "success",
            "audio": base64.b64encode(audio_data).decode()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接处理."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # TODO: 处理 WebSocket 消息
                await websocket.send_text(json.dumps({
                    "status": "success",
                    "message": "Message received"
                }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON"
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 静态文件目录
frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
if not os.path.exists(frontend_build_path):
    frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

# 添加静态文件服务
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 挂载静态文件
app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")

# 处理前端路由
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """服务前端静态文件."""
    if not full_path:
        full_path = "index.html"
    return FileResponse(f"../frontend/build/{full_path}")

# 启动命令: uvicorn main:app --reload --port 8000

# ===================== 启动初始化 =====================
@app.on_event("startup")
async def startup_event():
    """启动时初始化 Agents."""
    # 初始化 Agents
    agents["admin_agent"] = AdminAgent()

    # 启动 Agent 线程
    for agent_name, agent in agents.items():
        thread = threading.Thread(target=agent_task, args=(agent, message_queue))
        thread.daemon = True
        thread.start()

    # 初始化数据库
    await init_db()

def agent_task(agent, message_queue):
    """Agent 后台任务."""
    while True:
        try:
            message = message_queue.get()
            if message:
                response = agent.step(message)
                if response:
                    asyncio.run(manager.broadcast(json.dumps({
                        "type": "agent_response",
                        "agent": agent.__class__.__name__,
                        "content": response
                    })))
        except Exception as e:
            print(f"Error in agent_task: {str(e)}")
        finally:
            message_queue.task_done()
            time.sleep(0.1)  # 避免过度消耗 CPU

def get_or_create_student_agent(student_id: str) -> StudentAgent:
    """获取或创建学生 Agent"""
    if student_id not in agents:
        print(f"Creating new StudentAgent for student_id: {student_id}")
        student_agent = StudentAgent(student_id)
        agents[student_id] = student_agent
        print(f"StudentAgent created successfully for student_id: {student_id}")
    return agents[student_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")

    print("=== 智能教育系统后端服务器 ===")
    print("* 数据库初始化完成")
    print("* CORS 中间件配置完成")
    print("* WebSocket 管理器初始化完成")
    print("* 所有代理初始化完成")
    print(f"服务器运行在: http://localhost:8002")
    print(f"API 文档地址: http://localhost:8002/docs")
    print("==============================")