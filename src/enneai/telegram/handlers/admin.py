from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from enneai.config import TELEGRAM_ADMIN_ID
from enneai.db.repositories import UserMessageRepository, UserRepository
from enneai.telegram.keyboards import admin as admin_kb


admin_router = Router(name='admin')
user_rep = UserRepository()
message_rep = UserMessageRepository()


def is_admin(user_id: int) -> bool:
	return user_id == TELEGRAM_ADMIN_ID


async def build_admin_overview() -> str:
	users = await user_rep.get_all()
	messages = await message_rep.get_all()
	active_users = sum(not user.new for user in users)
	requests_left = sum(user.request_remain for user in users)

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
			f'• `{user.id}` {username} | {profile} | '
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
		reply_markup=admin_kb.build_admin_keyboard(),
	)


@admin_router.callback_query(F.data.startswith('admin:'))
async def admin_callback_handler(callback: CallbackQuery):
	if callback.from_user is None or not is_admin(callback.from_user.id):
		await callback.answer('Доступ запрещён', show_alert=True)
		return

	if callback.data is None or not isinstance(callback.message, Message):
		await callback.answer()
		return

	action = callback.data.split(':', 1)[1]
	if action in ('back', 'refresh', 'stats'):
		await callback.message.edit_text(
			await build_admin_overview(),
			reply_markup=admin_kb.build_admin_keyboard(),
		)
	elif action == 'users':
		await callback.message.edit_text(
			await build_users_report(),
			reply_markup=admin_kb.build_admin_back_keyboard(),
		)

	await callback.answer()
