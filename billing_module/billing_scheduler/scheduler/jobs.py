from database import postgres
from services.database_service import DatabaseService
from services.scheduler_service import SchedulerService


async def send_notification_tomorrow_auto_pay_job():
    async with postgres.async_session() as session:
        service = SchedulerService(DatabaseService(session))
        await service.send_notification_tomorrow_auto_pay()


async def send_notification_no_active_card_job():
    async with postgres.async_session() as session:
        service = SchedulerService(DatabaseService(session))
        await service.send_notification_no_active_card()


async def send_notification_no_auto_pay_job():
    async with postgres.async_session() as session:
        service = SchedulerService(DatabaseService(session))
        await service.send_notification_no_auto_pay_job()


async def check_transaction_status_job():
    async with postgres.async_session() as session:
        service = SchedulerService(DatabaseService(session))
        await service.check_transaction_status()


async def check_users_to_auto_pay_job():
    async with postgres.async_session() as session:
        service = SchedulerService(DatabaseService(session))
        await service.check_users_to_auto_pay()
