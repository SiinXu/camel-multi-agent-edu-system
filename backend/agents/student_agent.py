from typing import Optional, List, Dict, Any
from datetime import datetime
from camel.agents import ChatAgent
from camel.messages import BaseMessage

from .teacher_agent import LearningStyle, KnowledgeLevel

class StudentAgent(ChatAgent):
    def __init__(self, name: str, model_type=None):
        system_message = BaseMessage(
            role_name=name,
            role_type="USER",
            meta_dict=None,
            content="You are a student who wants to learn."
        )
        super().__init__(system_message, model_type)
        
        self.name = name
        self.learning_style: Optional[LearningStyle] = None
        self.knowledge_level: Optional[KnowledgeLevel] = None
        self.message_history: List[Dict[str, Any]] = []
        self.study_records: List[Dict[str, Any]] = []

    def step(self, input_message: BaseMessage) -> BaseMessage:
        """Process a message and return a reply."""
        # Record the message in history
        self.message_history.append({
            "role": input_message.role_name,
            "content": input_message.content,
            "timestamp": datetime.now().isoformat()
        })

        # Generate response based on learning style and knowledge level
        prompt = self._build_personalized_prompt(input_message.content)
        response = self.model.run(prompt)

        # Record the response in history
        self.message_history.append({
            "role": self.name,
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        return BaseMessage(
            role_name=self.name,
            role_type="USER",
            meta_dict=None,
            content=response
        )

    def _build_personalized_prompt(self, content: str) -> str:
        """Build a prompt that takes into account the student's learning style and knowledge level."""
        style_prompt = ""
        if self.learning_style:
            style_prompt = f"\nAs a {self.learning_style.value} learner, you prefer "
            if self.learning_style == LearningStyle.VISUAL:
                style_prompt += "visual explanations with diagrams and charts."
            elif self.learning_style == LearningStyle.AUDITORY:
                style_prompt += "verbal explanations and discussions."
            elif self.learning_style == LearningStyle.KINESTHETIC:
                style_prompt += "hands-on activities and practical examples."
            elif self.learning_style == LearningStyle.READING_WRITING:
                style_prompt += "written explanations and note-taking."

        level_prompt = ""
        if self.knowledge_level:
            level_prompt = f"\nYour current understanding is at a {self.knowledge_level.value} level."

        return f"""You are a student with the following characteristics:{style_prompt}{level_prompt}
Based on these characteristics, respond to the following message:

{content}

Remember to stay in character and respond in a way that reflects your learning style and knowledge level."""

    def update_learning_style(self, style: LearningStyle):
        """Update the student's learning style."""
        self.learning_style = style
        print(f"Updated learning style for {self.name} to {style.value}")

    def update_knowledge_level(self, level: KnowledgeLevel):
        """Update the student's knowledge level."""
        self.knowledge_level = level
        print(f"Updated knowledge level for {self.name} to {level.value}")

    def add_study_record(self, topic: str, content: str, score: Optional[float] = None):
        """Add a study record for the student."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "content": content,
            "score": score
        }
        self.study_records.append(record)

    def get_study_records(self) -> List[Dict[str, Any]]:
        """Get all study records for the student."""
        return self.study_records

    def get_message_history(self) -> List[Dict[str, Any]]:
        """Get the message history for the student."""
        return self.message_history

    def clear_history(self):
        """Clear the message history."""
        self.message_history = []