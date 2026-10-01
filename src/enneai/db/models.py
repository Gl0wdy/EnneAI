from datetime import datetime, date, timezone
from typing import  Literal

from beanie import Document, Link
from pydantic import BaseModel, Field


SYSTEMS = Literal["ennea", "socio", "psychosophy", "jungian", "auto"]

class UserSettings(BaseModel):
    mode: Literal['naranjo', 'jung'] = "naranjo"
    reasoning: Literal['low', 'medium', 'high'] = "medium"
    system: SYSTEMS = "ennea"
    instructions: str = ""
    requery: bool = True


from datetime import datetime, date, timezone
from beanie import Document, Link, BackLink, Indexed
from pydantic import Field


class User(Document):
    id: int  # telegram id
    new: bool = True
    username: str
    settings: UserSettings = Field(default_factory=UserSettings)
    typologies: str = ""
    request_limit: int = 15
    request_remain: int = 15
    burmaldate: date = Field(default_factory=lambda: datetime.now(timezone.utc).date())
    encrypted_key: str = ""

    messages: list[BackLink["UserMessage"]] = Field(
        default_factory=list, original_field="user"
    )

    class Settings:
        name = "users"

    def __str__(self):
        return f'ID: {self.id}\nUsername: {self.username}\nTypologies: {self.typologies}'


class UserMessage(Document):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: Link[User]
    user_query: str
    response: str
    rag_context: str
    system: SYSTEMS

    class Settings:
        name = "user_messages"


class Group(Document):
    id: int
    bot_aliases: list[str] = Field(default_factory=list)
    floodwait: int = 15     # seconds
    last_request: datetime = Field(default=lambda: datetime.now(timezone.utc))
    name: str


class GroupMessage(UserMessage):
    group: Link[Group]
    reply_message_id: int


class AdminStatsSnapshot(Document):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    users_count: int
    active_users: int
    messages_count: int
    requests_left: int

    class Settings:
        name = "admin_stats_snapshots"