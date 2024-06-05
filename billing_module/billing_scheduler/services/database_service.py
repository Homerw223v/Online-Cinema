import datetime as dt
from models.abstract_database import AbstractDatabase

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from database.models import UserSubscription, UserPaymentMethod, History, TransactionState, Tariff


class DatabaseService(AbstractDatabase):
    def __init__(self, session: AsyncSession):
        """
        Initialize the DatabaseService with the provided AsyncSession.

        Args:
            session (AsyncSession): The asynchronous session to interact with the database.
        """
        self.session = session

    async def get_users_with_no_auto_pay(self):
        current_time: dt.datetime = dt.datetime.utcnow()
        two_days_later: dt.datetime = current_time + dt.timedelta(days=2)
        three_days_later: dt.datetime = current_time + dt.timedelta(days=3)
        smtp = select(UserSubscription.user_id).filter(
            ~UserSubscription.auto_prolong,
            UserSubscription.expired.between(two_days_later, three_days_later),
        )
        results = await self.session.execute(smtp)
        return list(results.scalars())

    async def get_users_with_no_active_card(self):
        current_time: dt.datetime = dt.datetime.utcnow()
        two_days_later: dt.datetime = current_time + dt.timedelta(days=2)
        three_days_later: dt.datetime = current_time + dt.timedelta(days=3)
        smtp = select(UserSubscription.user_id).join(
            UserPaymentMethod,
            and_(
                UserSubscription.user_id == UserPaymentMethod.user_id,
                UserSubscription.auto_prolong,
                UserSubscription.expired.between(two_days_later, three_days_later),
                ~UserPaymentMethod.active,
            ),
        )
        results = await self.session.execute(smtp)
        return list(results.scalars())

    async def get_users_with_tomorrow_payment_auto_pay(self):
        current_time: dt.datetime = dt.datetime.utcnow()
        one_day_later: dt.datetime = current_time + dt.timedelta(days=1)
        two_days_later: dt.datetime = current_time + dt.timedelta(days=2)
        smtp = select(UserSubscription.user_id).filter(
            UserSubscription.auto_prolong,
            UserSubscription.expired.between(one_day_later, two_days_later),
        )
        results = await self.session.execute(smtp)
        return list(results.scalars())

    async def get_users_to_pay_with_auto_prolong(self):
        current_time: dt.datetime = dt.datetime.utcnow()
        one_day_later: dt.datetime = current_time + dt.timedelta(days=1)
        two_days_later: dt.datetime = current_time + dt.timedelta(days=2)
        smtp = select(UserSubscription.user_id, Tariff.id).join(
            Tariff, Tariff.subscription_id == UserSubscription.subscription_id,
        ).join(
            UserPaymentMethod,
            and_(
                UserSubscription.user_id == UserPaymentMethod.user_id,
                UserSubscription.auto_prolong,
                UserSubscription.expired.between(one_day_later, two_days_later),
                UserPaymentMethod.active,
            ),
        )
        results = await self.session.execute(smtp)
        return list(results.all())

    async def get_transactions_with_waiting_payment_status(self):
        subquery = select(
            History,
            func.row_number().over(
                partition_by=History.transaction_id,
                order_by=desc(History.created_at),
            ).label("row_number"),
        ).subquery()
        stmt = select(subquery).where(
            subquery.c.state == TransactionState.PAYMENT_WAIT,
            subquery.c.row_number == 1,
        )
        results = await self.session.execute(stmt)
        return list(results.scalars())
