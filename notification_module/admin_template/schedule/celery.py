import asyncio
import logging
from uuid import UUID

import aiohttp
from celery import Celery

from core.config import settings

celery_event_loop = asyncio.new_event_loop()
celery_app = Celery(
    main="scheduler",
    broker=settings.celery.broker_dsn,
    redbeat_redis_url=settings.redis.dsn,
)

celery_app.autodiscover_tasks()
logger = logging.getLogger(__name__)


async def send_message_to_entity_once(
    entity_id: UUID,
    pattern_id: UUID,
    worker: str,
    send_to: str,
):
    """
    Sends a message to a notification service.

    Args:
        entity_id (UUID): Entity identifier
        pattern_id (UUID): Pattern identifier
        worker (str): Worker type
        send_to (str): Recipient ("user" or "group")

    Returns:
            None
    """
    headers = {"X-Request-Id": "1"}
    params = {"pattern_id": pattern_id, "worker": worker}
    if send_to not in ("user", "group"):
        return
    dict_key = "user_id" if send_to == "user" else "role_id"
    params.update({dict_key: entity_id})
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(  # noqa
                url=settings.celery.notification_user if send_to == "user" else settings.celery.notification_group,
                params=params,
                headers=headers,
            ):
                pass
    except Exception as error:
        logger.error("Something went wrong: %s" % error)
    else:
        logger.info("Task completed successfully")


@celery_app.task
def send_message_to_user_with_celery(
    entity_id: UUID,
    pattern_id: UUID,
    worker: str,
    send_to: str,
):
    celery_event_loop.run_until_complete(
        send_message_to_entity_once(entity_id, pattern_id, worker, send_to),
    )
