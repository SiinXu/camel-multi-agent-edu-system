import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException, Depends, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Import enhanced agents
from agents.enhanced_teacher_agent import EnhancedTeacherAgent
from agents.enhanced_student_agent import EnhancedStudentAgent
from agents.coordinator_agent import CoordinatorAgent, TaskPriority
from core.blackboard import Blackboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./enhanced_study_system.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create FastAPI app
app = FastAPI(title="Enhanced Multi-Agent Education System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests
class StudentRequest(BaseModel):
    student_id: str
    name: str

class TeacherRequest(BaseModel):
    teacher_id: str

class MessageRequest(BaseModel):
    sender_id: str
    content: str
    topic: Optional[str] = None

# Global state
blackboard = Blackboard()
coordinator: Optional[CoordinatorAgent] = None
teachers: Dict[str, EnhancedTeacherAgent] = {}
students: Dict[str, EnhancedStudentAgent] = {}
active_connections: Dict[str, WebSocket] = {}

async def initialize_system():
    """Initialize the multi-agent system"""
    global coordinator, teachers, students
    
    try:
        # Create coordinator agent
        coordinator = CoordinatorAgent("coordinator_1", blackboard)
        await coordinator.start()
        logger.info("Coordinator agent started successfully")
        
        # Create initial teacher agent
        teacher = EnhancedTeacherAgent("teacher_1", blackboard)
        teachers["teacher_1"] = teacher
        await teacher.start()
        logger.info("Teacher agent started successfully")
        
        # Register teacher with coordinator
        await coordinator.process_message({
            "type": "register_agent",
            "agent_id": "teacher_1",
            "capabilities": ["teach", "evaluate", "plan"]
        })
        
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    await initialize_system()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    for teacher in teachers.values():
        await teacher.stop()
    for student in students.values():
        await student.stop()
    if coordinator:
        await coordinator.stop()

@app.post("/student/register")
async def register_student(request: StudentRequest):
    """Register a new student"""
    try:
        # Create new student agent
        student = EnhancedStudentAgent(request.student_id, blackboard, request.name)
        students[request.student_id] = student
        await student.start()
        
        # Register student with coordinator
        if coordinator:
            await coordinator.process_message({
                "type": "register_agent",
                "agent_id": request.student_id,
                "capabilities": ["learn", "ask_questions", "submit_answers"]
            })
        
        return {"status": "success", "message": f"Student {request.name} registered successfully"}
    except Exception as e:
        logger.error(f"Error registering student: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/send")
async def send_message(request: MessageRequest):
    """Send a message to the system"""
    try:
        # Create task for the message
        if coordinator:
            task_response = await coordinator.process_message({
                "type": "new_task",
                "task_id": f"msg_{datetime.now().timestamp()}",
                "task_type": "process_message",
                "priority": TaskPriority.MEDIUM.value,
                "data": {
                    "sender_id": request.sender_id,
                    "content": request.content,
                    "topic": request.topic,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            return {"status": "success", "task_id": task_response.get("task_id")}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    try:
        await websocket.accept()
        active_connections[client_id] = websocket
        
        # Subscribe to blackboard updates for this client
        async def handle_update(entry):
            if entry.metadata.get("target_id") == client_id:
                await websocket.send_json({
                    "type": "update",
                    "data": {
                        "key": entry.key,
                        "value": entry.value,
                        "timestamp": entry.timestamp.isoformat()
                    }
                })
        
        await blackboard.subscribe(f"response_{client_id}", handle_update)
        
        try:
            while True:
                data = await websocket.receive_json()
                await send_message(MessageRequest(**data))
        except WebSocketDisconnect:
            active_connections.pop(client_id, None)
            # Cleanup
            # Note: We should also unsubscribe from blackboard updates here
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if client_id in active_connections:
            active_connections.pop(client_id)

@app.get("/system/status")
async def get_system_status():
    """Get current system status"""
    try:
        return {
            "coordinator_status": coordinator.get_status() if coordinator else None,
            "active_teachers": len(teachers),
            "active_students": len(students),
            "active_connections": len(active_connections)
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("enhanced_main:app", host="0.0.0.0", port=8000, reload=True)
