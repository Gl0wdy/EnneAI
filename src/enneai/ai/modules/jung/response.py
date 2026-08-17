from enneai.ai.modules.chat import ChatClient


class Jung(ChatClient):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/jung/prompt.txt",
            corr="data/corr/correlations.txt",
            model=model,
            api_key=api_key,
        )