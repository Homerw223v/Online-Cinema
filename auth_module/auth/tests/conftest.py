import pytest_asyncio
from httpx import AsyncClient
from redis import asyncio as redis_async

from core.config import AppSettings
from create_superuser import create_superuser as create_admin
from db import redis
from db.postgres import create_database, purge_database
from main import app
from tests.functional.test_data.helper_user import helper_user_credentials, helper_user_data
from tests.functional.test_data.superuser import superuser_credentials, superuser_model

app_settings = AppSettings()


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        app=app,
        base_url=f"{app_settings.app.host}",
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="session")
async def create_db():
    redis.redis_interface = redis_async.from_url(
        str(app_settings.redis.dsn),  # type: ignore
        encoding="utf8",
        decode_responses=True,
    )
    await create_database()
    yield
    await purge_database()
    await redis.redis_interface.close()


@pytest_asyncio.fixture(scope="session")
async def get_superuser_tokens(client, create_superuser):
    response = await client.post("login", data=superuser_credentials)
    return response.json()


@pytest_asyncio.fixture(scope="session")
async def auth_headers(get_superuser_tokens):
    return {
        "Authorization": f'Bearer {get_superuser_tokens["access_token"]}',
    }


@pytest_asyncio.fixture(scope="session")
async def create_superuser():
    await create_admin(**superuser_model)


@pytest_asyncio.fixture(scope="session")
async def create_helper_user(client):
    response = await client.post("/api/v1/users/", json=helper_user_data)
    return response.json()


@pytest_asyncio.fixture(scope="session")
async def helper_tokens(client, create_helper_user):
    response = await client.post("login", data=helper_user_credentials)
    return response.json()


@pytest_asyncio.fixture(scope="session")
async def helper_auth_headers(helper_tokens):
    return {
        "Authorization": f'Bearer {helper_tokens["access_token"]}',
    }


@pytest_asyncio.fixture(scope="session")
async def helper_uuid(client, create_helper_user):
    return create_helper_user["id"]
