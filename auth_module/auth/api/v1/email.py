from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from services.services import get_user_service
from services.repository import UsersService
from core.notification import set_confirm_email

email_router = APIRouter(prefix="/api/v1/email")


@email_router.get("/confirm_address/request/{request_id}")
async def set_confirm_email_address(
    request_id: UUID,
    user_service: UsersService = Depends(get_user_service),
) -> Any:
    return await set_confirm_email(request_id=request_id, user_service=user_service)
