from pydantic import BaseModel
from enum import Enum
from uuid import UUID


class HttpException(BaseModel):
    detail: str


class WorkerType(str, Enum):  # noqa
    email = 'email'
    web_socket = 'web_socket'


class Message(BaseModel):
    user_id: UUID
    pattern_id: UUID
    data: dict
    worker: WorkerType
