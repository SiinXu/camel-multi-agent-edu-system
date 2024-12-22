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

class FAQGeneratorAgent(Agent):
    """FAQ 生成器 Agent，负责生成常见问题解答."""

    def __init__(self, agent_id: str = "faq_generator_1", blackboard: Optional[Blackboard] = None):
        """初始化 FAQ 生成器 Agent."""
        super().__init__(agent_id, blackboard or Blackboard())
        self.faqs: Dict[str, List[Dict[str, Any]]] = {}

    async def run(self) -> None:
        """主执行循环."""
        while not self._stop_event.is_set():
            try:
                # 检查黑板上是否有新任务
                task = await self.blackboard.get_task()
                if task:
                    await self.process_message(task)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in FAQ generator run loop: {str(e)}")
                self.state = AgentState.ERROR
                await asyncio.sleep(5)

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息."""
        try:
            message_type = message.get("type")
            if message_type == "generate_faq":
                return await self.generate_faq(message)
            elif message_type == "get_faq":
                return await self.get_faq(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return None

    async def generate_faq(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成 FAQ."""
        try:
            topic = message.get("topic", "")
            content = message.get("content", "")

            # 生成 FAQ
            faq = {
                "question": content,
                "answer": f"这是关于 {topic} 的常见问题解答。",
                "topic": topic,
                "timestamp": datetime.now()
            }

            # 保存到知识库
            if topic not in self.faqs:
                self.faqs[topic] = []
            self.faqs[topic].append(faq)

            # 更新知识库
            await self.update_knowledge_base(f"faq_{topic}", self.faqs[topic])

            return {
                "type": "faq",
                "content": faq,
                "agent_id": self.agent_id
            }
        except Exception as e:
            logger.error(f"Error generating FAQ: {str(e)}")
            return None

    async def get_faq(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取指定主题的 FAQ."""
        try:
            topic = message.get("topic", "")
            faqs = self.faqs.get(topic, [])
            return {
                "type": "faq_list",
                "content": faqs,
                "agent_id": self.agent_id
            }
        except Exception as e:
            logger.error(f"Error getting FAQ: {str(e)}")
            return None