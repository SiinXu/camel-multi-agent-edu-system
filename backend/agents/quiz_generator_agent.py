from typing import Dict, List, Optional
import random
from duckduckgo_search import DDGS

class QuizGeneratorAgent:
    def __init__(self):
        self.name = "QuizGeneratorAgent"
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
                return self.generate_quiz(topic)
                
            return "请提供要生成测验的主题"
            
        except Exception as e:
            return f"处理消息时出错: {str(e)}"
