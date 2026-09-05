import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message, FSInputFile

from enneai.config import TELEGRAM_ADMIN_ID
from enneai.db.repositories import (
	AdminStatsSnapshotRepository,
	UserMessageRepository,
	UserRepository,
)
from enneai.telegram.keyboards import admin as admin_kb
from enneai.utils.infographic import build_infographic
import enneai.telegram.fsm as fsm


admin_router = Router(name='admin')
user_rep = UserRepository()
message_rep = UserMessageRepository()
snapshot_rep = AdminStatsSnapshotRepository()


def is_admin(user_id: int) -> bool:
	return user_id == TELEGRAM_ADMIN_ID


async def build_admin_overview() -> str:
	users = await user_rep.get_all()
	messages = await message_rep.get_all()
	active_users = sum(not user.new for user in users)
	requests_left = sum(user.request_remain for user in users)
	await snapshot_rep.create(
		users_count=len(users),
		active_users=active_users,
		messages_count=len(messages),
		requests_left=requests_left,
	)

	return (
		'*Панель администратора*\n\n'
		f'Пользователей: *{len(users)}*\n'
		f'Заполнили профиль: *{active_users}*\n'
		f'Запросов обработано: *{len(messages)}*\n'
		f'Осталось запросов: *{requests_left}*'
	)


async def build_users_report() -> str:
	users = await user_rep.get_all()
	if not users:
		return '*Пользователи*\n\nПока нет зарегистрированных пользователей.'

	lines = ['*Пользователи*', '']
	for user in users[:50]:
		username = user.username or 'без имени'
		profile = 'готов' if not user.new else 'новый'
		lines.append(
			f'• `{user.tg_id}` {username} | {profile} | '
			f'{user.request_remain}/{user.request_limit}'
		)

	if len(users) > 50:
		lines.append(f'\nПоказаны первые 50 из {len(users)}.')
	return '\n'.join(lines)


@admin_router.message(Command('admin'))
async def admin_handler(message: Message):
	if message.from_user is None or not is_admin(message.from_user.id):
		return

	await message.answer(
		await build_admin_overview(),
		reply_markup=admin_kb.main_keyboard,
	)


@admin_router.message(fsm.CommandStates.waiting_for_newsletter)
async def send_newsletter(message: Message, state: FSMContext):
	users = await user_rep.get_all()
	tasks = (message.copy_to(u.tg_id) for u in users)
	result = await asyncio.gather(*tasks, return_exceptions=True)

	succesful_count = len((r for r in result if not isinstance(r, Exception)))
	await message.answer(f'Успешно разослано {succesful_count} пользователям.')
	await state.clear()


@admin_router.callback_query(F.data.startswith('admin:'))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
	if callback.from_user is None or not is_admin(callback.from_user.id):
		await callback.answer('Доступ запрещён', show_alert=True)
		return

	if callback.data is None or not isinstance(callback.message, Message):
		await callback.answer()
		return

	action = callback.data.split(':', 1)[1]
	if action == 'back':
		await state.clear()
		action = 'stats'
	if action in ('back', 'refresh', 'stats'):
		await callback.message.edit_text(
			await build_admin_overview(),
			reply_markup=admin_kb.main_keyboard,
		)
	elif action == 'users':
		await callback.message.edit_text(
			await build_users_report(),
			reply_markup=admin_kb.back_keyboard,
		)
	elif action == 'newsletter':
		await callback.message.edit_text(
			'Пришлите сообщение, которое хотите разослать всем пользователям:',
			reply_markup=admin_kb.back_keyboard
		)
	elif action == 'infographic':
		users = await user_rep.get_all()
		messages = await message_rep.get_all()
		snapshots = await snapshot_rep.get_all()
		await bot.send_document(
			callback.from_user.id,
			BufferedInputFile(
				build_infographic(users, messages, snapshots),
				filename='enneai-infographic.svg',
			),
			caption='Инфографика по текущей статистике EnneAI',
		)
	elif action == 'broadcast':
		await state.set_state(fsm.AdminStates.waiting_for_broadcast)
		await callback.message.edit_text(
			'Введите текст рассылки одним сообщением. Для отмены отправьте /cancel.',
			reply_markup=admin_kb.back_keyboard,
		)
	elif action == 'logs':
		input_file = FSInputFile('logs/app.log', filename='app.log')
		await bot.send_document(callback.from_user.id, input_file, caption='Логи бота')

	await callback.answer()


@admin_router.message(StateFilter(fsm.AdminStates.waiting_for_broadcast))
async def broadcast_handler(message: Message, state: FSMContext, bot: Bot):
	if message.from_user is None or not is_admin(message.from_user.id):
		return
	if message.text is None or not message.text.strip():
		await message.answer('Нужен текст сообщения или /cancel для отмены.')
		return
	if message.text.strip().lower() == '/cancel':
		await state.clear()
		await message.answer('Рассылка отменена.', reply_markup=admin_kb.main_keyboard)
		return

	users = await user_rep.get_all()
	sent = 0
	failed = 0
	for user in users:
		try:
			await bot.send_message(user.tg_id, message.text, parse_mode=None)
			sent += 1
		except TelegramAPIError:
			failed += 1
		await asyncio.sleep(0.05)

	await state.clear()
	await message.answer(
		f'Рассылка завершена. Доставлено: {sent}. Недоступно: {failed}.',
		reply_markup=admin_kb.main_keyboard,
	)
