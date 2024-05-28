from datetime import datetime
from enum import Enum
from math import ceil
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.oauth_provider import OauthProviderFactory


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class HttpException(BaseModel):
    detail: str


class IdModel(BaseModel):
    id: UUID


class RetrieveRole(IdModel):
    name: str


class RetrievePermission(IdModel):
    name: str


class User(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    timezone_min: int

    @field_validator("password")
    def check_password(cls, password: str):  # noqa
        # check that the password has at least 8 characters, one uppercase letter, one lowercase letter, and one digit
        if len(password) < 8:
            raise ValueError("Password must have at least 8 characters")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must have at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must have at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must have at least one digit")
        return password


class RetrieveUser(IdModel, BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    roles: list[RetrieveRole]
    permissions: list[RetrievePermission]
    notice_email: bool
    notice_websocket: bool
    confirmed_email: bool
    timezone_min: int


class ReceivedUser(User):
    notice_email: bool
    notice_websocket: bool


class RetrieveUserAuthHistory(BaseModel):
    time: datetime = Field(validation_alias="created_at")
    ip_address: str
    user_agent: str


class PaginatedParams(BaseModel):
    page_size: int = Field(ge=1, default=20)
    page_number: int = Field(ge=1, default=1)


class Paginations(BaseModel):
    count: int
    total_pages: int
    next: int | None
    prev: int | None
    page: int
    results: Any

    @classmethod
    def calculate_pages(cls, results, item_count, paginated_params: PaginatedParams):
        page_size = paginated_params.page_size
        page_number = paginated_params.page_number
        total_page = ceil(item_count / page_size)
        return cls(
            count=item_count,
            total_pages=total_page,
            prev=page_number - 1 if page_number > 1 else None,
            next=page_number + 1 if page_number < total_page else None,
            page=page_number,
            results=results,
        )


class RetrieveUserAuthHistoryPaginator(Paginations):
    results: list[RetrieveUserAuthHistory]


class StrEnum(str, Enum):  # noqa
    pass  # noqa


OauthProviders = StrEnum(
    "OauthProviders",
    {key: key for key in OauthProviderFactory.providers},
)


class OauthState(BaseModel):
    provider_name: OauthProviders
    user_id: UUID | None = None
