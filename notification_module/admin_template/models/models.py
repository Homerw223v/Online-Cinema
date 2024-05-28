import uuid
from datetime import datetime
from functools import cached_property

from beanie import Document
from pydantic import BaseModel, Field, EmailStr, computed_field, ConfigDict


class IdModel(BaseModel):
    id: uuid.UUID


class CRUDPatternModel(BaseModel):
    subject: str
    content: str
    aggregate: bool = False


class PatterIdModel(BaseModel):
    pattern_id: uuid.UUID


class PatternListModel(PatterIdModel, CRUDPatternModel):
    ...  # noqa


class MongoPatternModel(Document, PatterIdModel, CRUDPatternModel):
    created_at: datetime
    updated_at: datetime


class Permission(IdModel):
    name: str


class Role(IdModel):
    name: str


class User(IdModel, BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class TokenInfo(BaseModel):
    user: str = Field(validation_alias="sub")
    roles_list: str = Field(validation_alias="roles", exclude=True)
    permissions_list: str = Field(validation_alias="permissions", exclude=True)
    jti: str

    @computed_field
    @cached_property
    def roles(self) -> set[str]:
        return set(filter(None, self.roles_list.split(",")))

    @computed_field
    @cached_property
    def permissions(self) -> set[str]:
        return set(filter(None, self.permissions_list.split(",")))

    model_config = ConfigDict(arbitrary_types_allowed=True)
