from typing import Annotated
from uuid import UUID

import aiohttp
import jwt

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace

from api.v1.models import PaginatedParams
from core.config import AppSettings, settings
from services.auth import get_auth_client, AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(AppSettings.auth.login_redirect_url))

tracer = trace.get_tracer(__name__)


async def paginator_params_dep(
    page_size: Annotated[int, Query(description="Pagination page size", ge=1)] = 20,
    page_number: Annotated[int, Query(description="Pagination page number", ge=1)] = 1,
) -> PaginatedParams:
    return PaginatedParams(page_size=page_size, page_number=page_number)


async def token_roles_dep(
    request: Request,
    token=Depends(oauth2_scheme),
) -> set[str]:
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
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth Error")
                    return set(await response.json())
        except Exception:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Auth service is not responding")


async def user_subscriptions_dep(
    request: Request,
    token=Depends(oauth2_scheme),
    auth_client: AuthService = Depends(get_auth_client),
) -> list[UUID]:
    user_id = jwt.decode(token, options={'verify_signature': False})['sub']
    user_subscriptions_raw = []
    with tracer.start_as_current_span("get_user_subscriptions"):
        user_subscriptions_raw = await auth_client.get_query(
            url=str(settings.billing.user_subscription_list_url).replace('user_id', user_id),
            request_id=request.headers.get("x-request-id"),
        )
    return [UUID(subscription['subscription_id']) for subscription in user_subscriptions_raw]
