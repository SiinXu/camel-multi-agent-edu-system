from typing import Dict, List, Optional
import random
from duckduckgo_search import DDGS

class QuizGeneratorAgent:
    def __init__(self):
        self.search_engine = DDGS()
        
    def generate_quiz(self, topic: str) -> str:
        """生成特定主题的测验"""
        try:
            results = list(self.search_engine.text(f"{topic} quiz questions", max_results=5))
            quiz = []
            for i, result in enumerate(results, 1):
                quiz.append(f"Question {i}: {result['title']}")
                quiz.append(f"Hint: {result['body']}\n")
            return "\n".join(quiz) if quiz else f"未找到关于 {topic} 的测验题"
        except Exception as e:
            return f"生成测验时出错: {str(e)}"
            
    def step(self, message: str) -> str:
        """处理一条消息并返回回复"""
        try:
            # 解析消息
            if isinstance(message, str) and "topic=" in message:
                topic = message.split("topic=")[1].split("&")[0]
                return self.generate_quiz(topic)
            return "请提供要生成测验的主题，格式：topic=主题名"
        except Exception as e:
            return f"处理消息时出错: {str(e)}"
