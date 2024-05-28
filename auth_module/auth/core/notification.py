import json
from datetime import timedelta
from uuid import UUID, uuid4
import aiohttp

from db import redis
from fastapi import HTTPException, status
from models.users import User
from services.repository import UsersService

from core.config import settings


async def generate_short_link(link):
    api_url = 'http://tinyurl.com/api-create.php'
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params={"url": link}) as response:
            return await response.text()


async def send_confirm_email(user_id: UUID, email: str, request_id: str):
    if settings.notification.email_pattern is None:
        return
    confirm_request_id = str(uuid4())
    await redis.redis_interface.setex(
        confirm_request_id,
        timedelta(minutes=settings.notification.email_confirm_ttl_min),
        json.dumps({"user_id": str(user_id), "email": email}),
    )
    link = await generate_short_link(f"{settings.auth.email_confirm_url}{confirm_request_id}")
    async with aiohttp.ClientSession() as session:
        await session.post(
            str(settings.notification.email_confirm_endpoint),
            params={
                "user_id": str(user_id),
                "pattern_id": str(settings.notification.email_pattern),
                "worker": "email",
                "urgently": str(True),
            },
            json={"link_confirm": link},
            headers={"X-Request-Id": request_id},
        )


async def set_confirm_email(request_id: UUID, user_service: UsersService):
    raw_request = await redis.redis_interface.get(str(request_id))
    if raw_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    request = json.loads(raw_request)
    user = await user_service.get_by_id(entity_id=request['user_id'])
    if user.email != request['email']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    user.confirmed_email = True
    await user_service.update(
        entity_id=UUID(request['user_id']),
        entity=User.model_validate(user),
        confirmed_email=True,
    )
