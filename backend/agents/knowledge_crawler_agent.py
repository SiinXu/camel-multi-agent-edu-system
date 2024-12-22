import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import Dict, List, Optional

class KnowledgeCrawlerAgent:
    def __init__(self):
        self.name = "KnowledgeCrawlerAgent"
        self.search_engine = DDGS(timeout=20)

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"Knowledge Crawler received message: {message}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

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
            
    def step(self, message: dict) -> str:
        """处理一条消息并返回回复"""
        try:
            # 从消息中获取内容和主题
            content = message.get("content", "")
            topic = message.get("topic")
            
            # 如果没有主题，尝试从内容中提取
            if not topic and isinstance(content, str) and "topic=" in content:
                topic = content.split("topic=")[1].split("&")[0]
                
            if topic:
                return self.crawl(topic)
                
            return "请提供要抓取的主题"
            
        except Exception as e:
            return f"处理消息时出错: {str(e)}"