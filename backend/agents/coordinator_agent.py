from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging
from enum import Enum

from ..core.agent import Agent, AgentState
from ..core.blackboard import Blackboard

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    def __init__(
        self,
        task_id: str,
        task_type: str,
        priority: TaskPriority,
        data: Dict[str, Any],
        assigned_to: Optional[str] = None
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.data = data
        self.assigned_to = assigned_to
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "data": self.data,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        task = cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            priority=TaskPriority(data["priority"]),
            data=data["data"],
            assigned_to=data.get("assigned_to")
        )
        task.status = TaskStatus(data["status"])
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        return task

class CoordinatorAgent(Agent):
    def __init__(self, agent_id: str, blackboard: Blackboard):
        super().__init__(agent_id, blackboard)
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.task_queue: List[Task] = []
        self.agent_capabilities: Dict[str, List[str]] = {}

    async def run(self) -> None:
        """Main execution loop"""
        try:
            # Update agent statuses
            await self._update_agent_statuses()
            
            # Process new tasks
            await self._process_new_tasks()
            
            # Assign pending tasks
            await self._assign_tasks()
            
            # Monitor task progress
            await self._monitor_tasks()
            
            # Clean up completed tasks
            await self._cleanup_tasks()
            
        except Exception as e:
            logger.error(f"Error in coordinator agent run loop: {str(e)}")
            self.state = AgentState.ERROR

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming message"""
        try:
            message_type = message.get("type")
            if message_type == "register_agent":
                return await self._register_agent(message)
            elif message_type == "task_update":
                return await self._handle_task_update(message)
            elif message_type == "new_task":
                return await self._create_task(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"error": str(e)}

    async def _register_agent(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent with the coordinator"""
        try:
            agent_id = message["agent_id"]
            capabilities = message["capabilities"]
            
            self.active_agents[agent_id] = {
                "status": AgentState.IDLE.value,
                "last_seen": datetime.now(),
                "current_task": None
            }
            
            self.agent_capabilities[agent_id] = capabilities
            
            logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
            
            return {"status": "success", "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Error registering agent: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _create_task(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        try:
            task = Task(
                task_id=message["task_id"],
                task_type=message["task_type"],
                priority=TaskPriority(message["priority"]),
                data=message["data"]
            )
            
            self.task_queue.append(task)
            
            # Write task to blackboard
            await self.write_to_blackboard(
                f"task_{task.task_id}",
                task.to_dict()
            )
            
            logger.info(f"Created new task: {task.task_id}")
            
            return {"status": "success", "task_id": task.task_id}
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _handle_task_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task status update"""
        try:
            task_id = message["task_id"]
            new_status = TaskStatus(message["status"])
            
            # Update task status
            task = await self._get_task(task_id)
            if task:
                task.status = new_status
                task.updated_at = datetime.now()
                if new_status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.now()
                
                # Update task on blackboard
                await self.write_to_blackboard(
                    f"task_{task_id}",
                    task.to_dict()
                )
                
                logger.info(f"Updated task {task_id} status to {new_status.value}")
                
                return {"status": "success", "task_id": task_id}
            else:
                return {"status": "error", "message": f"Task {task_id} not found"}
        except Exception as e:
            logger.error(f"Error handling task update: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _update_agent_statuses(self):
        """Update status of all registered agents"""
        try:
            current_time = datetime.now()
            for agent_id, agent_info in self.active_agents.items():
                # Check agent heartbeat
                heartbeat = await self.read_from_blackboard(f"agent_heartbeat_{agent_id}")
                if heartbeat:
                    last_heartbeat = datetime.fromisoformat(heartbeat["timestamp"])
                    if (current_time - last_heartbeat).seconds > 30:  # 30 seconds timeout
                        agent_info["status"] = AgentState.ERROR.value
                    else:
                        agent_info["status"] = heartbeat["status"]
                        agent_info["last_seen"] = last_heartbeat
        except Exception as e:
            logger.error(f"Error updating agent statuses: {str(e)}")

    async def _process_new_tasks(self):
        """Process and prioritize new tasks"""
        try:
            # Sort tasks by priority
            self.task_queue.sort(key=lambda x: TaskPriority[x.priority.value].value, reverse=True)
        except Exception as e:
            logger.error(f"Error processing new tasks: {str(e)}")

    async def _assign_tasks(self):
        """Assign pending tasks to available agents"""
        try:
            for task in self.task_queue:
                if task.status == TaskStatus.PENDING:
                    # Find suitable agent
                    agent_id = await self._find_suitable_agent(task)
                    if agent_id:
                        # Assign task
                        task.assigned_to = agent_id
                        task.status = TaskStatus.ASSIGNED
                        task.updated_at = datetime.now()
                        
                        # Update task on blackboard
                        await self.write_to_blackboard(
                            f"task_{task.task_id}",
                            task.to_dict()
                        )
                        
                        # Notify agent
                        await self.write_to_blackboard(
                            f"agent_task_{agent_id}",
                            task.to_dict()
                        )
                        
                        logger.info(f"Assigned task {task.task_id} to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error assigning tasks: {str(e)}")

    async def _monitor_tasks(self):
        """Monitor progress of assigned tasks"""
        try:
            for task in self.task_queue:
                if task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    # Check task progress
                    progress = await self.read_from_blackboard(f"task_progress_{task.task_id}")
                    if progress:
                        # Update task status if needed
                        if progress["status"] != task.status.value:
                            task.status = TaskStatus(progress["status"])
                            task.updated_at = datetime.now()
                            
                            # Update task on blackboard
                            await self.write_to_blackboard(
                                f"task_{task.task_id}",
                                task.to_dict()
                            )
        except Exception as e:
            logger.error(f"Error monitoring tasks: {str(e)}")

    async def _cleanup_tasks(self):
        """Clean up completed or failed tasks"""
        try:
            # Remove completed tasks from queue after certain time
            current_time = datetime.now()
            self.task_queue = [
                task for task in self.task_queue
                if not (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                       (current_time - task.updated_at).seconds > 3600)  # 1 hour retention
            ]
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {str(e)}")

    async def _find_suitable_agent(self, task: Task) -> Optional[str]:
        """Find a suitable agent for the given task"""
        try:
            for agent_id, capabilities in self.agent_capabilities.items():
                if (task.task_type in capabilities and
                    self.active_agents[agent_id]["status"] == AgentState.IDLE.value):
                    return agent_id
            return None
        except Exception as e:
            logger.error(f"Error finding suitable agent: {str(e)}")
            return None

    async def _get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        try:
            task_data = await self.read_from_blackboard(f"task_{task_id}")
            if task_data:
                return Task.from_dict(task_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            return None
