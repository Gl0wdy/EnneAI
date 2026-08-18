from enneai.ai.modules.chat import ChatClient
from enneai.config import OPENROUTER_PRIMARY_MODEL

class Jung(ChatClient):
    def __init__(
        self,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/jung/prompt.txt",
            corr="data/corr/correlations.txt",
            model=model
        )