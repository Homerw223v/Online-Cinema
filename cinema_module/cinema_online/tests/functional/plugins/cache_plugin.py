import pytest_asyncio
from functional.config import settings
from functional.utils.interfaces.cache_interface import RedisCacheInterface
from redis import asyncio as redis


@pytest_asyncio.fixture(scope="session")
async def cache_client():
    client = redis.from_url(str(settings.redis.dsn), decode_responses=True)
    yield RedisCacheInterface(client)
    await client.close()
