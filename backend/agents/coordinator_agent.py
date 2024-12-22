from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
import sys
import os

# 添加父目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Agent, AgentState
from core.blackboard import Blackboard

logger = logging.getLogger(__name__)

class CoordinatorAgent(Agent):
    """协调者 Agent，负责管理和协调其他 Agent 的工作."""

    def __init__(self, agent_id: str, blackboard: Blackboard):
        """初始化协调者 Agent."""
        super().__init__(agent_id, blackboard)
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Dict[str, Any]] = []
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        """主执行循环."""
        while not self._stop_event.is_set():
            try:
                # 检查黑板上是否有新任务
                task = await self.blackboard.get_task()
                if task:
                    await self.route_task(task)
                
                # 检查各个 Agent 的状态
                await self.check_agents()
                
                # 监控所有 Agent 的状态
                await self.monitor_agents()
                
                # 等待一段时间再继续下一次循环
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in coordinator run loop: {str(e)}")
                self.state = AgentState.ERROR
                await asyncio.sleep(5)  # 出错后等待一段时间再继续

    async def analyze_task(self, task: Dict[str, Any]) -> str:
        """分析任务，决定使用哪个 Agent."""
        logger.info(f"Analyzing task: {task}")
        
        # 获取任务内容
        content = task.get("question", "").lower()
        topic = task.get("topic", "").lower()
        
        # 根据内容和主题选择合适的 Agent
        if "faq" in content or "常见问题" in content or topic == "system_faq":
            return "faq_generator"  # FAQ 生成器
        elif "搜索" in content or "查找" in content or topic == "search":
            return "knowledge_crawler"  # 知识爬虫
        elif "测试" in content or "quiz" in content or "考试" in content or topic == "quiz":
            return "quiz_generator"  # 测试生成器
        else:
            return "teacher_agent"  # 教师 Agent

    async def route_task(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """根据任务类型路由到相应的 Agent."""
        try:
            # 分析任务，选择合适的 Agent
            agent_id = await self.analyze_task(task)
            logger.info(f"Selected agent: {agent_id}")
            logger.info(f"Available agents: {list(self.agents.keys())}")
            logger.info(f"Task content: {task.get('content')}")
            logger.info(f"Task type: {task.get('type')}")
            
            agent = self.agents.get(agent_id)
            if not agent:
                logger.warning(f"Agent {agent_id} not found")
                return {
                    "type": "error",
                    "content": f"Agent {agent_id} not found",
                    "agent_id": self.agent_id
                }
            
            # 处理任务
            response = await agent.process_message(task)
            logger.info(f"Agent {agent_id} response: {response}")
            
            if response:
                # 记录任务处理结果
                await self.blackboard.write(
                    key=f"task_result_{task.get('student_id')}_{datetime.now().isoformat()}",
                    value=response,
                    agent_id=self.agent_id,
                    metadata={"task_type": task.get("type"), "agent_id": agent_id}
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error routing task: {str(e)}")
            return {
                "type": "error",
                "content": f"Error routing task: {str(e)}",
                "agent_id": self.agent_id
            }

    async def monitor_agents(self) -> None:
        """监控所有 Agent 的状态."""
        try:
            status = {}
            for agent_id, agent in self.agents.items():
                status[agent_id] = {
                    "state": agent.state,
                    "last_active": agent.last_action_time.isoformat() if hasattr(agent, 'last_action_time') else None,
                    "error": agent.last_error if hasattr(agent, 'last_error') else None
                }
            
            # 将状态信息写入黑板
            await self.blackboard.write(
                key="agent_status",
                value=status,
                agent_id=self.agent_id,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Error monitoring agents: {str(e)}")

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息."""
        try:
            message_type = message.get("type")
            if message_type == "task":
                return await self.route_task(message)
            elif message_type == "status":
                await self.monitor_agents()
                return {"type": "status", "content": "Status updated"}
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return None

    async def handle_question(self, task: Dict[str, Any]) -> None:
        """处理问题任务."""
        question = task.get("content")
        student_id = task.get("student_id")
        
        # 根据问题内容选择合适的 Agent
        agent = self.select_agent(question)
        if agent:
            response = await agent.process_message({
                "type": "question",
                "content": question,
                "student_id": student_id
            })
            
            if response:
                await self.blackboard.post_message({
                    "type": "response",
                    "content": response.get("content"),
                    "student_id": student_id,
                    "agent_id": agent.agent_id,
                    "timestamp": datetime.now()
                })

    async def handle_search(self, task: Dict[str, Any]) -> None:
        """处理搜索任务."""
        query = task.get("content")
        student_id = task.get("student_id")
        
        # 使用知识爬虫 Agent 进行搜索
        crawler = self.agents.get("knowledge_crawler")
        if crawler:
            response = await crawler.process_message({
                "type": "search",
                "content": query,
                "student_id": student_id
            })
            
            if response:
                await self.blackboard.post_message({
                    "type": "search_result",
                    "content": response.get("content"),
                    "student_id": student_id,
                    "agent_id": crawler.agent_id,
                    "timestamp": datetime.now()
                })

    def select_agent(self, question: str) -> Optional[Agent]:
        """根据问题选择合适的 Agent."""
        # 这里可以添加更复杂的选择逻辑
        return self.agents.get("teacher_agent")

    async def check_agents(self) -> None:
        """检查所有 Agent 的状态."""
        for agent_id, agent in self.agents.items():
            if agent.state == AgentState.ERROR:
                logger.warning(f"Agent {agent_id} is in error state")
                # 尝试重启出错的 Agent
                await self.restart_agent(agent_id)

    async def restart_agent(self, agent_id: str) -> None:
        """重启指定的 Agent."""
        try:
            agent = self.agents.get(agent_id)
            if agent:
                await agent.stop()
                await agent.start()
                logger.info(f"Agent {agent_id} restarted successfully")
        except Exception as e:
            logger.error(f"Error restarting agent {agent_id}: {str(e)}")

    async def register_agent(self, agent: Agent) -> None:
        """注册一个 Agent."""
        try:
            self.agents[agent.agent_id] = agent
            logger.info(f"Agent {agent.agent_id} registered with coordinator")
            logger.info(f"Current agents: {list(self.agents.keys())}")
        except Exception as e:
            logger.error(f"Error registering agent {agent.agent_id}: {str(e)}")
            raise

    async def unregister_agent(self, agent_id: str) -> None:
        """注销一个 Agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")

    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """向所有 Agent 广播消息."""
        for agent in self.agents.values():
            try:
                await agent.process_message(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to agent {agent.agent_id}: {str(e)}")

    async def get_agent_status(self) -> Dict[str, Any]:
        """获取所有 Agent 的状态信息."""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "state": agent.state.value,
                "last_active": agent.last_active.isoformat() if agent.last_active else None,
                "error": agent.last_error
            }
        return status

    async def stop(self) -> None:
        """停止协调者 Agent."""
        self._stop_event.set()
        # 停止所有 Agent
        for agent in self.agents.values():
            await agent.stop()
        logger.info("Coordinator agent stopped")
