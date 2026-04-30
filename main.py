from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
import asyncio

from bot.handlers.base import base_router
from bot.handlers.admin import admin_router

from config import ADMIN_ID
from config import BOT_TOKEN, DEBUG_TOKEN


bot = Bot(
        token=DEBUG_TOKEN,
        default=DefaultBotProperties(
            parse_mode='Markdown',
            link_preview_is_disabled=True
        )
    )
dp = Dispatcher()

@dp.startup()
async def startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.send_message(ADMIN_ID, '✅ Бот запущен')

@dp.shutdown()
async def shutdown():
    await bot.send_message(ADMIN_ID, '❌ Бот остановлен')

async def main():
    dp.include_router(admin_router)
    dp.include_router(base_router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())