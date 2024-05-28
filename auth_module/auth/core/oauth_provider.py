import json
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import aiohttp

from core.config import AppSettings, BaseOauth
from models.oauth_provider import OauthUserData
from models.tokens import OauthState, TokenInfo


class UnknownOauthProviderError(Exception): ...  # noqa


class OauthProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...  # noqa

    @property
    @abstractmethod
    def settings(self) -> BaseOauth: ...  # noqa

    @classmethod
    def get_redirect_url(cls, user_payload: TokenInfo | None) -> str:
        url = str(cls.settings.dialog_oauth_url)
        redirect_params = cls._get_redirect_params()
        state = {"provider_name": cls.provider_name}
        if user_payload:
            state["user_id"] = user_payload.user
        redirect_params["state"] = json.dumps(state)
        params = urlencode(redirect_params)
        return f"{url}?{params}"

    @classmethod
    async def get_user_info(cls, code: str, state: str | None) -> OauthUserData:
        provider_payload = await cls._get_token(code)
        user_info = await cls._get_user_info(provider_payload)
        return await cls._create_oauth_user_info(provider_payload, user_info, state)

    @classmethod
    @abstractmethod
    def _get_redirect_params(cls) -> dict[str, str]: ...  # noqa

    @classmethod
    @abstractmethod
    async def _get_token(cls, code: str) -> dict[str, str]: ...  # noqa

    @classmethod
    @abstractmethod
    async def _get_user_info(cls, provider_payload: dict[str, str]) -> dict[str, str]: ...  # noqa

    @classmethod
    @abstractmethod
    async def _create_oauth_user_info(
        cls,
        provider_payload: dict[str, str],
        user_info: dict[str, str],
        state: OauthState,
    ) -> OauthUserData:
        pass  # noqa


class YandexOauthProvider(OauthProvider):
    provider_name = "yandex"
    settings = AppSettings.oauth_yandex

    @classmethod
    def _get_redirect_params(cls) -> dict[str, str]:
        return {
            "response_type": "code",
            "client_id": cls.settings.client_id,
        }

    @classmethod
    async def _get_token(cls, code: str) -> dict[str, str]:
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": cls.settings.client_id,
            "client_secret": cls.settings.client_secret,
        }
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=str(cls.settings.token_oauth_url),
                data=params,
                headers=headers,
            )
            return await response.json()

    @classmethod
    async def _get_user_info(cls, provider_payload: dict[str, str]) -> dict[str, str]:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url=str(cls.settings.user_info_url),
                params={"format": "json", "jwt_secret": cls.settings.client_secret},
                headers={"Authorization": f"OAuth {provider_payload['access_token']}"},
            )
            return await response.json()

    @classmethod
    async def _create_oauth_user_info(
        cls,
        provider_payload: dict[str, str],
        user_info: dict[str, str],
        state: OauthState,
    ) -> OauthUserData:
        return OauthUserData(
            provider_name=cls.provider_name,
            user_id=state.user_id,
            client_id=user_info["id"],
            email=user_info["default_email"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
        )


class VkOauthProvider(OauthProvider):
    provider_name = "vk"
    settings = AppSettings.oauth_vk

    @classmethod
    def _get_redirect_params(cls) -> dict[str, str]:
        return {
            "response_type": "code",
            "client_id": cls.settings.client_id,
            "redirect_uri": cls.settings.redirect_url,
            "scope": cls.settings.scope,
        }

    @classmethod
    async def _get_token(cls, code: str) -> dict[str, str]:
        params = {
            "code": code,
            "client_id": cls.settings.client_id,
            "client_secret": cls.settings.client_secret,
            "redirect_uri": cls.settings.redirect_url,
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=str(cls.settings.token_oauth_url),
                data=params,
            )
            return await response.json()

    @classmethod
    async def _get_user_info(cls, provider_payload: dict[str, str]) -> dict[str, str]:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url=str(cls.settings.user_info_url),
                params={"v": "5.199"},
                headers={"Authorization": f"Bearer {provider_payload['access_token']}"},
            )
            body = await response.json()
            return body["response"]

    @classmethod
    async def _create_oauth_user_info(
        cls,
        provider_payload: dict[str, str],
        user_info: dict[str, str],
        state: OauthState,
    ) -> OauthUserData:
        return OauthUserData(
            provider_name=cls.provider_name,
            user_id=state.user_id,
            client_id=str(user_info["id"]),
            email=provider_payload["email"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
        )


class OauthProviderFactory:
    _providers_list = [YandexOauthProvider, VkOauthProvider]
    providers = {provider.provider_name: provider for provider in _providers_list}

    @classmethod
    def get_provider(cls, name: str):
        provider = cls.providers.get(name)
        if not provider:
            raise UnknownOauthProviderError
        return provider

    @classmethod
    def get_all_provider_names(cls):
        return list(cls.providers.keys())
