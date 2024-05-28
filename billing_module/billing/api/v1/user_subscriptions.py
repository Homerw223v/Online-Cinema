from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.v1.models import UserSubscriptionsList, PaginatedParams, AutoProlongState, Paginations
from core.dependencies import user_info_dep

from services.services import get_user_subscriptions_service
from services.repositories import UserSubscriptionService
from api.v1.dependencies import paginator_params_dep

user_subscriptions_router = APIRouter(
    prefix="/api/v1/subscriptions",
    tags=["user_subscriptions"],
)


@user_subscriptions_router.get(
    "/",
    response_model=UserSubscriptionsList,
    status_code=status.HTTP_200_OK,
)
async def get_list(
    user_subscriptions_service: UserSubscriptionService = Depends(get_user_subscriptions_service),
    user_info: UUID = Depends(user_info_dep),
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
) -> Any:
    results = await user_subscriptions_service.get_list(paginated_params, filters={"user_id": user_info.user})
    count = await user_subscriptions_service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@user_subscriptions_router.post(
    "/{user_subscription_id}/auto_prolong",
    response_model=Any,
    status_code=status.HTTP_200_OK,
)
async def set_auto_prolong(
    user_subscription_id: UUID,
    state: AutoProlongState,
    user_subscriptions_service: UserSubscriptionService = Depends(get_user_subscriptions_service),
    user_info: UUID = Depends(user_info_dep),
) -> Any:
    db_item = await user_subscriptions_service.get_by_id(user_subscription_id)
    if db_item.user_id == user_info.user:
        return await user_subscriptions_service.update(user_subscription_id, state)
    raise PermissionError
