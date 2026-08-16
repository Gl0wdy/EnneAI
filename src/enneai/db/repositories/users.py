from .abc import RepositoryABC
from ..models import User


class UserRepository(RepositoryABC[User]):
    model = User