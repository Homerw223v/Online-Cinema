from db.postgres import async_session
from services.repository import OauthProviderService  # noqa
from services.repository import (
    PermissionsService,
    RolesService,
    TokensService,
    UserAuthHistoryService,
    UsersAdminService,
    UsersService,
)


async def get_user_service():
    async with async_session() as session:
        yield UsersService(session)


async def get_user_admin_service():
    async with async_session() as session:
        yield UsersAdminService(session)


async def get_permission_service():
    async with async_session() as session:
        yield PermissionsService(session)


async def get_role_service():
    async with async_session() as session:
        yield RolesService(session)


async def get_token_service():
    async with async_session() as session:
        yield TokensService(session)


async def get_user_auth_history_service():
    async with async_session() as session:
        yield UserAuthHistoryService(session)


async def get_oauth_provider_service():
    async with async_session() as session:
        yield OauthProviderService(session)
