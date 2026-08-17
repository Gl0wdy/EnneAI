# from .handlers.admin import admin_router
from .handlers.user import router
from .middlewares import UserMiddleware

__all__ = ['router', 'UserMiddleware']