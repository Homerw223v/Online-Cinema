from abc import ABC
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, func, literal_column, select, update, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.v1.models import UserPayment, PaginatedParams
from db.models import (
    Tariff,
    Subscription,
    Base,
    Transaction,
    History,
    UserSubscription,
    UserPaymentMethod,
    TransactionState,
)
from services.exceptions import AlreadyExistException
from utils import DurationAdapter
from schemas import UserPaymentMethodDTO


DBModel = TypeVar("DBModel", bound=Base)
Schema = TypeVar("Schema", bound=BaseModel)
ExtendedSchema = TypeVar("ExtendedSchema", bound=BaseModel)
RetrieveSchema = TypeVar("RetrieveSchema", bound=BaseModel)
RetrieveExtendedSchema = TypeVar("RetrieveExtendedSchema", bound=BaseModel)


class BaseService(Generic[DBModel, ExtendedSchema], ABC):
    _model = DBModel

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        paginated_params: PaginatedParams | None,
        filters: dict,
    ) -> list[_model]:
        limit = paginated_params.page_size if paginated_params else None
        offset = (paginated_params.page_number - 1) * paginated_params.page_size if paginated_params else None
        stmt = select(self._model).filter_by(**filters).limit(limit).offset(offset)
        results = await self.session.execute(stmt)
        return list(results.scalars())

    async def count(self, filters: dict) -> int:
        stmt = select(func.count(self._model.id)).filter_by(**filters)
        return await self.session.scalar(stmt)

    async def get_by_id(self, entity_id: UUID) -> _model:
        return await self.session.get_one(self._model, entity_id)

    async def create(self, entity: ExtendedSchema) -> _model:
        db_item = self._model(**entity.model_dump())
        self.session.add(db_item)
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return db_item

    async def update(self, entity_id: UUID, entity: ExtendedSchema) -> _model:
        stmt = (
            update(self._model)
            .where(
                self._model.id == entity_id,
            )
            .values(**entity.model_dump())
            .returning(literal_column("*"))
        )
        obj = (await self.session.execute(stmt)).scalars().first()
        try:
            await self.session.commit()
        except IntegrityError:
            raise AlreadyExistException(f"Entity {entity} already exists")
        return obj

    async def delete(self, entity_id: UUID) -> None:
        stmt = delete(self._model).where(self._model.id == entity_id)
        await self.session.execute(stmt)
        await self.session.commit()


class SubscriptionsService(BaseService):
    _model = Subscription


class TransactionsService(BaseService):
    _model = Transaction

    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .options(selectinload(Transaction.tariff).selectinload(Tariff.subscription))
            .filter(self._model.id == entity_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: UserPayment) -> _model:
        tariff = await self.session.get_one(Tariff, entity.tariff_id)
        db_item = self._model(user_id=entity.user_id, tariff=tariff)
        self.session.add(db_item)
        await self.session.commit()
        return db_item

    async def set_payment_id(self, model: Transaction, payment_id: UUID) -> _model:
        model.payment_id = payment_id
        self.session.add(model)
        await self.session.commit()
        return model

    async def change_state(self, model: Transaction, state: str, commit=True):
        db_item = History(state=state, transaction=model)
        self.session.add(db_item)
        if commit:
            await self.session.commit()
        return db_item

    async def actual_state(self, transaction_id: UUID) -> str:
        subquery = select(
            History,
            func.row_number()
            .over(partition_by=History.transaction_id, order_by=desc(History.created_at))
            .label("row_number"),
        ).subquery()
        stmt = select(subquery).where(subquery.c.state == TransactionState.PAYMENT_WAIT, subquery.c.row_number == 1)
        await self.session.execute(stmt)

        stmt = select(History).filter(History.transaction_id == transaction_id).order_by(History.created_at.desc())
        model = (await self.session.execute(stmt)).scalars().first()
        return model.state

    async def activate_subscription(self, transaction: Transaction):
        tariff = transaction.tariff
        stmt = (
            select(UserSubscription)
            .filter(UserSubscription.subscription_id == tariff.subscription_id)
            .order_by(desc(UserSubscription.expired))
        )
        user_subscription = (await self.session.execute(stmt)).scalars().first()
        if user_subscription:
            current_expired = user_subscription.expired
            user_subscription.expired = DurationAdapter.increase_expired(
                current_expired, tariff.duration, tariff.duration_unit,
            )
        else:
            expired = DurationAdapter.increase_expired(datetime.utcnow(), tariff.duration, tariff.duration_unit)
            user_subscription = UserSubscription(
                user_id=transaction.user_id, subscription=tariff.subscription, expired=expired,
            )

        self.session.add(user_subscription)
        await self.change_state(transaction, TransactionState.TRANSACTION_COMPLETE.name)
        await self.session.commit()
        return user_subscription

    async def decrease_subscription(self, transaction: Transaction):
        tariff = transaction.tariff
        stmt = (
            select(UserSubscription)
            .filter(UserSubscription.subscription_id == tariff.subscription_id)
            .order_by(desc(UserSubscription.expired))
        )
        user_subscription = (await self.session.execute(stmt)).scalars().first()
        current_expired = user_subscription.expired
        user_subscription.expired = DurationAdapter.increase_expired(
            current_expired, tariff.duration, tariff.duration_unit,
        )

        self.session.add(user_subscription)
        await self.change_state(transaction, TransactionState.TRANSACTION_COMPLETE.name)
        await self.session.commit()
        return user_subscription

    async def save_user_payment_method(self, entity: UserPaymentMethodDTO):
        stmt = select(UserPaymentMethod).filter(
            UserSubscription.user_id == entity.user_id, UserPaymentMethod.title == entity.title,
        )
        payment_method = (await self.session.execute(stmt)).scalars().first()
        if not payment_method:
            payment_method = UserPaymentMethod(**entity.model_dump())
            self.session.add(payment_method)
            try:
                await self.session.commit()
            except IntegrityError:
                raise AlreadyExistException(f"Entity {entity} already exists")
        return payment_method

    async def get_user_payment_method(self, user_id) -> UserPaymentMethod:
        stmt = select(UserPaymentMethod).filter(
            UserPaymentMethod.user_id == user_id,
            UserPaymentMethod.active == True, # noqa!
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def deactivate_user_payment_method(self, entity_id: UUID) -> None:
        stmt = (
            update(UserPaymentMethod)
            .where(
                UserPaymentMethod.id == entity_id,
            )
            .values({"active": False})
            .returning(literal_column("*"))
        )
        obj = (await self.session.execute(stmt)).one()
        await self.session.commit()
        return obj


class TransactionsHistoryService(BaseService):
    _model = History


class UserSubscriptionService(BaseService):
    _model = UserSubscription


class UserPaymentMethodService(BaseService):
    _model = UserPaymentMethod
