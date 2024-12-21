import json
import random
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.configs import QwenConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
import os
from getpass import getpass

class QuizGeneratorAgent(ChatAgent):
    def __init__(self, system_message=None, model_type=None):
        if system_message is None:
          system_message = BaseMessage(
              role_name="QuizGenerator",
              role_type="USER",
              meta_dict=None,
              content="You are a quiz generator. "
                      "You generate quizzes based on the given topic, using the question bank or prompt in the config file."
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
        print(f"Quiz Generator received message: {message.content}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def generate_quiz_from_bank(self, topic, num_questions=3):
        """根据主题从题库中选题，生成测验."""
        topic_info = self.config["topic_config"].get(topic)
        if not topic_info:
            return f"No configuration found for topic: {topic}"

        question_bank = topic_info.get("question_bank", [])
        if not question_bank:
            return f"No question bank found for topic: {topic}"

        random.shuffle(question_bank)
        return question_bank[:num_questions]

    def generate_quiz_from_prompt(self, topic, text):
        """根据主题和提供的文本，使用 prompt 生成测验题."""
        topic_info = self.config["topic_config"].get(topic)
        if not topic_info:
            return f"No configuration found for topic: {topic}"

        prompt = topic_info.get("quiz_prompt")
        if not prompt:
            return f"No quiz generation prompt found for topic: {topic}"

        # 使用 Qwen 模型生成测验题
        full_prompt = f"{prompt}\n\nText:\n{text}\n\nQuestions:\n"
        response = self.model.run(full_prompt)
        return response

    def step(self, input_message: BaseMessage) -> BaseMessage:
        try:
            content = json.loads(input_message.content)
            topic = content.get("topic")
            action = content.get("action")

            if action == "generate_quiz":
                # 你可以选择从题库生成测验或使用 prompt 生成
                # quiz = self.generate_quiz_from_bank(topic)
                
                # 如果想使用 prompt 生成，你需要提供一个文本作为生成的依据
                # 例如，你可以使用 KnowledgeCrawlerAgent 爬取的文本
                # 或者使用其他的文本数据
                text = "这里应该是用于生成测验题的文本数据。"  # 示例数据
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
                quiz = self.generate_quiz_from_prompt(topic, text)
                
                if isinstance(quiz, str):
                  # 如果是 prompt 生成的，直接返回
                  message = BaseMessage(role_name="QuizGenerator", role_type="AI",
                                        meta_dict=None, content=quiz)
                  return message
                else:
                  # 将测验题目格式化为字符串
                  quiz_str = ""
                  for i, q in enumerate(quiz):
                      quiz_str += f"Question {i+1}: {q['question']} (Type: {q['type']})\n"
                      quiz_str += f"Answer: {q['answer']}\n"

                  message = BaseMessage(role_name="QuizGenerator", role_type="AI",
                                        meta_dict=None, content=quiz_str)
                  return message
            else:
                error_msg = "Invalid action specified for QuizGenerator."
                message = BaseMessage(role_name="QuizGenerator", role_type="AI",
                                      meta_dict=None, content=error_msg)
                return message
        except Exception as e:
            error_msg = f"Error in QuizGeneratorAgent: {e}"
            message = BaseMessage(role_name="QuizGenerator", role_type="AI",
                                  meta_dict=None, content=error_msg)
            return message