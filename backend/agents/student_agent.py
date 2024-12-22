from typing import Dict, Optional
from enum import Enum

class StudentAgent:
    """学生 Agent."""

    def __init__(self, student_id: str):
        """初始化学生 Agent."""
        self.student_id = student_id
        self.conversation_history = []
        self.learning_style = None
        self.knowledge_level = None
        self.interests = []
        self.current_topic = None

    def process_teacher_response(self, response: str) -> str:
        """处理教师的回复."""
        try:
            # 记录对话历史
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # 这里可以添加更多处理逻辑，比如：
            # 1. 分析教师回复中的关键信息
            # 2. 更新学生的知识水平
            # 3. 生成跟进问题
            # 等等
            
            return response
        except Exception as e:
            error_message = f"处理教师回复时出错: {str(e)}"
            print(error_message)
            return error_message

    def update_learning_style(self, style: str):
        """更新学习风格."""
        self.learning_style = style

    def update_knowledge_level(self, topic: str, level: str):
        """更新知识水平."""
        self.knowledge_level = level

    def add_interest(self, topic: str):
        """添加感兴趣的主题."""
        if topic not in self.interests:
            self.interests.append(topic)

    def set_current_topic(self, topic: str):
        """设置当前学习主题."""
        self.current_topic = topic

    def get_profile(self) -> Dict:
        """获取学生档案."""
        return {
            "student_id": self.student_id,
            "learning_style": self.learning_style,
            "knowledge_level": self.knowledge_level,
            "interests": self.interests,
            "current_topic": self.current_topic
        }