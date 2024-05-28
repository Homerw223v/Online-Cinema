from uuid import UUID
from enum import Enum
from pydantic import Field
from datetime import datetime
from beanie import Document


class WorkerType(str, Enum): # noqa!
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
