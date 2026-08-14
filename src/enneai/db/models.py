from datetime import datetime, timezone
from typing import Annotated, Literal

from beanie import Document, Indexed, Link
from pydantic import BaseModel


class TypologySystem(Document):
    id: int
    name: str
    description: str
    author: str

    class Settings:
        name = "typology_systems"


class UserSettings(BaseModel):
    mode: Literal['naranjo', 'jung'] = "naranjo"
    reasoning: Literal['low', 'medium', 'high'] = "medium"
    system: Link[TypologySystem] = None
    prompt: str = ""
    rag: bool = True


class UserMessage(Document):
    id: int
    user_id: int
    request: str
    response: str
    rag_context: str
    system: Link[TypologySystem]

    class Settings:
        name = "user_messages"


class User(Document):
    id: int
    settings: UserSettings = UserSettings()
    typologies: str
    request_limit: int = 15
    request_remain: int = 15
    encrypted_key: str = ""

    class Settings:
        name = "users"