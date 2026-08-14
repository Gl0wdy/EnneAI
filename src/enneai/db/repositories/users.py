from beanie import PydanticObjectId
from typing import Any

from enneai.db.models import User


class UserRepository:
    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
        )

        await user.insert()

        return user

    async def get_by_id(
        self,
        user_id: PydanticObjectId,
    ) -> User | None:
        return await User.get(user_id)

    async def delete(
        self,
        user: User,
    ) -> None:
        await user.delete()

    async def change_field(
        self,
        telegram_id: int,
        field: str,
        value: Any,
    ) -> None:
        await User.find_one(
            User.telegram_id == telegram_id
        ).update(
            {
                "$set": {
                    field: value,
                }
            }
        )