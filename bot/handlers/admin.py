from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

import bot.keyboards as kb
import bot.database as db
from bot.config import ADMIN_ID
from bot.fsm import SendingState


admin_router = Router(name='router')


@admin_router.message(Command(commands=['admin']))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer('Админ-панель открыта.', reply_markup=kb.admin_markup)


@admin_router.message(lambda x: x.text == 'Рассылка')
async def sending(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(SendingState.enter_content)
    await message.answer('Отправьте контент для рассылки:')


@admin_router.message(SendingState.enter_content)
async def enter_sending(message: Message, state: FSMContext):
    await state.clear()
    users = await db.get_all_users()
    c = 0
    async for i in users:
        try:
            await message.copy_to(i['user_id'])
            c += 1
        except:
            pass
    await message.answer(f'Успешно разослано всем пользователем ({c})')


@admin_router.message(lambda x: x.text == 'Логи')
async def sending(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        file = FSInputFile('app.log', 'app.log')
        await message.answer_document(file)
    except:
        await message.answer('Логовый файл пуст.')


@admin_router.message(lambda x: x.text == 'Юзеры')
async def sending(message: Message):
    users_cursor = await db.get_all_users()
    c = len([i async for i in users_cursor])
    await message.answer(f'Количество живых юзеров: {c}')