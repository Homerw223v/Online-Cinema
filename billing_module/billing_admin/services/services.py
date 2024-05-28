from db.postgres import async_session
from services.repositories import SubscriptionsService, UsersSubscriptionsService


async def get_users_subscriptions_service():
    async with async_session() as session:
        yield UsersSubscriptionsService(session)


async def get_subscriptions_service():
    async with async_session() as session:
        yield SubscriptionsService(session)
