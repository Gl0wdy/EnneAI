from g4f import AsyncClient

from ai.vector_db import VectorDb
from ai.utils import get_enneadata


AI_PROMT = '''
Ты - нейросеть "Клаудио Наранхо". Пока что ты разбираешься только в эннеаграмме, но в будущем
овладеешь и другими типологиями (такими как соционика, психософия и т.д).
Ты должен перепроверять себя и сверять ответ с БАЗОЙ ЗНАНИЙ (knowledge database) и краткой информацией (SHORT INFO).
Не нужно лишний раз шутить, если тебя об этом не просят. Прежде всего ты профессианальный типолог,
который определяет тип личности по эннеаграмме как своих собеседников, так и выдуманных персонажей.
Запомни следующее: 
1. сх перед типом (например, сх5) = сексуальная Е5
    со - социальная
    сп - самосохраняющаяся (консервативная)
    примеры: со7, со4, сх9, сп1 и так далее.
2. Ты используешь данные из базы знаний. Иногда цитируй ее, оговаривая, что взял информацию из книги,
    чтобы подтвердить значимость своих слов.
'''
enneadata = get_enneadata()


class Chat:
    '''
    Класс для представления чата с пользователем.
    Соединяется с векторной БД.
    '''

    def __init__(self):
        self._client = AsyncClient()
        self.vector_db = VectorDb()

    async def create(self, request: str, collections: list | str, chat_history: list = []) -> str:
        if isinstance(collections, str):
            data_chunks = await self.vector_db.search(request, collections)
        else:
            # @TODO
            data_chunks = []

        messages = [
            {'role': 'system', 'content': f'KNOWLEDGE DATABASE N.{n}:\n{chunk}'}
            for n, chunk in enumerate(data_chunks, 1) 
        ] + enneadata + [
            {'role': 'system', 'content': AI_PROMT}
        ] + chat_history

        response = await self._client.chat.completions.create(
            messages=messages,
            model='gpt-4o'
        )
        return response.choices[0].message.content
        
    # @TODO
    async def deep_create(self, request: str, collections: list | str, depth: int = 2):
        pass