from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from pydantic import BaseModel
import json

class BlackboardEntry(BaseModel):
    key: str
    value: Any
    timestamp: datetime
    agent_id: str
    metadata: Dict = {}

class Blackboard:
    def __init__(self):
        self._data: Dict[str, BlackboardEntry] = {}
        self._subscribers: Dict[str, List[callable]] = {}
        self._lock = asyncio.Lock()

    async def write(self, key: str, value: Any, agent_id: str, metadata: Dict = None) -> None:
        """Write data to the blackboard"""
        async with self._lock:
            entry = BlackboardEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                agent_id=agent_id,
                metadata=metadata or {}
            )
            self._data[key] = entry
            
            # Notify subscribers
            if key in self._subscribers:
                for callback in self._subscribers[key]:
                    await callback(entry)

    async def read(self, key: str) -> Optional[BlackboardEntry]:
        """Read data from the blackboard"""
        async with self._lock:
            return self._data.get(key)

    async def subscribe(self, key: str, callback: callable) -> None:
        """Subscribe to changes on a specific key"""
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)

    async def unsubscribe(self, key: str, callback: callable) -> None:
        """Unsubscribe from changes on a specific key"""
        if key in self._subscribers and callback in self._subscribers[key]:
            self._subscribers[key].remove(callback)

    async def get_all_entries(self) -> Dict[str, BlackboardEntry]:
        """Get all entries from the blackboard"""
        async with self._lock:
            return self._data.copy()

    async def clear(self) -> None:
        """Clear all data from the blackboard"""
        async with self._lock:
            self._data.clear()

    def to_json(self) -> str:
        """Convert blackboard data to JSON string"""
        data_dict = {
            key: {
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
                "agent_id": entry.agent_id,
                "metadata": entry.metadata
            }
            for key, entry in self._data.items()
        }
        return json.dumps(data_dict)
