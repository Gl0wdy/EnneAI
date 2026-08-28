from .abc import RepositoryABC
from ..models import AdminStatsSnapshot


class AdminStatsSnapshotRepository(RepositoryABC[AdminStatsSnapshot]):
    model = AdminStatsSnapshot