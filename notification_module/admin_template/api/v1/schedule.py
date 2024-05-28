import asyncio
import functools
from fastapi import APIRouter, status, Depends

from core.config import settings
from models.schedule import ScheduleInformation
from models.models import TokenInfo

from schedule.celery import send_message_to_user_with_celery
from core.dependencies import (
    check_access_endpoint,
    token_payload_dep,
)
from service.pattern_service import get_pattern_service, PatternService

router = APIRouter(
    prefix="/api/v1/schedule",
    tags=["schedule"],
)


@router.post(
    "/",
    description="Set a delayed notification to user or group of users. Depends on send_to: Optional['user', 'group']",
)
@check_access_endpoint(roles={settings.service_role})
async def schedule_notification_to_user(
    information: ScheduleInformation,
    pattern_service: PatternService = Depends(get_pattern_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
):
    if await pattern_service.get_single_pattern(pattern_id=information.pattern_id):
        loop = asyncio.get_running_loop()
        celery_run_func = functools.partial(
            send_message_to_user_with_celery.apply_async,
            (
                information.entity_id,
                information.pattern_id,
                information.worker,
                information.send_to,
            ),
            eta=information.time,
        )
        await loop.run_in_executor(None, celery_run_func)
        return status.HTTP_200_OK
