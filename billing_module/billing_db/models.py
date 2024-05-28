from __future__ import annotations

from datetime import datetime
import enum
from uuid import uuid4

from sqlalchemy import Enum
from typing_extensions import Annotated
from sqlalchemy import (
    DateTime,
    MetaData,
    String,
    ForeignKey,
    DECIMAL,
    BOOLEAN,
    UUID,
    INTEGER,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


uuid = Annotated[UUID, mapped_column(UUID, nullable=False)]
timestamp = Annotated[DateTime, mapped_column(DateTime, nullable=False)]


class TransactionState(enum.Enum):
    TRANSACTION_START = "TRANSACTION START"
    PAYMENT_WAIT = "PAYMENT WAIT"
    PAYMENT_SUCCESS = "PAYMENT SUCCESS"
    PAYMENT_CANCELED = "PAYMENT CANCELED"
    REFUND_START = "REFUND START"
    REFUND_SUCCESS = "REFUND SUCCESS"
    REFUND_CANCELED = "REFUND CANCELED"
    TRANSACTION_COMPLETE = "TRANSACTION COMPLETE"


class DurationUnit(enum.Enum):
    DAYS = "Days"
    MONTH = "Month"
    YEAR = "Year"


class Base(DeclarativeBase):
    metadata = MetaData(schema="billing")

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    created_at: Mapped[timestamp] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    name: Mapped[str] = mapped_column(String(255))
    tariffs: Mapped[list[Tariff]] = relationship("Tariff")

    def __str__(self):
        return f"{self.name}"


class Tariff(Base):
    __tablename__ = "tariffs"

    name: Mapped[str] = mapped_column(String(255))
    subscription_id: Mapped[uuid] = mapped_column(
        UUID,
        ForeignKey("billing.subscriptions.id"),
    )
    subscription: Mapped[Subscription] = relationship(
        Subscription,
        back_populates="tariffs",
    )
    duration: Mapped[int] = mapped_column(INTEGER)
    duration_unit: Mapped[str] = mapped_column(Enum(DurationUnit), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL, nullable=False)
    repeat: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=False)

    def __str__(self):
        return f"{self.name}"


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    subscription_id: Mapped[uuid] = mapped_column(
        UUID,
        ForeignKey("billing.subscriptions.id"),
    )
    subscription: Mapped[Subscription] = relationship(Subscription)
    user_id: Mapped[uuid]
    expired: Mapped[timestamp]
    auto_prolong: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)


class UserFreezeSubscription(Base):
    __tablename__ = "user_freeze_subscription"

    subscription_id: Mapped[uuid] = mapped_column(
        UUID,
        ForeignKey("billing.subscriptions.id"),
    )
    subscription: Mapped[Subscription] = relationship(Subscription)
    user_id: Mapped[uuid]
    freeze_days: Mapped[int] = mapped_column(INTEGER)


class UserPaymentMethod(Base):
    __tablename__ = "usercard"

    user_id: Mapped[uuid]
    payment_id: Mapped[uuid]
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    user_id: Mapped[uuid]
    payment_id: Mapped[UUID] = mapped_column(UUID, nullable=True)
    tariff_id: Mapped[uuid] = mapped_column(UUID, ForeignKey("billing.tariffs.id"))
    tariff: Mapped[Tariff] = relationship(Tariff)

    def __str__(self):
        return f"{self.id}:{self.payment_id}"


class History(Base):
    __tablename__ = "history"

    transaction_id: Mapped[Transaction] = mapped_column(
        UUID,
        ForeignKey("billing.transactions.id"),
    )
    transaction: Mapped[Transaction] = relationship(Transaction)
    state: Mapped[str] = mapped_column(Enum(TransactionState), nullable=False)
