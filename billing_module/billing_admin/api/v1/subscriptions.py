from typing import Any
from uuid import UUID

from api.v1.dependencies import paginator_params_dep
from api.v1.models import ExtendedSubscriptions, PaginatedParams, Paginations, SubscriptionsPaginator
from fastapi import APIRouter, Depends
from services.repositories import SubscriptionsService
from services.services import get_subscriptions_service

subscription_router = APIRouter(
    prefix="/api/v1/subscriptions",
    tags=["subscriptions"],
)


@subscription_router.get("/", response_model=SubscriptionsPaginator)
async def get_subscription_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: SubscriptionsService = Depends(get_subscriptions_service),
) -> Any:
    results = await service.get_list(paginated_params, filters={})
    count = await service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@subscription_router.get("/{subscription_id}", response_model=ExtendedSubscriptions)
async def get_subscription(
    subscription_id: UUID,
    service: SubscriptionsService = Depends(get_subscriptions_service),
) -> Any:
    return await service.get_by_id(subscription_id)
