from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from decimal import Decimal
from datetime import timedelta


class SubscribeInfoDTO(BaseModel):
    name: str
    price: Decimal = Field(ge=0, decimal_places=2)
    expired: timedelta


class IdModel(BaseModel):
    id: UUID


class PaymentDTO(BaseModel):
    tariff_id: UUID


class UserPaymentDTO(PaymentDTO):
    user_id: UUID


class RetrievePaymentDTO(IdModel, UserPaymentDTO):
    confirmation_url: HttpUrl | None


class PaymentProviderStateDTO(IdModel):
    state: str


class UserPaymentMethodDTO(BaseModel):
    user_id: UUID
    payment_id: UUID
    type: str
    title: str
