from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr
    password: str | None
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class ExtendedUser(User):
    roles: list[UUID]
    permissions: list[UUID]
    notice_email: bool = True
    notice_websocket: bool = True
    confirmed_email: bool = False


class UserAuthHistory(BaseModel):
    user_id: UUID
    ip_address: str
    user_agent: str
