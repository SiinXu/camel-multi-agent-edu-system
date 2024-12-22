from typing import Dict, List, Optional
from enum import Enum
from duckduckgo_search import DDGS
import httpx

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    CRAWLING = "crawling"
    GENERATING_FAQ = "generating_faq"
    GENERATING_QUIZ = "generating_quiz"
    ERROR = "error"
    USING_TOOL = "using_tool"

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"

class KnowledgeLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TeacherAgent:
    def __init__(self, agent_id: str = "teacher_agent"):
        self.agent_id = agent_id
        self.search_engine = DDGS()
        self.conversation_history = []
        self._status = AgentStatus.IDLE
        self._status_message = ""
        self.learning_style_model = None
        self.knowledge_assessment_model = None
        self.tools = {
            "DuckDuckGoSearchTool": DDGS(),
        }
        self.knowledge_crawler_agent = None
        self.faq_generator_agent = None
        self.quiz_generator_agent = None
        self.available_topics = []
        self.model_config = {
            "temperature": 0.2,
        }
        self.model = None

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
        print(f"Teacher received message: {message}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def search(self, query: str) -> str:
        """使用 DuckDuckGo 搜索信息"""
        try:
            self.set_status(AgentStatus.CRAWLING)
            results = list(self.search_engine.text(query, max_results=3))
            return "\n".join(f"{r['title']}: {r['body']}" for r in results)
        except Exception as e:
            return f"搜索时出错: {str(e)}"
        finally:
            self.set_status(AgentStatus.IDLE)

    def answer_question(self, question: str, topic: Optional[str] = None) -> str:
        """回答学生的问题"""
        try:
            self.set_status(AgentStatus.THINKING)
            
            # 记录对话历史
            self.conversation_history.append({"role": "user", "content": question})

            # 根据主题和问题生成回答
            if topic:
                response = f"关于{topic}的问题：{question}\n"
            else:
                response = f"问题：{question}\n"

            # 搜索相关信息
            search_query = f"{topic} {question}" if topic else question
            search_results = self.search(search_query)
            
            # 生成回答
            response += f"\n根据搜索结果，我为您整理了以下信息：\n\n{search_results}"
            
            # 记录回答
            self.conversation_history.append({"role": "assistant", "content": response})

            return response
        except Exception as e:
            return f"回答问题时出错: {str(e)}"
        finally:
            self.set_status(AgentStatus.IDLE)

    def process_file(self, file_content: str) -> str:
        """处理上传的文件内容"""
        try:
            self.set_status(AgentStatus.THINKING)
            # 简单地返回文件内容的摘要
            return f"文件内容摘要：\n{file_content[:500]}..." if len(file_content) > 500 else file_content
        except Exception as e:
            return f"处理文件时出错: {str(e)}"
        finally:
            self.set_status(AgentStatus.IDLE)

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history

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
        prompt = student_message
        if current_topic:
            prompt += f"\n(Current topic: {current_topic})"

        # 调用 Qwen API
        response = self.answer_question(prompt, current_topic)
        return response

    def step(self, message: dict) -> str:
        """处理一条消息并返回回复."""
        try:
            self.set_status(AgentStatus.THINKING, "思考问题中...")

            # 从消息中获取内容
            content = message.get("content", "")
            current_topic = message.get("topic")

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
                    message_to_crawler = f"topic={current_topic}&action=crawl_data"

                    # 调用 Knowledge Crawler Agent
                    crawler_response = self.knowledge_crawler_agent.step(message_to_crawler)

                    # 使用 Knowledge Crawler Agent 返回的信息
                    response_content = f"Here's some information I found: {crawler_response}"
                elif "生成FAQ" in content:
                    # 构建发给 FAQ Generator Agent 的消息
                    self.set_status(AgentStatus.GENERATING_FAQ, "生成FAQ中...")
                    message_to_faq_generator = f"topic={current_topic}&action=generate_faq"
                    faq_generator_response = self.faq_generator_agent.step(message_to_faq_generator)
                    response_content = f"Here are some FAQs generated: {faq_generator_response}"

                elif "生成测验" in content:
                    # 构建发给 Quiz Generator Agent 的消息
                    self.set_status(AgentStatus.GENERATING_QUIZ, "生成测验中...")
                    message_to_quiz_generator = f"topic={current_topic}&action=generate_quiz"
                    quiz_generator_response = self.quiz_generator_agent.step(message_to_quiz_generator)
                    response_content = f"Here is a quiz for you: {quiz_generator_response}"
                else:
                    # 调用 Qwen API
                    self.set_status(AgentStatus.THINKING, "生成回复中...")
                    response_content = self.generate_response(content, current_topic)
            else:
                # 如果没有指定主题, 正常调用 Qwen API
                self.set_status(AgentStatus.THINKING, "生成回复中...")
                response_content = self.answer_question(content)

            self.set_status(AgentStatus.IDLE)
            return response_content

        except Exception as e:
            self.set_status(AgentStatus.ERROR, f"发生错误: {str(e)}")
            raise e

    def reset(self):
        """重置 Agent 状态."""
        self.set_status(AgentStatus.IDLE)

    def use_tool(self, tool_name: str, tool_params: str) -> str:
        """使用工具."""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            try:
                if tool_name == "DuckDuckGoSearchTool":
                    result = tool(tool_params)
                else:
                    result = "Tool does not support specified parameters."

                ret = json.dumps(result, ensure_ascii=False, indent=2)
                return ret
            except Exception as e:
                return f"Error using tool {tool_name}: {e}"
        else:
            return f"Tool {tool_name} not found."