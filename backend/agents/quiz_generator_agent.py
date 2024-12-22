# quiz_generator_agent.py

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

class QuizGeneratorAgent(Agent):
    """测验生成器 Agent."""

    def __init__(self, blackboard: Blackboard, agent_id: str = "quiz_1"):
        """初始化测验生成器 Agent."""
        super().__init__(agent_id, blackboard)
        self.conversation_history = []

    async def run(self) -> None:
        """Agent 的主循环."""
        self.state = AgentState.RUNNING
        try:
            while self.state == AgentState.RUNNING:
                # 从黑板获取任务
                task = await self.blackboard.get_task()
                if task:
                    await self.process_message(task)
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in run loop: {str(e)}")
            self.state = AgentState.ERROR
            await asyncio.sleep(5)

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理一条消息并返回回复."""
        try:
            # 从消息中获取内容
            content = message.get("content", "")
            topic = message.get("topic", "")
            
            # 记录消息
            self.conversation_history.append({
                "role": "user",
                "content": content,
                "timestamp": datetime.now()
            })
            
            # 生成回复
            response = self.generate_response(content)
            
            # 记录回复
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
            
            return {
                "type": "response",
                "content": response,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            logger.error(error_message)
            return {
                "type": "error",
                "content": error_message,
                "agent_id": self.agent_id
            }

    def generate_response(self, question: str) -> str:
        """生成回复."""
        # 这里可以添加实际的回复生成逻辑
        return f'我是测验生成器，你问了："{question}"。我会帮你生成相关的测验题目。'

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史."""
        return self.conversation_history
