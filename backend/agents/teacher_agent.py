from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import sys
import os
import asyncio

# 添加父目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Agent, AgentState
from core.blackboard import Blackboard

logger = logging.getLogger(__name__)

class TeacherAgent(Agent):
    """教师 Agent."""

    def __init__(self, agent_id: str = "teacher_1", blackboard: Optional[Blackboard] = None):
        """初始化教师 Agent."""
        super().__init__(agent_id, blackboard or Blackboard())
        self.conversation_history = []

    async def run(self) -> None:
        """主执行循环."""
        while not self._stop_event.is_set():
            try:
                # 检查黑板上是否有新消息
                message = await self.blackboard.get_task()
                if message:
                    await self.process_message(message)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in teacher run loop: {str(e)}")
                self.state = AgentState.ERROR
                await asyncio.sleep(5)

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理一条消息并返回回复."""
        try:
            # 从消息中获取内容
            content = message.get("content", "")
            student_id = message.get("student_id", "")
            topic = message.get("topic", "")

            # 记录消息
            self.conversation_history.append({
                "timestamp": datetime.now(),
                "student_id": student_id,
                "content": content,
                "topic": topic
            })

            # 生成回复
            response = f"我是教师 {self.agent_id}，我收到了你的问题：{content}。"
            if topic:
                response += f"\n主题是：{topic}。"

            # 更新知识库
            await self.update_knowledge_base(f"last_question_{student_id}", {
                "content": content,
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "type": "response",
                "content": response,
                "agent_id": self.agent_id
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return None

    async def get_conversation_history(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取对话历史."""
        if student_id:
            return [msg for msg in self.conversation_history if msg["student_id"] == student_id]
        return self.conversation_history