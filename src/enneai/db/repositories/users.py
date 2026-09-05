from .abc import RepositoryABC
from ..models import User


class UserRepository(RepositoryABC[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.model.find_one(self.model.tg_id == telegram_id)