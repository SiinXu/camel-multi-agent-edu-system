import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import Dict, List, Optional

class KnowledgeCrawlerAgent:
    def __init__(self, system_message=None, model_type=None):
        if system_message is None:
          system_message = {
              "role_name": "KnowledgeCrawler",
              "role_type": "USER",
              "meta_dict": None,
              "content": "You are a knowledge crawler. "
                      "You crawl web pages based on the given topic and keywords from the config file."
          }
        self.system_message = system_message
        self.model_type = model_type
        
        # 加载配置文件
        with open("config.json", "r") as f:
            self.config = json.load(f)
            
        self.search_engine = DDGS()

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"Knowledge Crawler received message: {message}")

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

    def crawl(self, topic: str) -> str:
        """抓取特定主题的知识"""
        try:
            results = list(self.search_engine.text(topic, max_results=5))
            return f"已找到关于 {topic} 的 {len(results)} 条信息：\n" + "\n".join(
                f"{i+1}. {result['title']}: {result['body']}"
                for i, result in enumerate(results)
            )
        except Exception as e:
            return f"抓取知识时出错: {str(e)}"
            
    def step(self, input_message: str) -> str:
        """处理一条消息并返回回复"""
        try:
            # 解析消息
            if isinstance(input_message, str) and "topic=" in input_message:
                topic = input_message.split("topic=")[1].split("&")[0]
                return self.crawl(topic)
            return "请提供要抓取的主题，格式：topic=主题名"
        except Exception as e:
            return f"处理消息时出错: {str(e)}"