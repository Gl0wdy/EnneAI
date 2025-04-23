from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import bot.keyboards as kb
import bot.database as db
from bot.config import ADMIN_ID
from bot.fsm import SendingState
import asyncio


admin_router = Router(name='router')


@admin_router.message(Command(commands=['admin']))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer('Админ-панель открыта.', reply_markup=kb.admin_markup)


@admin_router.message(lambda x: x.text == 'Рассылка')
async def sending(message: Message, context: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await context.set_state(SendingState.enter_content)
    await message.answer('Отправьте контент для рассылки:')


@admin_router.message(SendingState.enter_content)
async def enter_sending(message: Message, context: FSMContext):
    await context.clear()
    users = await db.get_all_users()
    tasks = (
        await message.copy_to(u['user_id']) for u in users
    )
    await asyncio.gather(*tasks)
    await message.answer(f'Успешно разослано всем пользователем ({len(users)})')