from enneai.ai.modules.chat import ChatClient


class Naranjo(ChatClient):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/naranjo/prompt.txt",
            model=model,
            api_key=api_key,
        )