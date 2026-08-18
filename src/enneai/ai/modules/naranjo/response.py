from enneai.ai.modules.chat import ChatClient
from enneai.config import OPENROUTER_PRIMARY_MODEL


class Naranjo(ChatClient):
    def __init__(
        self,
        model: str | None = OPENROUTER_PRIMARY_MODEL
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/naranjo/prompt.txt",
            model=model
        )