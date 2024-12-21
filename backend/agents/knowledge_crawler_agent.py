import json
import requests
from bs4 import BeautifulSoup
from camel.agents import ChatAgent
from camel.messages import BaseMessage

class KnowledgeCrawlerAgent(ChatAgent):
    def __init__(self, system_message=None, model_type=None):
        if system_message is None:
          system_message = BaseMessage(
              role_name="KnowledgeCrawler",
              role_type="USER",
              meta_dict=None,
              content="You are a knowledge crawler. "
                      "You crawl web pages based on the given topic and keywords from the config file."
          )
        super().__init__(system_message, model_type)

        # 加载配置文件
        with open("config.json", "r") as f:
            self.config = json.load(f)

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"Knowledge Crawler received message: {message.content}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def crawl_data(self, topic):
        """根据主题配置爬取数据."""
        topic_info = self.config["topic_config"].get(topic)
        if not topic_info:
            return f"No configuration found for topic: {topic}"

        keywords = topic_info["keywords"]
        target_websites = topic_info["target_websites"]

        extracted_content = ""
        for keyword in keywords:
            for site in target_websites:
                url = f"{site}?search={keyword}"  # 简单的搜索 URL 构造
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # 提取网页内容
                    for paragraph in soup.find_all('p'):
                        extracted_content += paragraph.text + "\n"
                except requests.exceptions.RequestException as e:
                    print(f"Error crawling {url}: {e}")

        return extracted_content or "No relevant content found for this topic."

    def step(self, input_message: BaseMessage) -> BaseMessage:
        try:
            content = json.loads(input_message.content)
            topic = content.get("topic")
            action = content.get("action")

            if action == "crawl_data":
                result = self.crawl_data(topic)
                message = BaseMessage(role_name="KnowledgeCrawler", role_type="AI",
                                    meta_dict=None, content=result)
                return message
            else:
                error_msg = "Invalid action specified for KnowledgeCrawler."
                message = BaseMessage(role_name="KnowledgeCrawler", role_type="AI",
                                    meta_dict=None, content=error_msg)
                return message
        except Exception as e:
            error_msg = f"Error in KnowledgeCrawlerAgent: {e}"
            message = BaseMessage(role_name="KnowledgeCrawler", role_type="AI",
                                  meta_dict=None, content=error_msg)
            return message