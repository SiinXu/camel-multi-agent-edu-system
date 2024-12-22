import json
from typing import Dict, List, Optional

class AdminAgent:
    def __init__(self):
        self.name = "AdminAgent"
        self.config_file = "config.json"
        self.available_topics = []
        self.topic_config = {}
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
                self.available_topics = config.get("available_topics", [])
                self.topic_config = config.get("topic_config", {})
        except FileNotFoundError:
            # 如果配置文件不存在，创建一个新的
            self.save_config()
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            
    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                "available_topics": self.available_topics,
                "topic_config": self.topic_config
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
        
    def update_config(self, action: str, params: Dict) -> str:
        """更新配置文件."""
        try:
            topic_name = params.get("topic_name")
            if not topic_name:
                return "Topic name is required."

            if action == "add_topic":
                if topic_name in self.available_topics:
                    return f"Topic '{topic_name}' already exists."
                self.available_topics.append(topic_name)
                self.topic_config[topic_name] = params.get("topic_info", {})

            elif action == "modify_topic":
                if topic_name not in self.available_topics:
                    return f"Topic '{topic_name}' not found."
                self.topic_config[topic_name] = params.get("topic_info", {})

            elif action == "delete_topic":
                if topic_name not in self.available_topics:
                    return f"Topic '{topic_name}' not found."
                self.available_topics.remove(topic_name)
                del self.topic_config[topic_name]

            else:
                return "Invalid action specified."

            self.save_config()
            return f"Config updated successfully. Action: {action}"
            
        except Exception as e:
            return f"Error updating config: {e}"
            
    def step(self, message: dict) -> str:
        """处理一条消息并返回回复"""
        try:
            # 从消息中获取内容
            content = message.get("content", "")
            
            # 解析消息内容
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                    action = data.get("action")
                    params = data.get("params", {})
                    if action in ["add_topic", "modify_topic", "delete_topic"]:
                        return self.update_config(action, params)
                    return "Invalid action specified."
                except json.JSONDecodeError:
                    return "Invalid message format. Expected JSON string."
            return "Invalid message type. Expected string."
            
        except Exception as e:
            return f"处理消息时出错: {str(e)}"
