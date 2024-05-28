from uuid import UUID
from enum import Enum
from pydantic import BaseModel, EmailStr
from beanie.odm.fields import PydanticObjectId


class WorkerType(str, Enum): # noqa!
    email = "email"
    web_socket = "web_socket"


class SingleMessage(BaseModel):
    request_id: str
    incoming_msg_id: UUID
    pattern_id: UUID
    user_id: UUID
    data: dict
    worker: WorkerType
    urgently: bool


class GroupMessage(BaseModel):
    request_id: str
    incoming_msg_id: UUID
    pattern_id: UUID
    group_id: UUID
    data: dict
    worker: WorkerType
    urgently: bool


class ProcessingMessage(BaseModel):
    request_id: str
    msg_id: PydanticObjectId
    user_id: UUID
    pattern_id: UUID
    urgently: bool


class IdModel(BaseModel):
    id: UUID


class Permission(IdModel):
    name: str


class Role(IdModel):
    name: str


class User(IdModel, BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    roles: list[Role]
    permissions: list[Permission]
    notice_email: bool
    notice_websocket: bool
    confirmed_email: bool
    timezone_min: int


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
