import aiohttp
import pytest_asyncio
from functional.config import settings


@pytest_asyncio.fixture(scope="session")
async def api_session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
def api_request(api_session):
    async def inner(path, params={}):  # noqa
        base_url = str(settings.fast_api.host).removesuffix("/")
        url = f"{base_url}{path}"
        async with api_session.get(url, params=params) as response:
            status = response.status
            data = await response.json() if response.ok else None
        return status, data

    return inner
