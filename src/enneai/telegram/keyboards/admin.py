from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_admin_keyboard() -> InlineKeyboardMarkup:
	builder = InlineKeyboardBuilder()
	builder.button(text='Статистика', callback_data='admin:stats')
	builder.button(text='Пользователи', callback_data='admin:users')
	builder.button(text='Инфографика', callback_data='admin:infographic')
	builder.button(text='Рассылка', callback_data='admin:broadcast')
	builder.button(text='Обновить', callback_data='admin:refresh')
	builder.adjust(2, 2, 1)
	return builder.as_markup()


def build_admin_back_keyboard() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text='Назад', callback_data='admin:back')]
		]
	)
