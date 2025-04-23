from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ChatAction

import bot.database as db
from ai.completions import Chat


base_router = Router(name='main')
chat = Chat()


@base_router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        text='Привет, я - Клаудио Наранхо, чилийский психиатр, доктор медицины, гештальт-терапевт, и я готов помочь с вопросами по эннеаграмме и твоему типу.\n\nP.S пиши названия сабтипов полностью, чтобы результат был более корректным (вместо "со7" лучше писать "социальная е7", например)'
    )
    await message.answer('Также рекомендую подписаться на [новостной канал](https://t.me/typologyAIchannel), чтобы не пропускать новую информацию о боте.',
                         parse_mode='markdown')
    

@base_router.message(lambda x: bool(x.text) | bool(x.caption))
async def message_handler(message: Message):
    user_id = message.from_user.id
    is_busy = await db.get_busy_state(user_id)
    if is_busy:
        await message.delete()
        return
    await db.set_busy_state(user_id, True)
    await db.save_message(user_id, 'user', message.text)
    chat_history = await db.get_history(user_id)

    waiting_msg = await message.answer('⏳')
    await message.bot.send_chat_action(user_id, ChatAction.TYPING)

    response = await chat.create(
        request=message.text,
        collections='naranjo',
        chat_history=chat_history
    )
    await waiting_msg.delete()
    await db.save_message(user_id, 'system', response)
    await message.answer(response, parse_mode='Markdown')
    await db.set_busy_state(user_id, False)