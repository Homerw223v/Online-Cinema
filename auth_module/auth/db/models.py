from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey, MetaData, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    metadata = MetaData(schema="auth")
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)


class Users(Base):
    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    _password = Column(String(255), name="password")
    first_name = Column(String(50))
    last_name = Column(String(50))
    confirmed_email = Column(Boolean, nullable=False, default=False)
    notice_email = Column(Boolean, nullable=False, default=True)
    notice_websocket = Column(Boolean, nullable=False, default=True)
    timezone_min = Column(Integer, nullable=False, default=180)

    roles = relationship(
        "Roles",
        secondary="auth.users_roles",
        back_populates="users",
        cascade="all, delete",
    )
    permissions = relationship(
        "Permissions",
        secondary="auth.users_permissions",
        back_populates="users",
        cascade="all, delete",
    )
    tokens: Mapped[list[Tokens]] = relationship(
        back_populates="user",
        cascade="all, delete",
    )
    oauth_provider: Mapped[list[OauthProvider]] = relationship(
        back_populates="user",
        cascade="all, delete",
    )

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):  # noqa
        if password:
            self._password = generate_password_hash(password)  # noqa

    def check_password(self, password: str) -> bool:
        return check_password_hash(self._password, password)

    def __repr__(self) -> str:
        return f"<User {self.login}>"


class Roles(Base):
    __tablename__ = "roles"

    name = Column(String(255), unique=True, nullable=False)

    users = relationship(
        "Users",
        secondary="auth.users_roles",
        back_populates="roles",
        cascade="all, delete",
    )
    permissions = relationship(
        "Permissions",
        secondary="auth.roles_permissions",
        back_populates="roles",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permissions(Base):
    __tablename__ = "permissions"

    name = Column(String(255), unique=True, nullable=False)

    users = relationship(
        "Users",
        secondary="auth.users_permissions",
        back_populates="permissions",
        cascade="all, delete",
    )
    roles = relationship(
        "Roles",
        secondary="auth.roles_permissions",
        back_populates="permissions",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class UsersRoles(Base):
    __tablename__ = "users_roles"

    user_id = Column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    role_id = Column(ForeignKey("auth.roles.id", ondelete="CASCADE"))


class RolesPermissions(Base):
    __tablename__ = "roles_permissions"

    role_id = Column(ForeignKey("auth.roles.id", ondelete="CASCADE"))
    permission_id = Column(ForeignKey("auth.permissions.id", ondelete="CASCADE"))


class UsersPermissions(Base):
    __tablename__ = "users_permissions"

    user_id = Column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    permission_id = Column(ForeignKey("auth.permissions.id", ondelete="CASCADE"))


class UsersAuthHistory(Base):
    __tablename__ = "user_auth_history"
    user_id = Column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    ip_address = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=False)


class Tokens(Base):
    __tablename__ = "tokens"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    jti = Column(String(255), nullable=False)

    user: Mapped[Users | None] = relationship(back_populates="tokens")

    def __repr__(self) -> str:
        return f"<Token {self.user_id}>"


class OauthProvider(Base):
    __tablename__ = "oauth_provider"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    provider_name = Column(String(255), nullable=False)
    client_id = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))

    user: Mapped[Users] = relationship(back_populates="oauth_provider")

    def __repr__(self) -> str:
        return f"<OauthProvider {self.user_id} {self.provider_name}>"
