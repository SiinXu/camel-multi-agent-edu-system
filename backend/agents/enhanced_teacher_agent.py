import os
from typing import Dict, Any, Optional
from datetime import datetime
import json
import asyncio
from ..core.agent import Agent, AgentState
from ..core.blackboard import Blackboard
from enum import Enum
import logging

from camel.messages import BaseMessage
from camel.configs import QwenConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType

logger = logging.getLogger(__name__)

class TeacherAgentState(Enum):
    TEACHING = "teaching"
    EVALUATING = "evaluating"
    PLANNING = "planning"
    RESEARCHING = "researching"
    COLLABORATING = "collaborating"

class EnhancedTeacherAgent(Agent):
    def __init__(self, agent_id: str, blackboard: Blackboard):
        super().__init__(agent_id, blackboard)
        
        # Initialize ModelScope integration
        self.modelscope_api_key = os.environ.get("MODELSCOPE_API_KEY")
        self.model_config = QwenConfig(
            model="Qwen/Qwen2.5-32B-Instruct",
            temperature=0.2,
        )
        
        # Initialize models
        self._initialize_models()
        
        # Initialize teaching state
        self.current_topic = None
        self.current_student_id = None
        self.teaching_state = TeacherAgentState.PLANNING
        
        # Load configuration
        self._load_config()

    def _initialize_models(self):
        """Initialize AI models"""
        try:
            self.main_model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type="Qwen/Qwen2.5-32B-Instruct",
                api_key=self.modelscope_api_key,
                url="https://api-inference.modelscope.cn/v1/models/Qwen/Qwen2.5-32B-Instruct",
                model_config_dict=self.model_config.as_dict(),
            )
            
            self.learning_style_model = ModelFactory.create(
                model_platform=ModelPlatformType.MODEL_SCOPE,
                model_type="qwen/Qwen-7B-Chat",
                api_key=self.modelscope_api_key,
                model_config_dict={
                    "device": "cuda" if os.environ.get("USE_GPU", "0") == "1" else "cpu",
                    "max_length": 2048,
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            self.knowledge_assessment_model = ModelFactory.create(
                model_platform=ModelPlatformType.MODEL_SCOPE,
                model_type="qwen/Qwen-7B-Chat",
                api_key=self.modelscope_api_key,
                model_config_dict={
                    "device": "cuda" if os.environ.get("USE_GPU", "0") == "1" else "cpu",
                    "max_length": 2048,
                    "temperature": 0.2,
                    "top_p": 0.9
                }
            )
            
            logger.info("All models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            raise

    def _load_config(self):
        """Load configuration from file"""
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
            self.available_topics = self.config["available_topics"]
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    async def run(self) -> None:
        """Main execution loop"""
        try:
            # Check for new messages on the blackboard
            messages = await self.read_from_blackboard("student_messages")
            if messages:
                for message in messages:
                    response = await self.process_message(message)
                    if response:
                        await self.write_to_blackboard(
                            f"teacher_response_{message['student_id']}",
                            response,
                            metadata={"topic": self.current_topic}
                        )

            # Update teaching state based on current context
            await self._update_teaching_state()
            
            # Perform state-specific actions
            await self._execute_teaching_actions()
            
        except Exception as e:
            logger.error(f"Error in teacher agent run loop: {str(e)}")
            self.state = AgentState.ERROR

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming student message"""
        try:
            self.current_student_id = message.get("student_id")
            self.current_topic = message.get("topic")
            
            # Update student model
            await self._update_student_model(message)
            
            # Generate response based on teaching state
            response = await self._generate_response(message)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"error": str(e)}

    async def _update_teaching_state(self):
        """Update teaching state based on context"""
        try:
            # Read student progress from blackboard
            progress = await self.read_from_blackboard(f"student_progress_{self.current_student_id}")
            
            if not progress:
                self.teaching_state = TeacherAgentState.PLANNING
            elif progress.get("needs_evaluation"):
                self.teaching_state = TeacherAgentState.EVALUATING
            elif progress.get("needs_research"):
                self.teaching_state = TeacherAgentState.RESEARCHING
            else:
                self.teaching_state = TeacherAgentState.TEACHING
                
        except Exception as e:
            logger.error(f"Error updating teaching state: {str(e)}")
            self.teaching_state = TeacherAgentState.PLANNING

    async def _execute_teaching_actions(self):
        """Execute actions based on current teaching state"""
        try:
            if self.teaching_state == TeacherAgentState.PLANNING:
                await self._plan_lesson()
            elif self.teaching_state == TeacherAgentState.EVALUATING:
                await self._evaluate_student()
            elif self.teaching_state == TeacherAgentState.RESEARCHING:
                await self._research_topic()
            elif self.teaching_state == TeacherAgentState.TEACHING:
                await self._deliver_lesson()
        except Exception as e:
            logger.error(f"Error executing teaching actions: {str(e)}")

    async def _update_student_model(self, message: Dict[str, Any]):
        """Update the student model based on interaction"""
        try:
            # Assess learning style
            learning_style = await self._assess_learning_style(message)
            
            # Assess knowledge level
            knowledge_level = await self._assess_knowledge_level(message)
            
            # Update student model on blackboard
            await self.write_to_blackboard(
                f"student_model_{self.current_student_id}",
                {
                    "learning_style": learning_style,
                    "knowledge_level": knowledge_level,
                    "last_update": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error updating student model: {str(e)}")

    async def _assess_learning_style(self, message: Dict[str, Any]) -> str:
        """Assess student's learning style"""
        # Implementation using self.learning_style_model
        return "visual"  # Placeholder

    async def _assess_knowledge_level(self, message: Dict[str, Any]) -> str:
        """Assess student's knowledge level"""
        # Implementation using self.knowledge_assessment_model
        return "intermediate"  # Placeholder

    async def _generate_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response based on teaching state and student model"""
        try:
            student_model = await self.read_from_blackboard(f"student_model_{self.current_student_id}")
            
            # Prepare context for response generation
            context = {
                "message": message,
                "student_model": student_model,
                "teaching_state": self.teaching_state,
                "topic": self.current_topic
            }
            
            # Generate response using main model
            response = await self._generate_with_model(context)
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {"error": "Failed to generate response"}
