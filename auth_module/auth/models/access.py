from uuid import UUID

from pydantic import BaseModel


class Permission(BaseModel):
    name: str


class ExtendedPermission(Permission):
    users: list[UUID]
    roles: list[UUID]


class Role(BaseModel):
    name: str


class ExtendedRole(Role):
    users: list[UUID]
    permissions: list[UUID]
