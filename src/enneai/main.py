from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
import asyncio

from enneai.telegram import router
from enneai.config import TELEGRAM_BOT_TOKEN, TELEGRAM_DEBUG_TOKEN, TELEGRAM_ADMIN_ID

bot = Bot(
        token=TELEGRAM_DEBUG_TOKEN,
        default=DefaultBotProperties(
            parse_mode='Markdown',
            link_preview_is_disabled=True
        )
    )
dp = Dispatcher()

@dp.startup()
async def startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.send_message(TELEGRAM_ADMIN_ID, '✅ Бот запущен')

@dp.shutdown()
async def shutdown():
    await bot.send_message(TELEGRAM_ADMIN_ID, '❌ Бот остановлен')

async def main():
    # dp.include_router(admin_router)
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())