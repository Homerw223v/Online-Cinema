from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.v1.models import (
    UserPaymentMethodList,
    PaginatedParams,
    ActivePaymentMethodState,
    RetrieveUserPaymentMethod,
    Paginations,
)
from core.dependencies import user_info_dep

from services.services import get_user_payment_methods_service
from services.repositories import UserPaymentMethodService
from api.v1.dependencies import paginator_params_dep

cards_router = APIRouter(
    prefix="/api/v1/cards",
    tags=["cards"],
)


@cards_router.get(
    "/",
    response_model=UserPaymentMethodList,
    status_code=status.HTTP_200_OK,
)
async def get_list(
    payment_method_service: UserPaymentMethodService = Depends(get_user_payment_methods_service),
    user_info: UUID = Depends(user_info_dep),
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
) -> Any:
    results = await payment_method_service.get_list(paginated_params, filters={"user_id": user_info.user})
    count = await payment_method_service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@cards_router.delete(
    "/{payment_method_id}",
)
async def delete(
    payment_method_id: UUID,
    payment_method_service: UserPaymentMethodService = Depends(get_user_payment_methods_service),
    user_info: UUID = Depends(user_info_dep),
) -> Any:
    db_item = await payment_method_service.get_by_id(payment_method_id)
    if db_item.user_id == user_info.user:
        return await payment_method_service.delete(payment_method_id)
    raise PermissionError


@cards_router.post(
    "/{payment_method_id}/change_active",
    response_model=RetrieveUserPaymentMethod,
    status_code=status.HTTP_200_OK,
)
async def set_active_state(
    payment_method_id: UUID,
    state: ActivePaymentMethodState,
    payment_method_service: UserPaymentMethodService = Depends(get_user_payment_methods_service),
    user_info: UUID = Depends(user_info_dep),
) -> Any:
    db_item = await payment_method_service.get_by_id(payment_method_id)
    if db_item.user_id == user_info.user:
        return await payment_method_service.update(payment_method_id, state)
    raise PermissionError
