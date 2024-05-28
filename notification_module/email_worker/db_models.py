from datetime import datetime
from enum import Enum
from uuid import UUID

from beanie import Document
from pydantic import Field


class WorkerType(str, Enum):  # noqa!
    email = "email"
    web_socket = "web_socket"


class Message(Document):
    incoming_msg_id: UUID
    user_id: UUID
    pattern_id: UUID
    data: dict
    sent: bool = False
    created: datetime = Field(default_factory=datetime.now)
    worker: WorkerType
