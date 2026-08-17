from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

from enneai.db import User
from enneai.ai.modules.naranjo.response import Naranjo
from enneai.ai.modules.jung.response import Jung


from ..stream import TelegramStream
from enneai.config import OPENROUTER_API_KEY

from enneai.ai.llm.keys_rotation import KeyRotator


router = Router(name='user')
vertolet = KeyRotator([map(str, OPENROUTER_API_KEY.split(','))]) # в .env передаём ключи через запятую

# naranjo = Naranjo(model='poolside/laguna-s-2.1:free', api_key=OPENROUTER_API_KEY)
# jung = Jung(model='nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free', api_key=OPENROUTER_API_KEY)

async def processor(msg: Message, user: User, api_key: str): # начинка для хэндлера чтобы крутить ключи на вертолете
    '''вот тут всю логику пиши иначе кирдык'''
    naranjo = Naranjo(model='poolside/laguna-s-2.1:free', api_key=api_key) # каждый раз реинициализация клиента по приказу вертолета
    chunks = await naranjo.response(
            query=msg.text, typology='ennea', stream=True
        )
    
    telegram_stream = TelegramStream(
            msg.bot, msg.chat.id
        )
    
    await telegram_stream.stream(chunks)

@router.message(CommandStart())
async def start_handler(msg: Message, user: User):
    await msg.answer('бурмалда')

@router.message()
async def handler(msg: Message, user: User): 
    await vertolet.rotate(processor, msg, user) # ключи вертолет во внутренней логике класса передает сам

# i have no mouth and i must scream