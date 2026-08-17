import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from enneai.telegram import router, UserMiddleware
from enneai.config import (
    TELEGRAM_DEBUG_TOKEN,
    TELEGRAM_ADMIN_ID,
    MONGO_URI,
)

from enneai.db import MongoDB


bot = Bot(
    token=TELEGRAM_DEBUG_TOKEN,
    default=DefaultBotProperties(
        parse_mode="Markdown",
        link_preview_is_disabled=True,
    ),
)

dp = Dispatcher()

mongo = MongoDB(
    uri=MONGO_URI,
    database="enneai",
)


@dp.startup()
async def startup():
    await mongo.init()

    await bot.delete_webhook(
        drop_pending_updates=True,
    )

    await bot.send_message(
        TELEGRAM_ADMIN_ID,
        "✅ Бот запущен",
    )


@dp.shutdown()
async def shutdown():
    await bot.send_message(
        TELEGRAM_ADMIN_ID,
        "❌ Бот остановлен",
    )

    await mongo.close()


async def main():
    dp.include_router(router)

    dp.message.middleware(
        UserMiddleware()
    )

    await dp.start_polling(
        bot,
        skip_updates=True,
    )


if __name__ == "__main__":
    asyncio.run(main())