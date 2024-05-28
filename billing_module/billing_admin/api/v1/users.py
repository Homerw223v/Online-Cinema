from typing import Any
from uuid import UUID

from api.v1.models import UserSubscriptions
from fastapi import APIRouter, Depends, Request
from core.dependencies import check_access_active_subscription_endpoint, oauth2_scheme
from services.repositories import UsersSubscriptionsService
from services.services import get_users_subscriptions_service

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


@user_router.get(
    "/{user_id}/subscriptions/active",
    response_model=list[UserSubscriptions],
)
@check_access_active_subscription_endpoint(roles={"cinema"})
async def get_active_subscriptions(
    user_id: UUID,
    request: Request,
    token: str = Depends(oauth2_scheme),
    user_subscriptions_service: UsersSubscriptionsService = Depends(get_users_subscriptions_service),
) -> Any:
    return await user_subscriptions_service.get_active_subscriptions(entity_id=user_id)
