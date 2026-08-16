from datetime import datetime
from typing import  Literal

from beanie import Document, Link
from pydantic import BaseModel


SYSTEMS = Literal["ennea", "socio", "psychosophy", "jungian"]

class UserSettings(BaseModel):
    mode: Literal['naranjo', 'jung'] = "naranjo"
    reasoning: Literal['low', 'medium', 'high'] = "medium"
    system: SYSTEMS
    prompt: str = ""
    rag: bool = True


class UserMessage(Document):
    created_at: datetime
    user_id: int
    user_query: str
    response: str
    rag_context: str
    system: SYSTEMS

    class Settings:
        name = "user_messages"


class User(Document):
    id: int     # telegram id actually
    username: str
    settings: UserSettings = UserSettings()
    typologies: str
    request_limit: int = 15
    request_remain: int = 15
    encrypted_key: str = ""

    class Settings:
        name = "users"