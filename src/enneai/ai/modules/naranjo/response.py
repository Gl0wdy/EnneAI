from enneai.ai.llm import OpenRouterClient
from enneai.ai.rag import retrieve

from utils.reader import load_file


class NaranjoClient:
    PROMPT = load_file('prompt.txt')
    CTX = {
        'ennea': load_file('data/ennea/context.txt'),
        'socio': load_file('data/socio/context.txt'),
        'psychosophy': load_file('data/psychosophy/content.txt')
    }

    def __init__(self, model: str, api_key: str | None = None):
        self.client = OpenRouterClient(model=model, api_key=api_key)

    def _build_prompt(self, rag_data: str, context: str):
        return self.PROMPT.replace('<RAG>', rag_data).replace('<CONTEXT>', context)

    async def response(
            self,
            query: str, model: str | None = None,
            typology: str | None = None,
            **kwargs
    ) -> str:
        rag_data = await retrieve(query, **kwargs)
        context = self.CTX.get(typology, 'ennea')
        prompt = self._build_prompt(rag_data, context)

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]

        return await self.client.async_response(messages=messages, model=model)