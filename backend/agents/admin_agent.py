import json
from camel.agents import ChatAgent
from camel.messages import BaseMessage

class AdminAgent(ChatAgent):
    def __init__(self, system_message=None, model_type=None):
        if system_message is None:
          system_message = BaseMessage(
              role_name="Admin",
              role_type="USER",
              meta_dict=None,
              content="You are an administrator. "
                      "You can manage the system configuration, such as adding, modifying, or deleting topics in the config file."
          )
        super().__init__(system_message, model_type)

    def receive_message(self, message):
        # 这里可以添加处理消息的逻辑，例如记录消息、触发特定动作等
        print(f"Admin received message: {message.content}")

    def send_message(self, message, recipient):
        recipient.receive_message(message)

    def update_config(self, action, params):
        """更新配置文件."""
        try:
            with open("config.json", "r") as f:
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

            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

            return f"Config updated successfully. Action: {action}"
        except Exception as e:
            return f"Error updating config: {e}"

    def step(self, input_message: BaseMessage) -> BaseMessage:
        try:
            content = json.loads(input_message.content)
            action = content.get("action")
            params = content.get("params")

            if action in ["add_topic", "modify_topic", "delete_topic"]:
                result = self.update_config(action, params)
                message = BaseMessage(role_name="Admin", role_type="AI",
                                      meta_dict=None, content=result)
                return message
            else:
                error_msg = "Invalid action specified for AdminAgent."
                message = BaseMessage(role_name="Admin", role_type="AI",
                                      meta_dict=None, content=error_msg)
                return message
        except Exception as e:
            error_msg = f"Error in AdminAgent: {e}"
            message = BaseMessage(role_name="Admin", role_type="AI",
                                  meta_dict=None, content=error_msg)
            return message