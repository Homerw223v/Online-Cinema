import asyncio
from aiohttp import ClientSession
from urllib.parse import urlencode

from core.config import settings
from models.abstract_database import AbstractDatabase
from models.abstract_schedule import AbstractSchedule
from services.auth import AuthService


class SchedulerService(AbstractSchedule):
    def __init__(self, database: AbstractDatabase):
        """
        Initialize the service with the provided database service.

        Args:
            database (DatabaseService): The database service instance.
        """
        self.database = database
        self.auth = AuthService(**settings.auth.model_dump()).connections()

    async def send_notification_no_auto_pay_job(self):
        users: list = await self.database.get_users_with_no_auto_pay()
        for user in users:
            await self.send_notification_to_user(str(user), settings.pattern.no_auto_pay)

    async def send_notification_no_active_card(self):
        users: list = await self.database.get_users_with_no_active_card()
        for user in users:
            await self.send_notification_to_user(str(user), settings.pattern.no_active_card)

    async def send_notification_tomorrow_auto_pay(self):
        users: list = await self.database.get_users_with_tomorrow_payment_auto_pay()
        for user in users:
            await self.send_notification_to_user(str(user), settings.pattern.tomorrow_auto_pay)

    async def check_users_to_auto_pay(self):
        users: list = await self.database.get_users_to_pay_with_auto_prolong()
        for user in users:
            await self.start_auto_payment(str(user[0]), str(user[1]))

    async def check_transaction_status(self):
        transactions: list = (
            await self.database.get_transactions_with_waiting_payment_status()
        )
        for transaction in transactions:
            await self.check_payment_status(str(transaction))

    async def send_notification_to_user(self, user_id: str, pattern_id: str):
        async with ClientSession() as session:
            async with session.post(
                settings.job.notification_url,
                params={
                    "user_id": user_id,
                    "pattern_id": pattern_id,
                    "worker": "email",
                },
                headers={"X-Request-Id": settings.x_request_id},
            ):
                await asyncio.sleep(0.1)

    async def check_payment_status(self, transaction_id: str):
        params = urlencode({"transaction_id": transaction_id})
        await self.auth.get_query(f'{settings.job.payment_status}?{params}', request_id=settings.x_request_id)
        await asyncio.sleep(0.1)

    async def start_auto_payment(self, user_id: str, tariff_id: str):
        data = {"user_id": user_id, "tariff_id": tariff_id}
        await self.auth.post_query(settings.job.auto_payment, request_id=settings.x_request_id, data=data)
        await asyncio.sleep(0.1)
