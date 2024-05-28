from typing import Any
import aiohttp
from fastapi import Request

from core.config import settings
from models.models import Tokens
from http import HTTPStatus
from pydantic import HttpUrl, BaseModel


class AuthorizationError(Exception):
    ...  # noqa


class AuthService:
    def __init__(
        self,
        username: str,
        password: str,
        login_url: HttpUrl,
        refresh_url: HttpUrl,
        request_id: Any = None,
    ):
        self.login_url = str(login_url)
        self.refresh_url = str(refresh_url)
        self.username = username
        self.password = password
        self.session: aiohttp.ClientSession
        self.refresh_token = None
        self.access_token = None
        self.request_id = request_id if request_id else ''

    def connections(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        return self

    async def close(self):
        await self.session.close()

    async def get_query(self, url, response_model: BaseModel):
        async with self.session.get(url=url, headers=await self._get_headers()) as resp:
            if resp.ok:
                return response_model.model_validate_json(await resp.text())
            elif resp.status in (
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            ):
                await self.refresh_tokens()
                async with self.session.get(url=url, headers=await self._get_headers()) as resp:  # noqa
                    if resp.ok:
                        return response_model.model_validate_json(await resp.text())
            raise AuthorizationError(f"Error get user info. {await resp.text()}")

    async def get_tokens(self):
        params = {"username": self.username, "password": self.password}
        async with self.session.post(
            url=self.login_url, data=params, headers={"X-Request-Id": self.request_id},
        ) as resp:
            if resp.ok:
                tokens = Tokens.model_validate_json(await resp.text())
                self.access_token = tokens.access_token
                self.refresh_token = tokens.refresh_token
            else:
                raise AuthorizationError(f"Error receiving token. {await resp.text()}")

    async def refresh_tokens(self):
        headers = {"Authorization": f"Bearer {self.refresh_token}"}
        async with self.session.post(url=self.refresh_url, headers=headers) as resp:
            if resp.ok:
                tokens = Tokens.model_validate_json(await resp.text())
                self.access_token = tokens.access_token
                self.refresh_token = tokens.refresh_token
            elif resp.status in (
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            ):
                await self.get_tokens()
            else:
                raise AuthorizationError(f"Error refresh token. {await resp.text()}")

    async def __aenter__(self):
        return self.connections()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _get_headers(self):
        if self.access_token is None:
            await self.get_tokens()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Request-Id": self.request_id,
        }


def get_auth_service(request: Request):
    return AuthService(request_id=request.headers.get('X-Request-Id'), **settings.auth.model_dump())
