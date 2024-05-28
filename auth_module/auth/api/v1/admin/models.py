from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from api.v1.models import Paginations


class IdModel(BaseModel):
    id: UUID


class Credentials(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    notice_email: bool
    notice_websocket: bool
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


class ExtendedUser(User):
    roles: list[UUID]
    permissions: list[UUID]
    confirmed_email: bool


class RetrieveUser(IdModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    notice_email: bool
    notice_websocket: bool
    confirmed_email: bool
    timezone_min: int


class Permission(BaseModel):
    name: str


class RetrievePermission(IdModel, Permission):
    pass  # noqa


class ExtendedPermission(Permission):
    users: list[UUID]
    roles: list[UUID]


class Role(BaseModel):
    name: str


class ExtendedRole(Role):
    users: list[UUID]
    permissions: list[UUID]


class RetrieveRole(IdModel, Role):
    pass  # noqa


class RetrieveExtendedUser(RetrieveUser):
    roles: list[RetrieveRole]
    permissions: list[RetrievePermission]


class RetrieveExtendedRole(RetrieveRole):
    users: list[RetrieveUser]
    permissions: list[RetrievePermission]


class RetrieveExtendedPermission(RetrievePermission):
    users: list[RetrieveUser]
    roles: list[RetrieveRole]


class RetrieveUserPaginator(Paginations):
    results: list[RetrieveUser]


class RetrieveRolePaginator(Paginations):
    results: list[RetrieveRole]


class RetrievePermissionsPaginator(Paginations):
    results: list[RetrievePermission]
