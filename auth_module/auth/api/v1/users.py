from typing import Any
from uuid import UUID

from api.v1.dependencies import paginator_params_dep
from api.v1.models import Paginations  # noqa
from api.v1.models import (
    HttpException, PaginatedParams, ReceivedUser, RetrieveUser, RetrieveUserAuthHistoryPaginator, User,
)
from core.dependencies import check_access_personal_account, oauth2_scheme, token_payload_dep
from core.notification import send_confirm_email
from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException, Request
from services.repository import UserAuthHistoryService, UsersService
from services.services import get_user_auth_history_service, get_user_service

from models.tokens import TokenInfo

open_user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["personal_account"],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
    },
)

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["personal_account"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
        status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Not Found"},
    },
)


@open_user_router.post(
    "/",
    response_model=RetrieveUser,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
async def create_user(
    entity: User,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UsersService = Depends(get_user_service),
) -> Any:
    user = await user_service.create(entity)
    background_tasks.add_task(send_confirm_email, user.id, user.email, request.headers.get("X-Request-Id"))
    return user


@user_router.put(
    "/{user_id}",
    response_model=RetrieveUser,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_personal_account
async def update_user(
    user_id: UUID,
    entity: ReceivedUser,
    background_tasks: BackgroundTasks,
    user_service: UsersService = Depends(get_user_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    current_user = await user_service.get_by_id(user_id)
    confirmed_email = current_user.confirmed_email
    if current_user.email != entity.email:
        confirmed_email = False
    updated_user = await user_service.update(user_id, entity, confirmed_email=confirmed_email)
    if confirmed_email is False:
        background_tasks.add_task(send_confirm_email, updated_user.id, updated_user.email)
    return updated_user


@user_router.delete("/{user_id}")
@check_access_personal_account
async def delete_user(
    user_id: UUID,
    user_service: UsersService = Depends(get_user_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.delete(user_id)


@user_router.get("/{user_id}", response_model=RetrieveUser)
@check_access_personal_account
async def get_user(
    user_id: UUID,
    user_service: UsersService = Depends(get_user_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.get_by_id(user_id)


@user_router.get(
    "/{user_id}/login_history",
    response_model=RetrieveUserAuthHistoryPaginator,
)
@check_access_personal_account
async def get_login_history(
    user_id: UUID,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: UserAuthHistoryService = Depends(get_user_auth_history_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    results = await service.get_list(paginated_params, filters={"user_id": user_id})
    count = await service.count(filters={"user_id": user_id})
    return Paginations.calculate_pages(results, count, paginated_params)


@user_router.post(
    "/{user_id}/confirm_email",
    status_code=status.HTTP_202_ACCEPTED,
    description="Send email for confirm address",
)
@check_access_personal_account
async def send_confirm_email_address(
    user_id: UUID,
    background_tasks: BackgroundTasks,
    user_service: UsersService = Depends(get_user_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> None:
    current_user = await user_service.get_by_id(user_id)
    if current_user.confirmed_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email confirmed")
    background_tasks.add_task(send_confirm_email, current_user.id, current_user.email)
