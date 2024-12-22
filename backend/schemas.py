from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class AskRequest(BaseModel):
    """问题请求模型."""
    student_id: str
    question: str
    agent_name: str
    topic: Optional[str] = None

class ToolRequest(BaseModel):
    """工具请求模型."""
    tool_name: str
    params: Dict[str, Any]

class TextToSpeechRequest(BaseModel):
    """文字转语音请求模型."""
    text: str
    voice_id: Optional[str] = None

class SpeechToTextRequest(BaseModel):
    audio_file: str

class AdminRequest(BaseModel):
    """管理员操作请求模型."""
    action: str
    params: Dict[str, Any]

class StudentInteractRequest(BaseModel):
    """学生互动请求模型."""
    sender_id: str
    action: str
    content: str

class FirecrawlScrapeRequest(BaseModel):
    url: str
    params: Dict[str, Any]

class FirecrawlMapRequest(BaseModel):
    url: str

class MultimodalRequest(BaseModel):
    question: str
    image: Optional[str] = None

class MessageSchema(BaseModel):
    content: str = Field(default="")
    role: str = Field(default="user")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class StudySession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    topic: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = Field(default="active")

class ChatMessage(BaseModel):
    content: str
    role: str = Field(default="user")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class StudentInteractRequest(BaseModel):
    """学生互动请求模型."""
    sender_id: str
    action: str
    content: str

class FirecrawlScrapeRequest(BaseModel):
    """网页抓取请求模型."""
    url: str
    params: Optional[Dict[str, Any]] = None

class FirecrawlMapRequest(BaseModel):
    """知识地图请求模型."""
    topic: str
    params: Optional[Dict[str, Any]] = None

class MultimodalRequest(BaseModel):
    """多模态请求模型."""
    content: str
    mode: str
    params: Optional[Dict[str, Any]] = None

class MessageSchema(BaseModel):
    """消息模型."""
    id: str
    content: str
    sender: str
    timestamp: datetime

class StudySession(BaseModel):
    """学习会话模型."""
    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    topic: Optional[str] = None

class ChatMessage(BaseModel):
    """聊天消息模型."""
    message_id: str
    session_id: str
    content: str
    sender: str
    timestamp: datetime
    role: str
    metadata: Optional[Dict[str, Any]] = None
