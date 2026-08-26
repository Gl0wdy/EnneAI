from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# имхо билдеры избыточны если нет нужды в динамическом колбэке/тексте...
# def build_admin_keyboard() -> InlineKeyboardMarkup:
# 	builder = InlineKeyboardBuilder()
# 	builder.button(text='Статистика', callback_data='admin:stats')
# 	builder.button(text='Пользователи', callback_data='admin:users')
# 	builder.button(text='Рассылка', callback_data='admin:newsletter')
# 	builder.button(text='Обновить', callback_data='admin:refresh')
# 	builder.adjust(2, 1)
# 	return builder.as_markup()


main_keyboard = InlineKeyboardMarkup(
	inline_keyboard=[
		[
			InlineKeyboardButton(text='Статистика', callback_data='admin:stats'),
			InlineKeyboardButton(text='Пользователи', callback_data='admin:users')
		],
		[
			InlineKeyboardButton(text='Рассылка', callback_data='admin:newsletter'),
			InlineKeyboardButton(text='Обновить', callback_data='admin:refresh')
		]
	]
)

back_keyboard = InlineKeyboardMarkup(
	inline_keyboard=[
		[InlineKeyboardButton(text='Назад', callback_data='admin:back')]
	]
)