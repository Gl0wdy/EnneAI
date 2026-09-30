from .abc import RepositoryABC
from ..models import UserMessage, GroupMessage


class UserMessageRepository(RepositoryABC[UserMessage]):
    model = UserMessage

    async def clear_history(self, user_id: int) -> None:
        await self.model.find(
            self.model.user_id == user_id
        ).delete()

class GroupMessageRepository(RepositoryABC[GroupMessage]):
    model = GroupMessage

    async def clear_history(self, group_id: int) -> None:
            await self.model.find(
                self.model.group.id == group_id
            ).delete()