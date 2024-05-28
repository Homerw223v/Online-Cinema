# type: ignore
import asyncio
from typing import Callable, Iterator

import pytest_asyncio
from httpx import AsyncClient
from pytest_asyncio.plugin import SimpleFixtureFunction
from settings import settings


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """
    Yield event loop for testing purpose in session scope.
    Close before session termination.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="httpx_session", scope="session")
async def httpx_session() -> AsyncClient:
    """
    Yield aiohttp client session in testing session scope.
    Close before session termination.
    """
    session = AsyncClient()
    yield session


@pytest_asyncio.fixture(name="post_aiohttp_response")
async def post_aiohttp_response(
    httpx_session: SimpleFixtureFunction,
) -> Callable:
    """
    Return inner function.

    :param httpx_session: Fixture of this module, which yields httpx client session.
    """

    async def inner(
        postfix: str,
        query_data: dict[str, int | str] | None = None,
    ) -> tuple[dict, int, dict]:
        """
        Return body, status, and headers of https request with postfix endpoint and query_data.

        :param postfix: Endpoint of API.
        :param query_data: Parameters of API request.
        """
        url = settings.test_base_url + postfix
        response = await httpx_session.post(
            url,
            json=query_data,
            headers={"X-Request-Id": "1"},
        )
        body = response.json()
        status = response.status_code
        headers = response.headers
        return body, status, headers

    return inner
