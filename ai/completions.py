from openai import AsyncOpenAI
from g4f import AsyncClient
from g4f.providers.any_provider import PollinationsAI

from ai.vector_db import VectorDb
from ai.data import Data, GROUP_PROMPT
from ai.utils import write_error

from utils.logger import logger
from config import API_KEY


class Chat:
    '''
    Класс для представления чата с пользователем.
    Соединяется с векторной БД.
    '''

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=API_KEY,
            base_url="https://api.aitunnel.ru/v1/"
        )
        self._free_client = AsyncClient()
        self.vector_db = VectorDb()

    async def create(self,
                     request: str,
                     collection: str,
                     chat_history: list = [],
                     is_group: bool = False,
                     premium: bool = False,
                     tags: str = ""):
        data_chunks = await self.vector_db.search(f"{tags}\n{request}", collection) or []
        data = Data(collection)
        messages = data.static + [
            {'role': 'system', 'content': f'БАЗА ЗНАНИЙ N.{n}:\n{chunk}'}
            for n, chunk in enumerate(data_chunks, 1) 
        ]  + data.prompt + (GROUP_PROMPT if is_group else []) + chat_history
        try:
            response = await self._free_client.chat.completions.create(
                messages=messages,
                provider=PollinationsAI,
                model='gpt-4o'
            )
        except Exception as err:
            if premium:
                response = await self._client.chat.completions.create(
                    messages=messages,
                    model='gpt-4o',
                    max_tokens=1000
                )
                write_error()
            else:
                self._free_client = AsyncClient()   # Reloading client
                logger.error('Error in ai/completions.py', exc_info=err)
                return "Сервера OpenAI не отвечают. Попробуйте отправить запрос позже ещё раз."

        response_content = response.choices[0].message.content
        return response_content