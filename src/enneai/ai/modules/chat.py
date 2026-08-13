import abc
from enneai.ai.llm import OpenRouterClient
from enneai.ai.rag import retrieve
from utils.reader import load_file

class ChatClient(abc.ABC): 
    def __init__(self, prompt: str, model: str, corr: str | None = 'None', api_key: str | None = None):
        self.CLIENT = OpenRouterClient(model=model, api_key=api_key)
        self.PROMPT = load_file(prompt)
        self.CORR = load_file(corr)
        self.CTX = {
            'ennea': load_file('data/ennea/context.txt'),
            'socio': load_file('data/socio/context.txt'),
            'psychosophy': load_file('data/psychosophy/context.txt')
    }

    def _build_prompt(self, rag_data: str, context: str):
        return self.PROMPT.replace('<RAG>', rag_data).replace('<CONTEXT>', context).replace('<CORR>', self.CORR)

    async def response(
            self,
            query: str, model: str | None = None,
            typology: str | None = None,
            **kwargs) -> str:
        
        # rag_data = await retrieve(query, **kwargs)
        context = self.CTX.get(typology, 'ennea')
        prompt = self._build_prompt(rag_data, context)

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]

        return await self.CLIENT.async_response(messages=messages, model=model)