import aiohttp
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
import jwt

from core.config import AppSettings
from models.token import TokenInfo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(AppSettings.auth.login_redirect_url))

tracer = trace.get_tracer(__name__)


async def user_info_dep(
    request: Request,
    token=Depends(oauth2_scheme),
) -> TokenInfo:
    with tracer.start_as_current_span("check-token-request"):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{AppSettings.auth.base_url}user_id",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "x-request-id": request.headers.get("x-request-id"),
                    },
                ) as response:
                    if response.status != status.HTTP_200_OK:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Auth Error",
                        )
                    return TokenInfo(**jwt.decode(token, options={"verify_signature": False}))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Auth service is not responding",
            )


async def is_admin_dep(
    request: Request,
    token=Depends(oauth2_scheme),
) -> bool:
    token_data = TokenInfo(**jwt.decode(token, options={"verify_signature": False}))
    if {"admin", "scheduler"}.intersection(token_data.roles):
        with tracer.start_as_current_span("check-token-request"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{AppSettings.auth.base_url}roles",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "x-request-id": request.headers.get("x-request-id"),
                        },
                    ) as response:
                        if response.status != status.HTTP_200_OK:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Auth Error",
                            )
                        return True
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Auth service is not responding",
                )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied",
    )
