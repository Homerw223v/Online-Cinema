from abc import ABC
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from api.v1.models import PaginatedParams
from db.models import Base, Subscription, UserSubscription

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

DBModel = TypeVar("DBModel", bound=Base)


class BaseService(Generic[DBModel], ABC):
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


class UsersSubscriptionsService(BaseService[UserSubscription]):
    _model = UserSubscription

    async def get_active_subscriptions(self, entity_id: UUID) -> list[_model]:
        stmt = (
            select(self._model)
            .filter(
                UserSubscription.user_id == entity_id,
                UserSubscription.expired > datetime.now(),
            )
            .options(
                selectinload(self._model.subscription),
            )
        )
        results = await self.session.execute(stmt)
        return list(results.scalars())


class SubscriptionsService(BaseService[Subscription]):
    _model = Subscription

    async def get_by_id(self, entity_id: UUID) -> _model:
        stmt = (
            select(self._model)
            .filter(
                Subscription.id == entity_id,
            )
            .options(
                selectinload(self._model.tariffs),
            )
        )
        return (await self.session.execute(stmt)).one()[0]
