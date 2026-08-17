from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

from enneai.db import User
from enneai.ai.modules.naranjo.response import Naranjo

from ..stream import TelegramStream
from enneai.config import OPENROUTER_API_KEY


router = Router(name='user')
naranjo = Naranjo(model='poolside/laguna-s-2.1:free', api_key=OPENROUTER_API_KEY)


@router.message(CommandStart())
async def start_handler(msg: Message, user: User):
    await msg.answer('Мне лень писать стартовый текст...')


@router.message()
async def test_handler(msg: Message, user: User):
    chunks = await naranjo.response(
        query=msg.text, typology='ennea', stream=True
    )

    telegram_stream = TelegramStream(
        msg.bot, msg.chat.id
    )

    await telegram_stream.stream(chunks)