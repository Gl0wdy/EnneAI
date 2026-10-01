from .abc import RepositoryABC
from ..models import UserMessage, GroupMessage


from beanie.operators import In


class TrimmedHistoryMixin:
    max_messages: int = 100

    def _owner_filter(self, instance):
        raise NotImplementedError

    async def create(self, **kwargs):
        instance = self.model(**kwargs)
        await instance.insert()
        await self._trim(self._owner_filter(instance))
        return instance

    async def _trim(self, owner_filter) -> None:
        query = self.model.find(owner_filter)
        excess = await query.count() - self.max_messages
        if excess <= 0:
            return

        oldest = await (
            self.model.find(owner_filter)
            .sort(+self.model.created_at)
            .limit(excess)
            .to_list()
        )
        await self.model.find(In(self.model.id, [m.id for m in oldest])).delete()


class UserMessageRepository(TrimmedHistoryMixin, RepositoryABC[UserMessage]):
    model = UserMessage

    def _owner_filter(self, instance: UserMessage):
        return self.model.user_id == instance.user_id

    async def clear_history(self, user_id: int) -> None:
        await self.model.find(self.model.user_id == user_id).delete()


class GroupMessageRepository(TrimmedHistoryMixin, RepositoryABC[GroupMessage]):
    model = GroupMessage

    def _owner_filter(self, instance: GroupMessage):
        return self.model.group.id == instance.group.ref.id

    async def clear_history(self, group_id: int) -> None:
        await self.model.find(self.model.group.id == group_id).delete()