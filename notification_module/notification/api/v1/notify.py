from typing import Any
from uuid import UUID
import aio_pika

from api.v1.models import HttpException, WorkerType
from fastapi import APIRouter, Depends, status, Body, Request

from db.rabbit import get_rabbit_exchange
from models.rabbit import GroupMessage, Message


notify_router = APIRouter(
    prefix="/api/v1/notification",
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
    },
)


@notify_router.post("/send_notify")
async def send_notification(
    request: Request,
    user_id: UUID,
    pattern_id: UUID,
    worker: WorkerType,
    data: dict[str, Any] = Body(default={}),
    urgently: bool = False,
    rabbit_exchange=Depends(get_rabbit_exchange),
) -> None:
    message = Message(
        request_id=request.headers.get("X-Request-Id"),
        user_id=user_id,
        pattern_id=pattern_id,
        worker=worker,
        data=data,
        urgently=urgently,
    )
    await rabbit_exchange.publish(
        aio_pika.Message(body=message.model_dump_json().encode()),
        routing_key="single",
    )


@notify_router.post("/group_send_notify")
async def send_notification_to_group(
    request: Request,
    role_id: UUID,
    pattern_id: UUID,
    worker: WorkerType,
    data: dict[str, Any] = Body(default={}),
    urgently: bool = False,
    rabbit_exchange=Depends(get_rabbit_exchange),
) -> None:
    message = GroupMessage(
        request_id=request.headers.get("X-Request-Id"),
        role_id=role_id,
        pattern_id=pattern_id,
        worker=worker,
        data=data,
        urgently=urgently,
    )
    await rabbit_exchange.publish(
        aio_pika.Message(body=message.model_dump_json().encode()),
        routing_key="group",
    )
