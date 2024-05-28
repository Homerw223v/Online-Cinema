from motor.motor_asyncio import AsyncIOMotorClient

db: AsyncIOMotorClient


async def get_db_client() -> AsyncIOMotorClient:
    return db  # noqa
