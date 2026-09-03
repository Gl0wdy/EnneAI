from datetime import datetime, date, timezone
from typing import  Literal

from beanie import Document
from pydantic import BaseModel, Field


SYSTEMS = Literal["ennea", "socio", "psychosophy", "jungian", "auto"]

class UserSettings(BaseModel):
    mode: Literal['naranjo', 'jung'] = "naranjo"
    reasoning: Literal['low', 'medium', 'high'] = "medium"
    system: SYSTEMS = "ennea"
    instructions: str = ""
    requery: bool = True


class UserMessage(Document):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int
    user_query: str
    response: str
    rag_context: str
    system: SYSTEMS

    class Settings:
        name = "user_messages"


class User(Document):
    id: int     # telegram id actually
    new: bool = True  
    username: str
    settings: UserSettings = Field(default_factory=UserSettings)
    typologies: str = ''
    request_limit: int = 15
    request_remain: int = 15
    burmaldate: date = datetime.now(timezone.utc).date()
    encrypted_key: str = ""

    class Settings:
        name = "users"


class AdminStatsSnapshot(Document):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    users_count: int
    active_users: int
    messages_count: int
    requests_left: int

    class Settings:
        name = "admin_stats_snapshots"