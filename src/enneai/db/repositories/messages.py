from .abc import RepositoryABC
from ..models import UserMessage


class UserMessageRepository(RepositoryABC[UserMessage]):
    model = UserMessage