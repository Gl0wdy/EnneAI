from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_keyboard = InlineKeyboardMarkup(
	inline_keyboard=[
		[
			InlineKeyboardButton(text='Статистика', callback_data='admin:stats'),
			InlineKeyboardButton(text='Пользователи', callback_data='admin:users')
		],
		[
			InlineKeyboardButton(text='Рассылка', callback_data='admin:newsletter'),
			InlineKeyboardButton(text='Обновить', callback_data='admin:refresh')
		],
		[
			InlineKeyboardButton(text='Логи', callback_data='admin:logs')
		]
	]
)

back_keyboard = InlineKeyboardMarkup(
	inline_keyboard=[
		[InlineKeyboardButton(text='Назад', callback_data='admin:back')]
	]
)