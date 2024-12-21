from camel.agents import ChatAgent
from camel.messages import BaseMessage

class MultimodalAgent(ChatAgent):
    def __init__(self, qwen_vl_model, system_message=None, model_type=None):
        if system_message is None:
            system_message = BaseMessage(
                role_name="MultimodalAgent",
                role_type="ASSISTANT",
                meta_dict=None,
                content="You are a helpful assistant that can process both text and images."
            )
        super().__init__(system_message, model_type)
        self.model = qwen_vl_model

    def step(self, input_message: BaseMessage) -> BaseMessage:
        # 使用 Qwen-VL 模型处理多模态消息
        response = self.model.run(input_message)

        # 由于 Qwen-VL 的输出可能包含多条消息，这里只取第一条
        response_content = response.msgs[0].content

        message = BaseMessage(role_name="MultimodalAgent", role_type="ASSISTANT",
                              meta_dict=None, content=response_content)
        return message