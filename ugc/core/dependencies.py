from typing import Annotated
from uuid import UUID

import aiohttp
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace

from api.v1.models import PaginatedParams
from core.config import AppSettings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(AppSettings.auth.login_redirect_url))

tracer = trace.get_tracer(__name__)


async def paginator_params_dep(
    page_size: Annotated[int, Query(description="Pagination page size", ge=1)] = 20,
    page_number: Annotated[int, Query(description="Pagination page number", ge=1)] = 1,
) -> PaginatedParams:
    return PaginatedParams(page_size=page_size, page_number=page_number)


async def user_id_dep(request: Request, token=Depends(oauth2_scheme)) -> UUID:
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
