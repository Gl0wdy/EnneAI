from typing import Any, Awaitable, Callable

from enneai.db.repositories import UserRepository

from aiogram import BaseMiddleware
from aiogram.types import Message


user_rep = UserRepository()

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        user = await user_rep.get_by_telegram_id(user_id)
        if user is None:
            user = await user_rep.create(
                tg_id=user_id,
                username=event.from_user.username
            )

        data['user'] = user

        result = await handler(event, data)
        return result