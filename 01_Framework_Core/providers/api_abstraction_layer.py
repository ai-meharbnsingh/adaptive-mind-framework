# 01_Framework_Core/providers/api_abstraction_layer.py
class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class CompletionResponse:
    def __init__(
        self, success: bool = True, content: str = "", model_used: str = "", **kwargs
    ):
        self.success = success
        self.content = content
        self.model_used = model_used
        for k, v in kwargs.items():
            setattr(self, k, v)
