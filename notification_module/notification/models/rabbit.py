from pydantic import BaseModel
from enum import Enum
from uuid import UUID


class WorkerType(str, Enum):  # noqa
    email = 'email'
    web_socket = 'web_socket'


class Message(BaseModel):
    request_id: str
    user_id: UUID
    pattern_id: UUID
    data: dict
    worker: WorkerType
    urgently: bool


class GroupMessage(BaseModel):
    request_id: str
    role_id: UUID
    pattern_id: UUID
    data: dict
    worker: WorkerType
    urgently: bool
