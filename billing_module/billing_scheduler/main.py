import asyncio
import logging

from scheduler.scheduler import scheduler
from scheduler import jobs

logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


async def main():
    scheduler.add_job(
        jobs.send_notification_tomorrow_auto_pay_job,
        "cron",
        hour="12",
        misfire_grace_time=43200,
        id='9158024c-0a50-441d-900a-3fc74aa5e76a',
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.send_notification_no_active_card_job,
        "cron",
        hour="12",
        misfire_grace_time=43200,
        id='df09ef87-013e-4142-9089-f6dcd8a5160c',
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.send_notification_no_auto_pay_job,
        "cron",
        hour="12",
        misfire_grace_time=43200,
        id='84c8d3a4-209b-4191-83de-6ae67566011e',
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.check_users_to_auto_pay_job,
        "cron",
        hour="8",
        misfire_grace_time=43200,
        id='e46fe35c-51f1-4fa1-b737-610f6d826429',
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.check_transaction_status_job,
        "cron",
        minute="*/5",
        misfire_grace_time=180,
        id='cd1d6c3d-f64f-4fd7-bbe1-6c2096073884',
        replace_existing=True,
    )
    scheduler.start()
    try:
        while True:  # noqa
            await asyncio.sleep(3)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
