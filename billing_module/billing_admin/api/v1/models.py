from datetime import datetime
from math import ceil
from typing import Any
from uuid import UUID

from pydantic import AliasPath, BaseModel, Field


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


class UserSubscriptions(BaseModel):
    class Config:
        from_attributes = True

    subscription_id: UUID
    name: str = Field(alias=AliasPath(["subscription", "name"]))
    expired: datetime
    auto_prolong: bool


class Subscriptions(BaseModel):
    class Config:
        from_attributes = True

    id: UUID
    name: str


class Tariffs(BaseModel):
    id: UUID
    name: str
    duration: int
    duration_unit: str
    price: float
    repeat: bool


class ExtendedSubscriptions(Subscriptions):
    tariffs: list[Tariffs]


class SubscriptionsPaginator(Paginations):
    results: list[Subscriptions]
