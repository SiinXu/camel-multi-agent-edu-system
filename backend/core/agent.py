from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .blackboard import Blackboard
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentState:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    THINKING = "thinking"
    WRITING = "writing"
    READING = "reading"

class Agent(ABC):
    def __init__(self, agent_id: str, blackboard: Blackboard):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.state = AgentState.IDLE
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self.knowledge_base: Dict[str, Any] = {}
        self.last_action_time = datetime.now()

    @abstractmethod
    async def run(self) -> None:
        """Main execution loop of the agent"""
        pass

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming messages"""
        pass

    async def start(self) -> None:
        """Start the agent"""
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())
            self.state = AgentState.RUNNING
            logger.info(f"Agent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent"""
        if self._task and not self._task.done():
            self._stop_event.set()
            await self._task
            self.state = AgentState.IDLE
            logger.info(f"Agent {self.agent_id} stopped")

    async def pause(self) -> None:
        """Pause the agent"""
        self.state = AgentState.PAUSED
        logger.info(f"Agent {self.agent_id} paused")

    async def resume(self) -> None:
        """Resume the agent"""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.RUNNING
            logger.info(f"Agent {self.agent_id} resumed")

    async def _run_loop(self) -> None:
        """Internal run loop"""
        try:
            while not self._stop_event.is_set():
                if self.state == AgentState.RUNNING:
                    await self.run()
                    self.last_action_time = datetime.now()
                elif self.state == AgentState.PAUSED:
                    await asyncio.sleep(1)
                await asyncio.sleep(0.1)  # Prevent CPU overload
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"Error in agent {self.agent_id}: {str(e)}")
            raise

    async def read_from_blackboard(self, key: str) -> Any:
        """Read data from the blackboard"""
        self.state = AgentState.READING
        try:
            entry = await self.blackboard.read(key)
            return entry.value if entry else None
        finally:
            self.state = AgentState.RUNNING

    async def write_to_blackboard(self, key: str, value: Any, metadata: Dict = None) -> None:
        """Write data to the blackboard"""
        self.state = AgentState.WRITING
        try:
            await self.blackboard.write(key, value, self.agent_id, metadata)
        finally:
            self.state = AgentState.RUNNING

    async def subscribe_to_key(self, key: str, callback: callable) -> None:
        """Subscribe to changes on a specific key in the blackboard"""
        await self.blackboard.subscribe(key, callback)

    def get_state(self) -> str:
        """Get the current state of the agent"""
        return self.state

    def get_status(self) -> Dict[str, Any]:
        """Get the full status of the agent"""
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "last_action_time": self.last_action_time.isoformat(),
            "knowledge_base_size": len(self.knowledge_base)
        }

    async def update_knowledge_base(self, key: str, value: Any) -> None:
        """Update the agent's knowledge base"""
        self.knowledge_base[key] = value

    async def get_knowledge(self, key: str) -> Optional[Any]:
        """Get knowledge from the agent's knowledge base"""
        return self.knowledge_base.get(key)

    async def clear_knowledge_base(self) -> None:
        """Clear the agent's knowledge base"""
        self.knowledge_base.clear()
