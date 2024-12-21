import json
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.configs import QwenConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
import os
from getpass import getpass

class FAQGeneratorAgent(ChatAgent):
    def __init__(self, system_message=None, model_type=None):
        if system_message is None:
          system_message = BaseMessage(
              role_name="FAQGenerator",
              role_type="USER",
              meta_dict=None,
              content="You are an FAQ generator. "
                      "You generate FAQs based on the given topic and provided text using the specified prompt in the config file."
          )
        super().__init__(system_message, model_type)

        # 加载配置文件
        with open("config.json", "r") as f:
            self.config = json.load(f)

        # 获取 API 密钥
        self.modelscope_api_key = os.environ.get("MODELSCOPE_API_KEY")
        if self.modelscope_api_key is None:
            print("ModelScope API Key not found in environment variables.")
            self.modelscope_api_key = getpass("Please enter your ModelScope API Key: ")
            os.environ["MODELSCOPE_API_KEY"] = self.modelscope_api_key

        # Qwen API 集成 (使用 ModelScope 兼容的 API)
        self.model_config = QwenConfig(
            model="Qwen/Qwen2.5-32B-Instruct",  # 使用 Qwen2.5-32B-Instruct 模型
            temperature=0.2,
        )
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="Qwen/Qwen2.5-32B-Instruct",  # 使用 Qwen2.5-32B-Instruct 模型
            api_key=self.modelscope_api_key,
            url="https://api-inference.modelscope.cn/v1/models/Qwen/Qwen2.5-32B-Instruct",
            model_config_dict=self.model_config.as_dict(),
        )

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"FAQ Generator received message: {message.content}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def generate_faq(self, topic, text):
        """根据主题和提供的文本生成 FAQ."""
        topic_info = self.config["topic_config"].get(topic)
        if not topic_info:
            return f"No configuration found for topic: {topic}"

        prompt = topic_info["faq_prompt"]
        prompt += f"\n\nText:\n{text}\n\nFAQs:\n"

        response = self.model.run(prompt)
        return response

    def step(self, input_message: BaseMessage) -> BaseMessage:
        try:
            content = json.loads(input_message.content)
            topic = content.get("topic")
            action = content.get("action")

            if action == "generate_faq":
                # 这里假设你已经有了要生成 FAQ 的文本数据
                # 你可以从之前的 Agent（如 KnowledgeCrawlerAgent）的输出中获取
                # 或者从其他数据源获取
                text = "这里应该是用于生成 FAQ 的文本数据。"  # 示例数据
                if topic == "photosynthesis":
                    text = """
                    Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water. Photosynthesis in plants generally involves the green pigment chlorophyll and generates oxygen as a byproduct.
                    """
                elif topic == "math_functions":
                    text = """
                    In mathematics, a function is a relation between sets that associates to every element of a first set exactly one element of the second set. Typical examples are functions from integers to integers, or from the real numbers to real numbers.
                    """
                elif topic == "world_history":
                    text = """
                    World history or global history as a field of historical study examines history from a global perspective. It traces the history of the entire world, including the history of Africa, Americas, Asia, Europe, and Oceania, and their interactions.
                    """
                # 如果需要根据爬取的数据生成 FAQ，可以先调用 KnowledgeCrawlerAgent
                # crawler_message = BaseMessage(...)
                # crawler_response = self.knowledge_crawler_agent.step(crawler_message)
                # text = crawler_response.content

                faq = self.generate_faq(topic, text)
                message = BaseMessage(role_name="FAQGenerator", role_type="AI",
                                      meta_dict=None, content=faq)
                return message
            else:
                error_msg = "Invalid action specified for FAQGenerator."
                message = BaseMessage(role_name="FAQGenerator", role_type="AI",
                                      meta_dict=None, content=error_msg)
                return message
        except Exception as e:
            error_msg = f"Error in FAQGeneratorAgent: {e}"
            message = BaseMessage(role_name="FAQGenerator", role_type="AI",
                                  meta_dict=None, content=error_msg)
            return message