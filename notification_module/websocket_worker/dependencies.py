from uuid import UUID

import aiohttp
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace

from config import AppSettings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(AppSettings.auth.login_redirect_url))

tracer = trace.get_tracer(__name__)


async def user_id_dep(
    request: Request,
    token=Depends(oauth2_scheme),
) -> UUID:
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
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth Error")
                    return UUID(await response.json())
        except Exception:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Auth service is not responding")
