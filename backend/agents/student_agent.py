from typing import List, Dict, Optional

class StudentAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.learning_style = None
        self.knowledge_level = None
        self.conversation_history = []
        self.current_topic = None
        
    def receive_message(self, message: str):
        """接收消息"""
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })
        
    def send_message(self, message: str) -> str:
        """发送消息"""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        return message
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def set_learning_style(self, style: str):
        """设置学习风格"""
        self.learning_style = style
        
    def set_knowledge_level(self, level: str):
        """设置知识水平"""
        self.knowledge_level = level
        
    def set_topic(self, topic: str):
        """设置当前主题"""
        self.current_topic = topic
        
    def get_status(self) -> Dict[str, str]:
        """获取状态信息"""
        return {
            "agent_id": self.agent_id,
            "learning_style": self.learning_style,
            "knowledge_level": self.knowledge_level,
            "current_topic": self.current_topic
        }
        
    def step(self, message: dict) -> str:
        """处理一条消息并返回回复."""
        try:
            # 从消息中获取内容
            content = message.get("content", "")
            current_topic = message.get("topic")
            
            # 更新当前主题
            if current_topic:
                self.set_topic(current_topic)
                
            # 记录消息
            self.conversation_history.append({
                "role": "user",
                "content": content
            })
            
            # 生成回复
            response = f"Student {self.agent_id} received message: {content}"
            
            # 记录回复
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except Exception as e:
            return f"Error processing message: {str(e)}"