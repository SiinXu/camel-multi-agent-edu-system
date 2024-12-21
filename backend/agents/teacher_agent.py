import os
from getpass import getpass
import json
import requests
from bs4 import BeautifulSoup
from enum import Enum

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.configs import QwenConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.utils.commons import build_tool_reponse

# 导入工具类
from tools.duckduckgo_search import DuckDuckGoSearchTool
from tools.web_scraper import WebScraperTool

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    USING_TOOL = "using_tool"
    CRAWLING = "crawling"
    GENERATING_FAQ = "generating_faq"
    GENERATING_QUIZ = "generating_quiz"
    ERROR = "error"

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"

class KnowledgeLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TeacherAgent(ChatAgent):
    def __init__(self, model_type=None):
        system_message = BaseMessage(
            role_name="Teacher",
            role_type="ASSISTANT",
            meta_dict=None,
            content="You are a helpful teacher. "
                    "You can use tools to help answer questions. "
                    "Available tools: DuckDuckGoSearchTool, WebScraperTool. "
                    "You can use the Knowledge Crawler Agent, FAQ Generator Agent and Quiz Generator Agent to assist you for different topics. "
                    "You can also call the Admin Agent to manage the topics."
        )
        super().__init__(system_message, model_type)

        # 初始化状态
        self._status = AgentStatus.IDLE
        self._status_message = ""

        # 获取 API 密钥
        self.modelscope_api_key = os.environ.get("MODELSCOPE_API_KEY")

        # Qwen API 集成 (使用 ModelScope 兼容的 API)
        self.model_config = QwenConfig(
            model="Qwen/Qwen2.5-32B-Instruct",  # 使用 Qwen2.5-32B-Instruct 模型
            temperature=0.2,
            # 可以添加其他参数, 例如 top_p, repetition_penalty 等
        )
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="Qwen/Qwen2.5-32B-Instruct",  # 使用 Qwen2.5-32B-Instruct 模型
            api_key=self.modelscope_api_key,  # 使用环境变量中的 API Key
            url="https://api-inference.modelscope.cn/v1/models/Qwen/Qwen2.5-32B-Instruct",
            model_config_dict=self.model_config.as_dict(),
        )

        # Initialize ModelScope models
        try:
            # Load learning style diagnosis model (using Qwen as base model)
            self.learning_style_model = ModelFactory.create(
                model_platform=ModelPlatformType.MODEL_SCOPE,
                model_type="qwen/Qwen-7B-Chat",  # Using Qwen-7B-Chat for text classification
                api_key=self.modelscope_api_key,
                model_config_dict={
                    "device": "cuda" if os.environ.get("USE_GPU", "0") == "1" else "cpu",
                    "max_length": 2048,
                    "temperature": 0.1,  # Lower temperature for more focused outputs
                    "top_p": 0.9
                }
            )
            print("Learning style model loaded successfully.")
        except Exception as e:
            print(f"Error loading learning style model: {e}")
            self.learning_style_model = None

        try:
            # Load knowledge assessment model (using Qwen as base model)
            self.knowledge_assessment_model = ModelFactory.create(
                model_platform=ModelPlatformType.MODEL_SCOPE,
                model_type="qwen/Qwen-7B-Chat",  # Using Qwen-7B-Chat for knowledge assessment
                api_key=self.modelscope_api_key,
                model_config_dict={
                    "device": "cuda" if os.environ.get("USE_GPU", "0") == "1" else "cpu",
                    "max_length": 2048,
                    "temperature": 0.2,
                    "top_p": 0.9
                }
            )
            print("Knowledge assessment model loaded successfully.")
        except Exception as e:
            print(f"Error loading knowledge assessment model: {e}")
            self.knowledge_assessment_model = None

        # 初始化工具
        self.tools = {
            "DuckDuckGoSearchTool": DuckDuckGoSearchTool(),
            "WebScraperTool": WebScraperTool(),
        }
        self.knowledge_crawler_agent = None
        self.faq_generator_agent = None
        self.quiz_generator_agent = None

        # 加载配置文件
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.available_topics = self.config["available_topics"]

    @property
    def status(self):
        return {
            "status": self._status.value,
            "message": self._status_message
        }

    def set_status(self, status: AgentStatus, message: str = ""):
        self._status = status
        self._status_message = message

    def add_tool(self, tool):
        self.tools[tool.__class__.__name__] = tool

    def set_knowledge_crawler_agent(self, agent):
        self.knowledge_crawler_agent = agent

    def set_faq_generator_agent(self, agent):
        self.faq_generator_agent = agent

    def set_quiz_generator_agent(self, agent):
        self.quiz_generator_agent = agent

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"Teacher received message: {message.content}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def run_with_qwen(self, prompt: str) -> str:
        """使用 Qwen API 生成回复."""
        response = self.model.run(prompt)
        return response

    def use_tool(self, tool_name: str, tool_params: str) -> str:
        """使用工具."""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            try:
                if tool_name == "DuckDuckGoSearchTool":
                    result = tool(tool_params)
                elif tool_name == "WebScraperTool":
                    result = tool(tool_params)
                else:
                    result = "Tool does not support specified parameters."

                ret = build_tool_reponse(result)
                return ret
            except Exception as e:
                return f"Error using tool {tool_name}: {e}"
        else:
            return f"Tool {tool_name} not found."

    def assess_learning_style(self, student_id: str, history: list) -> Optional[LearningStyle]:
        """Assess student's learning style based on interaction history."""
        if not self.learning_style_model:
            return None

        try:
            # Prepare input for the model
            # Combine recent interaction history into a single text
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in history[-5:]  # Use last 5 interactions
            ])

            # Create prompt for learning style assessment
            prompt = f"""Based on the following student interactions, determine their learning style.
Consider these aspects:
- How they ask questions
- What kind of explanations they prefer
- Their vocabulary and expression style

Student ID: {student_id}
Interaction History:
{history_text}

Analyze the student's learning style and classify it as one of:
- VISUAL (prefers diagrams, charts, videos)
- AUDITORY (prefers discussions, verbal explanations)
- KINESTHETIC (prefers hands-on activities, experiments)
- READING_WRITING (prefers text-based materials, taking notes)

Output the learning style as a single word (VISUAL/AUDITORY/KINESTHETIC/READING_WRITING).
"""
            # Get model response
            response = self.learning_style_model.run({
                "text": prompt,
                "max_length": 10,  # We only need a single word response
            })

            # Parse response
            style = response.strip().upper()
            if style in [ls.name for ls in LearningStyle]:
                return LearningStyle[style]
            return None

        except Exception as e:
            print(f"Error assessing learning style: {e}")
            return None

    def assess_knowledge_level(self, student_id: str, topic: str, answer: str) -> Optional[KnowledgeLevel]:
        """Assess student's knowledge level based on their answer to a topic."""
        if not self.knowledge_assessment_model:
            return None

        try:
            # Create prompt for knowledge assessment
            prompt = f"""Evaluate the student's understanding of the topic based on their answer.
Consider these aspects:
- Accuracy of concepts
- Depth of understanding
- Use of terminology
- Ability to explain

Topic: {topic}
Student's Answer: {answer}

Rate the knowledge level as one of:
- LOW (basic or incorrect understanding)
- MEDIUM (adequate understanding)
- HIGH (comprehensive understanding)

Output the knowledge level as a single word (LOW/MEDIUM/HIGH).
"""
            # Get model response
            response = self.knowledge_assessment_model.run({
                "text": prompt,
                "max_length": 10,  # We only need a single word response
            })

            # Parse response
            level = response.strip().upper()
            if level in [kl.name for kl in KnowledgeLevel]:
                return KnowledgeLevel[level]
            return None

        except Exception as e:
            print(f"Error assessing knowledge level: {e}")
            return None

    def generate_response(self, student_message, current_topic):
        # 根据当前主题和学生信息进行个性化指导
        prompt = student_message.content
        if current_topic:
            prompt += f"\n(Current topic: {current_topic})"

        # 调用 Qwen API
        response = self.run_with_qwen(prompt)
        message = BaseMessage(role_name="Teacher", role_type="ASSISTANT",
                              meta_dict=None, content=response)
        return message

    def step(self, input_message: BaseMessage, current_topic: str = None) -> BaseMessage:
        """处理一条消息并返回回复."""
        try:
            self.set_status(AgentStatus.THINKING, "思考问题中...")
            
            # 根据主题选择不同的处理方式
            content = input_message.content
            
            # 从消息中提取主题（如果存在）
            if not current_topic:
                for topic in self.available_topics:
                    if topic.lower() in content.lower():
                        current_topic = topic
                        break

            # 根据主题进行操作
            if current_topic:
                if "使用工具" in content:
                    # 提取工具名称和参数
                    try:
                        tool_info = content.split("使用工具")[1].strip()
                        tool_name = tool_info.split("(")[0].strip()
                        tool_params = tool_info.split("(")[1].split(")")[0].strip()
                        self.set_status(AgentStatus.USING_TOOL, "使用工具中...")
                        tool_response = self.use_tool(tool_name, tool_params)
                        response_content = f"Tool response: {tool_response}"
                    except Exception as e:
                        response_content = f"Error parsing tool information: {e}"
                elif "需要更多资料" in content:
                    # 构建发给 Knowledge Crawler Agent 的消息
                    self.set_status(AgentStatus.CRAWLING, "抓取网页内容...")
                    message_to_crawler = BaseMessage(
                        role_name="Teacher",
                        role_type="USER",
                        meta_dict=None,
                        content=json.dumps({
                            'topic': current_topic,
                            'action': 'crawl_data'
                        })
                    )

                    # 调用 Knowledge Crawler Agent
                    crawler_response = self.knowledge_crawler_agent.step(message_to_crawler)

                    # 使用 Knowledge Crawler Agent 返回的信息
                    response_content = f"Here's some information I found: {crawler_response.content}"
                elif "生成FAQ" in content:
                    # 构建发给 FAQ Generator Agent 的消息
                    self.set_status(AgentStatus.GENERATING_FAQ, "生成FAQ中...")
                    message_to_faq_generator = BaseMessage(
                        role_name="Teacher",
                        role_type="USER",
                        meta_dict=None,
                        content=json.dumps({
                            'topic': current_topic,
                            'action': 'generate_faq'
                        }),
                    )
                    faq_generator_response = self.faq_generator_agent.step(message_to_faq_generator)
                    response_content = f"Here are some FAQs generated: {faq_generator_response.content}"

                elif "生成测验" in content:
                    # 构建发给 Quiz Generator Agent 的消息
                    self.set_status(AgentStatus.GENERATING_QUIZ, "生成测验中...")
                    message_to_quiz_generator = BaseMessage(
                        role_name="Teacher",
                        role_type="USER",
                        meta_dict=None,
                        content=json.dumps({
                            'topic': current_topic,
                            'action': 'generate_quiz'
                        }),
                    )
                    quiz_generator_response = self.quiz_generator_agent.step(message_to_quiz_generator)
                    response_content = f"Here is a quiz for you: {quiz_generator_response.content}"
                else:
                    # 调用 Qwen API
                    self.set_status(AgentStatus.THINKING, "生成回复中...")
                    response_content = self.generate_response(input_message, current_topic)
            else:
                # 如果没有指定主题, 正常调用 Qwen API
                self.set_status(AgentStatus.THINKING, "生成回复中...")
                response_content = self.run_with_qwen(content)

            # Assess learning style and knowledge level
            if input_message.role_name.startswith("student_"):
                student_agent = agents.get(input_message.role_name)
                if student_agent:
                    # Assess learning style if not already set
                    if not hasattr(student_agent, 'learning_style') or not student_agent.learning_style:
                        self.set_status(AgentStatus.THINKING, "评估学习风格中...")
                        learning_style = self.assess_learning_style(input_message.role_name, student_agent.message_history)
                        if learning_style:
                            student_agent.learning_style = learning_style
                            print(f"Assessed learning style for {input_message.role_name}: {learning_style.value}")

                    # Assess knowledge level for the current topic
                    if current_topic:
                        self.set_status(AgentStatus.THINKING, "评估知识水平中...")
                        knowledge_level = self.assess_knowledge_level(input_message.role_name, current_topic, content)
                        if knowledge_level:
                            student_agent.knowledge_level = knowledge_level
                            print(f"Assessed knowledge level for {input_message.role_name}: {knowledge_level.value}")

            self.set_status(AgentStatus.IDLE)
            message = BaseMessage(role_name="Teacher", role_type="ASSISTANT",
                                meta_dict=None, content=response_content)
            return message

        except Exception as e:
            self.set_status(AgentStatus.ERROR, f"发生错误: {str(e)}")
            raise e

    def reset(self):
        """重置 Agent 状态."""
        super().reset()
        self.set_status(AgentStatus.IDLE)