from .abc import RepositoryABC
from ..models import UserMessage


class UserMessageRepository(RepositoryABC[UserMessage]):
    model = UserMessage

    async def clear_history(self, user_id: int) -> None:
        await self.model.find(
            self.model.user_id == user_id
        ).delete()