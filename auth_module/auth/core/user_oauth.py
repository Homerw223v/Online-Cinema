from contextlib import suppress
from uuid import UUID, uuid4

from sqlalchemy.exc import NoResultFound

from db.models import Users
from db.postgres import async_session
from models.oauth_provider import OauthUserData
from models.users import User
from services.repository import OauthProviderService, UsersService


class EmptyProfileError(Exception): ...  # noqa


async def add_provider(oauth_user_info: OauthUserData):
    oauth_db_data = None
    async with async_session() as session:
        oauth_provider_service = OauthProviderService(session)
        user_service = UsersService(session)

        with suppress(NoResultFound):
            oauth_db_data = await oauth_provider_service.get_by_user(
                user_id=oauth_user_info.user_id,
                provider_name=oauth_user_info.provider_name,
            )
        if oauth_db_data:
            await oauth_provider_service.update(
                entity_id=oauth_db_data.id,
                entity=oauth_user_info,
            )
        else:
            await oauth_provider_service.create(oauth_user_info)
        return await user_service.get_by_id(oauth_user_info.user_id)


async def get_oauth_user(oauth_user_info: OauthUserData):
    async with async_session() as session:
        oauth_provider_service = OauthProviderService(session)
        user_service = UsersService(session)

        try:  # noqa
            db_oauth_user = await oauth_provider_service.get_by_provider_user(
                client_id=oauth_user_info.client_id,
                provider_name=oauth_user_info.provider_name,
            )
            oauth_user_info.user_id = db_oauth_user.user_id
        except NoResultFound:
            user_id = await create_empty_oauth_user(oauth_user_info)
            oauth_user_info.user_id = user_id
            await oauth_provider_service.create(oauth_user_info)

        return await user_service.get_by_id(oauth_user_info.user_id)


async def create_empty_oauth_user(oauth_user_info: OauthUserData) -> UUID:
    async with async_session() as session:
        user_service = UsersService(session)
        user = await user_service.create(create_fake_user(oauth_user_info))
        return user.id


async def del_provider(provider_name: str, user_id: UUID) -> None:
    async with async_session() as session:
        oauth_provider_service = OauthProviderService(session)
        user_service = UsersService(session)

        await oauth_provider_service.get_by_user(
            provider_name=provider_name,
            user_id=user_id,
        )  # check exist record
        providers = await oauth_provider_service.get_list(
            paginated_params=None,
            filters={"user_id": user_id, "provider_name": provider_name},
        )
        if len(providers) == 1:
            if is_fake_user(await user_service.get_by_id(user_id)):
                raise EmptyProfileError

        await oauth_provider_service.delete_by_provider(
            provider_name=provider_name,
            user=user_id,
        )


def create_fake_user(oauth_user_info: OauthUserData) -> User:
    return User(
        username=f"{uuid4()}-fake",
        email=f"{uuid4()}@fake.com",
        password=None,
        first_name=oauth_user_info.first_name,
        last_name=oauth_user_info.last_name,
    )


def is_fake_user(user: Users) -> bool:
    return user.password is None or user.email.split("@")[-1] == "fake.com" or user.username.split("-")[-1] == "fake"
