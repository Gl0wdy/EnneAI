from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

import bot.database as db
import bot.keyboards as kb
from bot.fsm import ConfirmationState
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
    

@base_router.message(Command(commands='clear'))
async def clear_history(message: Message, state: FSMContext):
    await state.set_state(ConfirmationState.confirm)
    await message.answer('Вы уверены, что хотите стереть историю чата? Это нельзя отменить.',
                         reply_markup=kb.confirm_markup)
    

@base_router.message(ConfirmationState.confirm)
async def confirmation_process(message: Message, state: FSMContext):
    if message.text == 'Да':
        await db.clear_history(message.from_user.id)
        await message.answer('🗑 История чата успешно удалена. Теперь Наранхо ничего не помнит.',
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    elif message.text == 'Нет':
        await message.answer('История чата не была очищена. Можете продолжать диалог.',
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        await message.answer('Пожалуйста, выберите действие.')
    

@base_router.message(lambda x: bool(x.text) | bool(x.caption))
async def message_handler(message: Message):
    text = message.caption if message.caption else message.text
    user_id = message.from_user.id
    is_busy = await db.get_busy_state(user_id)
    if is_busy:
        await message.answer('Дождитесь завершения предыдущего запроса.')
        return
    await db.set_busy_state(user_id, True)
    await db.save_message(user_id, 'user', text)
    chat_history = await db.get_history(user_id)

    waiting_msg = await message.answer('⏳')
    await message.bot.send_chat_action(user_id, ChatAction.TYPING)

    response = await chat.create(
        request=text,
        collections='naranjo',
        chat_history=chat_history
    )
    await waiting_msg.delete()
    await db.save_message(user_id, 'system', response)
    await message.reply(response, parse_mode='Markdown')
    await db.set_busy_state(user_id, False)