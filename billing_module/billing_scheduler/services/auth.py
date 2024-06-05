from __future__ import annotations
from typing import Any
from asyncio import Lock
import aiohttp

from models.token import Tokens
from http import HTTPStatus
from pydantic import HttpUrl
from time import time


auth_interface: AuthService


async def get_auth_client() -> AuthService:
    return auth_interface  # noqa


class AuthorizationError(Exception):
    pass  # noqa!


class AuthService:
    def __init__(
        self,
        username: str,
        password: str,
        login_url: HttpUrl,
        refresh_url: HttpUrl,
        **kwargs: Any,
    ):
        self.login_url = str(login_url)
        self.refresh_url = str(refresh_url)
        self.username = username
        self.password = password
        self.session: aiohttp.ClientSession
        self.refresh_token = None
        self.access_token = None
        self.access_exp = time()
        self.lock = Lock()

    async def __aenter__(self):
        return self.connections()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def connections(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        return self

    async def close(self):
        await self.session.close()

    async def get_query(self, url, request_id):
        async with self.session.get(url=url, headers=await self._get_headers(request_id)) as resp:
            if resp.ok:
                return await resp.json()
            elif resp.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.UNPROCESSABLE_ENTITY):
                await self.refresh_tokens(request_id)
                async with self.session.get(url=url, headers=await self._get_headers(request_id)) as resp:  # noqa!
                    if resp.ok:
                        return await resp.json()
            raise AuthorizationError(f"Error get user info. {await resp.text()}")

    async def post_query(self, url, request_id, data):
        async with self.session.post(url=url, headers=await self._get_headers(request_id), json=data) as resp:
            if resp.ok:
                return await resp.json()
            elif resp.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.UNPROCESSABLE_ENTITY):
                await self.refresh_tokens(request_id)
                async with self.session.post(url=url, headers=await self._get_headers(request_id), json=data) as resp:  # noqa!
                    if resp.ok:
                        return await resp.json()
            raise AuthorizationError(f"Error get user info. {await resp.text()}")

    async def get_tokens(self, request_id):
        params = {"username": self.username, "password": self.password}
        async with self.session.post(
            url=self.login_url,
            data=params,
            headers={"X-Request-Id": request_id},
        ) as resp:
            if resp.ok:
                tokens = Tokens.model_validate_json(await resp.text())
                self.access_token = tokens.access_token
                self.refresh_token = tokens.refresh_token
                self.access_exp = tokens.access_expire
            else:
                raise AuthorizationError(f"Error receiving token. {await resp.text()}")

    async def refresh_tokens(self, request_id):
        headers = {
            "Authorization": f"Bearer {self.refresh_token}",
            "X-Request-Id": request_id,
        }
        async with self.session.post(url=self.refresh_url, headers=headers) as resp:
            if resp.ok:
                tokens = Tokens.model_validate_json(await resp.text())
                self.access_token = tokens.access_token
                self.refresh_token = tokens.refresh_token
                self.access_exp = tokens.access_expire
            elif resp.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.UNPROCESSABLE_ENTITY):
                await self.get_tokens(request_id)
            else:
                raise AuthorizationError(f"Error refresh token. {await resp.text()}")

    async def _get_headers(self, request_id):
        if self.access_token is None:
            await self.get_tokens(request_id)
        async with self.lock:
            if self.access_exp < time():
                await self.refresh_tokens(request_id)
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Request-Id": request_id,
        }
