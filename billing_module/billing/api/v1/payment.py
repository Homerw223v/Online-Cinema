from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.v1.models import Payment, RetrievePayment, UserPayment, PaymentProviderState, Refund
from core.dependencies import user_info_dep, is_admin_dep
from models.token import TokenInfo
from services.services import get_payment_service, get_refund_service
from services.payment import PaymentService, RefundService

roles_access_check_state = {'scheduler'}

payment_router = APIRouter(
    prefix="/api/v1/payment",
    tags=["payment"],
)


@payment_router.post(
    "/",
    response_model=RetrievePayment,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    payment: Payment,
    payment_service: PaymentService = Depends(get_payment_service),
    user_info: TokenInfo = Depends(user_info_dep),
) -> Any:
    user_payment = UserPayment(user_id=user_info.user, **payment.model_dump())
    transaction = await payment_service.start(user_payment)
    return await payment_service.create(transaction)


@payment_router.post(
    "/autopayment",
    response_model=RetrievePayment,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    user_payment: UserPayment,
    payment_service: PaymentService = Depends(get_payment_service),
    is_admin: bool = Depends(is_admin_dep),
) -> Any:
    transaction = await payment_service.start(user_payment)
    return await payment_service.create(transaction)


@payment_router.post(
    "/refund",
    response_model=PaymentProviderState,
    status_code=status.HTTP_201_CREATED,
)
async def refund_payment(
    refund: Refund,
    refund_service: RefundService = Depends(get_refund_service),
    is_admin: bool = Depends(is_admin_dep),
) -> Any:
    transaction = await refund_service.start(refund)
    return await refund_service.create(transaction)


@payment_router.get(
    "/",
    response_model=PaymentProviderState,
    status_code=status.HTTP_200_OK,
)
async def check_state(
    transaction_id: UUID,
    payment_service: PaymentService = Depends(get_payment_service),
    user_info: TokenInfo = Depends(user_info_dep),
) -> Any:
    db_item = await payment_service.get_transaction(transaction_id)
    if db_item.user_id == user_info.user or user_info.roles & roles_access_check_state:
        return await payment_service.check_state(transaction_id)
    raise PermissionError
