from typing import Any
from pydantic import BaseModel, HttpUrl, Field
from uuid import UUID
from math import ceil
from datetime import datetime


class IdModel(BaseModel):
    id: UUID


class PaginatedParams(BaseModel):
    page_size: int = Field(ge=1, default=20)
    page_number: int = Field(ge=1, default=1)


class Paginations(BaseModel):
    count: int
    total_pages: int
    next: int | None
    prev: int | None
    page: int
    results: Any

    @classmethod
    def calculate_pages(cls, results, item_count, paginated_params: PaginatedParams):
        page_size = paginated_params.page_size
        page_number = paginated_params.page_number
        total_page = ceil(item_count / page_size)
        return cls(
            count=item_count,
            total_pages=total_page,
            prev=page_number - 1 if page_number > 1 else None,
            next=page_number + 1 if page_number < total_page else None,
            page=page_number,
            results=results,
        )


class Payment(BaseModel):
    tariff_id: UUID


class Refund(BaseModel):
    transaction_id: UUID


class UserPayment(Payment):
    user_id: UUID


class RetrievePayment(IdModel, UserPayment):
    confirmation_url: HttpUrl | None


class PaymentProviderState(IdModel):
    state: str


class ActivePaymentMethodState(BaseModel):
    active: bool


class AutoProlongState(BaseModel):
    auto_prolong: bool


class RetrieveUserPaymentMethod(IdModel):
    type: str
    title: str
    active: bool


class UserPaymentMethodList(Paginations):
    results: list[RetrieveUserPaymentMethod]


class RetrieveUserSubscription(IdModel):
    subscription_id: UUID
    expired: datetime
    auto_prolong: bool


class UserSubscriptionsList(Paginations):
    results: list[RetrieveUserSubscription]
