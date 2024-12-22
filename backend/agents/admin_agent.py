import json
from typing import Dict, List, Optional

class AdminAgent:
    def __init__(self):
        self.config_file = "config.json"
        
    def update_config(self, action: str, params: Dict) -> str:
        """更新配置文件."""
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)

            if action == "add_topic":
                topic_name = params.get("topic_name")
                if topic_name in config["available_topics"]:
                    return f"Topic '{topic_name}' already exists."
                config["available_topics"].append(topic_name)
                config["topic_config"][topic_name] = params.get("topic_info", {})

            elif action == "modify_topic":
                topic_name = params.get("topic_name")
                if topic_name not in config["available_topics"]:
                    return f"Topic '{topic_name}' not found."
                config["topic_config"][topic_name] = params.get("topic_info", {})

            elif action == "delete_topic":
                topic_name = params.get("topic_name")
                if topic_name not in config["available_topics"]:
                    return f"Topic '{topic_name}' not found."
                config["available_topics"].remove(topic_name)
                del config["topic_config"][topic_name]

            else:
                return "Invalid action specified."

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)

            return f"Config updated successfully. Action: {action}"
        except Exception as e:
            return f"Error updating config: {e}"
            
    def step(self, message: str) -> str:
        """处理一条消息并返回回复"""
        try:
            # 解析消息
            if isinstance(message, str):
                try:
                    content = json.loads(message)
                    action = content.get("action")
                    params = content.get("params")
                    if action in ["add_topic", "modify_topic", "delete_topic"]:
                        return self.update_config(action, params)
                    return "Invalid action specified."
                except json.JSONDecodeError:
                    return "Invalid message format. Expected JSON string."
            return "Invalid message type. Expected string."
        except Exception as e:
            return f"处理消息时出错: {str(e)}"
