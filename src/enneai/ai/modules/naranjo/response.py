from enneai.ai.modules.chat import ChatClient
from enneai.config import OPENROUTER_PRIMARY_MODEL

from enneai.utils.reader import load_file
from enneai.config import OPENROUTER_SECONDARY_MODEL


class Naranjo(ChatClient):
    def __init__(
        self,
        model: str | None = OPENROUTER_PRIMARY_MODEL
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/naranjo/prompt.txt",
            model=model
        )
        self.requery_prompt = load_file('src/enneai/ai/modules/naranjo/requery_prompt.txt')

    async def requery(
        self,
        query: str,
        history: list[dict],
        api_key: str | None = None
    ) -> str:
        prompt = self.requery_prompt.replace(
            '<CONTEXT>', self.contexts['ennea']
        )
        history = [
            {'role': 'system', 'content': prompt}
        ] + history + [{'role': 'user', 'content': query}]

        response = await self.get_discrete(
            history,
            api_key=api_key,
            model=OPENROUTER_SECONDARY_MODEL,
            reasoning=False,
            max_tokens=50
        )
        print(response['choices'][0]['message']['content'])
        
        return response['choices'][0]['message']['content']