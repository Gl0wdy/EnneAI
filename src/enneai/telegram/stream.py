import asyncio
import random
import re
import time

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InputRichMessage


class TelegramStream:
    THINKING_MESSAGES = [
        "🧠 Думаю...",
        "🔎 Анализирую...",
        "📚 Изучаю вопрос...",
        "💭 Разбираюсь..."
    ]

    def __init__(
        self,
        bot: Bot,
        chat_id: int,
    ):
        self.bot = bot
        self.chat_id = chat_id
        self.draft_id = int(time.time() * 1000)

    async def _send_draft(self, rich_message: InputRichMessage) -> None:
        try:
            await self.bot.send_rich_message_draft(
                chat_id=self.chat_id,
                draft_id=self.draft_id,
                rich_message=rich_message,
            )
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)

    async def show_thinking(self) -> None:
        text = random.choice(self.THINKING_MESSAGES)

        await self._send_draft(
            InputRichMessage(
                markdown=text,
            )
        )

    async def update_draft(self, text: str) -> None:
        if not text.strip():
            return

        await self._send_draft(
            InputRichMessage(
                markdown=text,
            )
        )

    async def stream(self, chunks):
        text = ""

        last_update = 0.0
        last_length = 0

        update_interval = 0.8
        min_chars = 50

        await self.show_thinking()

        async for chunk in chunks:
            if not chunk:
                continue

            text += chunk
            if not self.has_visible_content(text):
                continue

            now = time.monotonic()

            if (
                now - last_update < update_interval
                and len(text) - last_length < min_chars
            ):
                continue

            await self.update_draft(text)

            last_update = now
            last_length = len(text)

        if not text.strip():
            return ""

        await self.bot.send_rich_message(
            chat_id=self.chat_id,
            rich_message=InputRichMessage(
                markdown=text,
            ),
        )

        return text

    def has_visible_content(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        stripped = re.sub(r'[#*_`~>\-\s]', '', text)

        return bool(stripped)