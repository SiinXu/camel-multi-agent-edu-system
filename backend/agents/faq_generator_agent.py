from typing import Dict, List, Optional
from duckduckgo_search import DDGS

class FAQGeneratorAgent:
    def __init__(self):
        self.name = "FAQGeneratorAgent"
        self.search_engine = DDGS(timeout=20)
        
    def generate_faq(self, topic: str) -> str:
        """生成特定主题的 FAQ"""
        try:
            results = list(self.search_engine.text(f"{topic} FAQ", max_results=5))
            faqs = []
            for i, result in enumerate(results, 1):
                faqs.append(f"Q{i}: {result['title']}")
                faqs.append(f"A{i}: {result['body']}\n")
            return "\n".join(faqs) if faqs else f"未找到关于 {topic} 的常见问题"
        except Exception as e:
            return f"生成 FAQ 时出错: {str(e)}"
            
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
                return self.generate_faq(topic)
                
            return "请提供要生成 FAQ 的主题"
            
        except Exception as e:
            return f"处理消息时出错: {str(e)}"