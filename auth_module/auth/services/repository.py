from abc import ABC
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

import backoff
from pydantic import BaseModel
from sqlalchemy import delete, func, literal_column, or_, select, update
from sqlalchemy.exc import IntegrityError, InterfaceError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.v1.models import PaginatedParams
from db.models import Base, OauthProvider, Permissions, Roles, Tokens, Users, UsersAuthHistory
from models.access import ExtendedPermission, ExtendedRole
from models.tokens import Token
from models.users import ExtendedUser, User, UserAuthHistory
from services.exceptions import AlreadyExistException

DBModel = TypeVar("DBModel", bound=Base)
Schema = TypeVar("Schema", bound=BaseModel)
ExtendedSchema = TypeVar("ExtendedSchema", bound=BaseModel)
RetrieveSchema = TypeVar("RetrieveSchema", bound=BaseModel)
RetrieveExtendedSchema = TypeVar("RetrieveExtendedSchema", bound=BaseModel)


class DatabaseConnectionError(Exception):
    pass  # noqa


def give_up(func):
    raise DatabaseConnectionError()


def backoff_decorator(backoff_interval=0.5, backoff_max_time_sec=2):
    def decorate(func):  # noqa
        @backoff.on_exception(
            backoff.constant,
            exception=(InterfaceError, PendingRollbackError, ConnectionRefusedError),
            jitter=backoff.random_jitter,
            interval=backoff_interval,
            max_time=backoff_max_time_sec,
            on_giveup=give_up,
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorate


class BaseService(Generic[DBModel, ExtendedSchema], ABC):
    _model = DBModel

    def __init__(self, session: AsyncSession):
        self.session = session

    @backoff_decorator()
    async def get_list(
        self,
        paginated_params: PaginatedParams | None,
        filters: dict,
    ) -> list[_model]:
        limit = paginated_params.page_size if paginated_params else None
        offset = (paginated_params.page_number - 1) * paginated_params.page_size if paginated_params else None
        stmt = select(self._model).filter_by(**filters).limit(limit).offset(offset)
        results = await self.session.execute(stmt)
        return list(results.scalars())

    @backoff_decorator()
    async def count(self, filters: dict) -> int:
        stmt = select(func.count(self._model.id)).filter_by(**filters)
        return await self.session.scalar(stmt)

    @backoff_decorator()
    async def get_by_id(self, entity_id: UUID) -> _model:
        return await self.session.get_one(self._model, entity_id)

    @backoff_decorator()
    async def create(self, entity: ExtendedSchema) -> _model:
        db_item = self._model(**entity.model_dump())
        self.session.add(db_item)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return db_item

    @backoff_decorator()
    async def update(self, entity_id: UUID, entity: ExtendedSchema) -> _model:
        stmt = (
            update(self._model)
            .where(
                self._model.id == entity_id,
            )
            .values(**entity.model_dump())
            .returning(literal_column("*"))
        )
        obj = (await self.session.execute(stmt)).one()
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj

    @backoff_decorator()
    async def delete(self, entity_id: UUID) -> None:
        stmt = delete(self._model).where(self._model.id == entity_id)
        await self.session.execute(stmt)
        await self.session.commit()


class TokensService(BaseService[Tokens, Token]):
    _model = Tokens

    @backoff_decorator()
    async def get_by_jti(self, jti: UUID) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.jti == jti)
            .options(
                selectinload(self._model.user).subqueryload(Users.roles),
                selectinload(self._model.user).subqueryload(Users.permissions),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def delete_by_jti(self, jti: UUID) -> None:
        stmt = delete(self._model).where(self._model.jti == jti)
        await self.session.execute(stmt)
        await self.session.commit()

    @backoff_decorator()
    async def delete_user_expire_tokens(
        self,
        entity_id: UUID,
        before_created: datetime,
    ) -> None:
        stmt = delete(self._model).where(
            self._model.id == entity_id,
            self._model.created_at < before_created,
        )
        await self.session.execute(stmt)
        await self.session.commit()


class UsersService(BaseService[Users, User]):
    _model = Users

    @backoff_decorator()
    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.roles),
                selectinload(self._model.permissions),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def check_credentials(self, login: str, password: str) -> bool:
        stmt = select(self._model).where(
            or_(self._model.username == login, self._model.email == login),
        )
        user = (await self.session.scalars(stmt)).one()
        return user.check_password(password)

    @backoff_decorator()
    async def create(self, entity: ExtendedSchema) -> _model:
        db_item = self._model(**entity.model_dump())
        self.session.add(db_item)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return await self.get_by_id(db_item.id)

    @backoff_decorator()
    async def update(self, entity_id: UUID, entity: ExtendedSchema, confirmed_email: bool) -> _model:
        stmt = (
            update(self._model)
            .where(
                self._model.id == entity_id,
            )
            .values(**entity.model_dump(), confirmed_email=confirmed_email)
        )
        await self.session.execute(stmt)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return await self.get_by_id(entity_id)


class RolesService(BaseService[Roles, ExtendedRole]):
    _model = Roles

    def __init__(self, session: AsyncSession):
        self.session = session

    @backoff_decorator()
    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.users),
                selectinload(self._model.permissions),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def create(self, entity: ExtendedRole) -> _model:
        obj = self._model(name=entity.name)
        stmt = select(Users).filter(Users.id.in_(entity.users))
        obj.users = list(await self.session.scalars(stmt))
        stmt = select(Permissions).filter(Permissions.id.in_(entity.permissions))
        obj.permissions = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj

    @backoff_decorator()
    async def update(self, entity_id: UUID, entity: ExtendedRole) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.users),
                selectinload(self._model.permissions),
            )
        )
        obj = await self.session.scalar(stmt)
        obj.name = entity.name
        stmt = select(Users).filter(Users.id.in_(entity.users))
        obj.users = list(await self.session.scalars(stmt))
        stmt = select(Permissions).filter(Permissions.id.in_(entity.permissions))
        obj.permissions = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj


class PermissionsService(BaseService[Permissions, ExtendedPermission]):
    _model = Permissions

    def __init__(self, session: AsyncSession):
        self.session = session

    @backoff_decorator()
    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.users),
                selectinload(self._model.roles),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def create(self, entity: ExtendedPermission) -> _model:
        obj = self._model(name=entity.name)
        stmt = select(Users).filter(Users.id.in_(entity.users))
        obj.users = list(await self.session.scalars(stmt))
        stmt = select(Roles).filter(Roles.id.in_(entity.roles))
        obj.roles = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj

    @backoff_decorator()
    async def update(self, entity_id: UUID, entity: ExtendedPermission) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.users),
                selectinload(self._model.roles),
            )
        )
        obj = await self.session.scalar(stmt)
        obj.name = entity.name
        stmt = select(Users).filter(Users.id.in_(entity.users))
        obj.users = list(await self.session.scalars(stmt))
        stmt = select(Roles).filter(Roles.id.in_(entity.roles))
        obj.roles = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj


class UsersAdminService(BaseService[Users, ExtendedUser]):
    _model = Users

    def __init__(self, session: AsyncSession):
        self.session = session

    @backoff_decorator()
    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .where(self._model.id == entity_id)
            .options(
                selectinload(self._model.roles),
                selectinload(self._model.permissions),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def get_by_login(self, login: str) -> _model:
        stmt = (
            select(self._model)
            .where(or_(self._model.username == login, self._model.email == login))
            .options(
                selectinload(self._model.roles),
                selectinload(self._model.permissions),
            )
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def create(self, entity: ExtendedUser) -> _model:
        obj = self._model(
            username=entity.username,
            email=entity.email,
            password=entity.password,
            first_name=entity.first_name,
            last_name=entity.last_name,
        )
        stmt = select(Roles).filter(Roles.id.in_(entity.roles))
        obj.roles = list(await self.session.scalars(stmt))
        stmt = select(Permissions).filter(Permissions.id.in_(entity.permissions))
        obj.permissions = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj

    @backoff_decorator()
    async def update(self, entity_id: UUID, entity: ExtendedUser) -> _model:
        obj = await self.get_by_id(entity_id)
        obj.username = entity.username
        obj.email = entity.email
        obj.password = entity.password
        obj.first_name = entity.first_name
        obj.last_name = entity.last_name
        obj.confirmed_email = entity.confirmed_email
        obj.notice_email = entity.notice_email
        obj.notice_websocket = entity.notice_websocket
        stmt = select(Permissions).filter(Permissions.id.in_(entity.permissions))
        obj.permissions = list(await self.session.scalars(stmt))
        stmt = select(Roles).filter(Roles.id.in_(entity.roles))
        obj.roles = list(await self.session.scalars(stmt))
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj


class UserAuthHistoryService(BaseService[UsersAuthHistory, UserAuthHistory]):
    _model = UsersAuthHistory


class OauthProviderService(BaseService[OauthProvider, OauthProvider]):
    _model = OauthProvider

    @backoff_decorator()
    async def get_by_user(self, user_id: UUID, provider_name: str) -> _model:
        stmt = (
            select(self._model)
            .where(
                self._model.user_id == user_id,
                self._model.provider_name == provider_name,
            )
            .options(selectinload(self._model.user))
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def get_by_provider_user(self, client_id: UUID, provider_name: str) -> _model:
        stmt = (
            select(self._model)
            .where(
                self._model.client_id == client_id,
                self._model.provider_name == provider_name,
            )
            .options(selectinload(self._model.user))
        )
        return (await self.session.scalars(stmt)).one()

    @backoff_decorator()
    async def delete_by_provider(self, user: UUID, provider_name: str) -> None:
        stmt = delete(self._model).where(
            self._model.user_id == user,
            self._model.provider_name == provider_name,
        )
        await self.session.execute(stmt)
        await self.session.commit()
