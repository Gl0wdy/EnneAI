from openai import AsyncOpenAI

from ai.vector_db import VectorDb
from ai.data import Data, GROUP_PROMPT

from utils.logger import logger
from config import API_KEY


class Chat:
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=API_KEY
        )
        self.vector_db = VectorDb()

    async def create(self,
                     request: str,
                     collection: str,
                     chat_history: list = [],
                     is_group: bool = False,
                     tags: str = ""):
        data_chunks = await self.vector_db.search(f"{tags}\n{request}", collection) or []
        data = Data(collection)
        messages = data.static + [
            {'role': 'system', 'content': f'БАЗА ЗНАНИЙ N.{n}:\n{chunk}'}
            for n, chunk in enumerate(data_chunks, 1) 
        ]  + data.prompt + (GROUP_PROMPT if is_group else []) + chat_history
        try:
            response = await self._client.chat.completions.create(
                messages=messages,
                model='gpt-4o',
                max_tokens=1000
            )
        except Exception as err:
                logger.error('Error in ai/completions.py', exc_info=err)
                return "Сервера OpenAI не отвечают. Попробуйте отправить запрос позже ещё раз."

        response_content = response.choices[0].message.content
        return response_content