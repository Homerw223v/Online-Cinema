from functools import wraps

import aiohttp
import jwt
from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from db import redis
from time import time
from models.token import TokenInfo
from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(settings.auth.login_redirect_url))
tracer = trace.get_tracer(__name__)


async def get_token_roles(request: Request, token=str) -> set[str]:
    with tracer.start_as_current_span("check-token-request"):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.auth.base_url}roles",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "x-request-id": request.headers.get("x-request-id"),
                    },
                ) as response:
                    if response.status != status.HTTP_200_OK:
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth Error")
                    return set(await response.json())
        except Exception:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Auth service is not responding")


def check_access_active_subscription_endpoint(roles: set[str] = set()):  # noqa
    def inner(func):  # noqa
        @wraps(func)
        async def view_method(*args, **kwargs):  # noqa
            token: str | None = kwargs.get("token")
            if token is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="token depends error",
                )
            token_data = TokenInfo(**jwt.decode(token, options={"verify_signature": False}))
            if token_data.roles & roles:
                # check cache tokens
                if await redis.redis_interface.get(token):
                    return await func(*args, **kwargs)

            # validate token
            request = kwargs.get("request")
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="request depends error",
                )
            request: Request
            user_roles = await get_token_roles(request, token)

            # checking the request for yourself
            user_id = kwargs.get("user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="user_id depends error",
                )
            if token_data.user == str(user_id):
                return await func(*args, **kwargs)

            # check roles permissions
            if "admin" not in user_roles:  # admin everything is allowed
                if not roles & user_roles:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            if roles & user_roles:
                await redis.redis_interface.setex(
                    name=token,
                    time=token_data.exp - int(time()),
                    value=1,
                )
            return await func(*args, **kwargs)

        return view_method

    return inner
