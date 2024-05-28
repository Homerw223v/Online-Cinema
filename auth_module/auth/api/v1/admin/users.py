from typing import Any
from uuid import UUID

from api.v1.admin.models import ExtendedUser, RetrieveExtendedUser, RetrieveUserPaginator
from api.v1.dependencies import paginator_params_dep
from api.v1.models import HttpException, PaginatedParams, Paginations, RetrieveUserAuthHistoryPaginator
from core.config import settings
from core.dependencies import check_access_endpoint, oauth2_scheme, token_payload_dep
from fastapi import APIRouter, Depends, status
from services.repository import UserAuthHistoryService, UsersAdminService
from services.services import get_user_admin_service, get_user_auth_history_service

from models.tokens import TokenInfo

users_router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["admin/users"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
    },
)


users_id_router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["admin/users"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
        status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Not Found"},
    },
)


@users_router.post(
    "/",
    response_model=RetrieveExtendedUser,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def create_user(
    entity: ExtendedUser,
    user_service: UsersAdminService = Depends(get_user_admin_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.create(entity)


@users_router.get("/", response_model=RetrieveUserPaginator)
@check_access_endpoint()
async def get_users_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: UsersAdminService = Depends(get_user_admin_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    results = await service.get_list(paginated_params, filters={})
    count = await service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@users_id_router.put(
    "/{user_id}",
    response_model=RetrieveExtendedUser,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def update_user(
    user_id: UUID,
    entity: ExtendedUser,
    user_service: UsersAdminService = Depends(get_user_admin_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.update(user_id, entity)


@users_id_router.delete("/{user_id}")
@check_access_endpoint()
async def delete_user(
    user_id: UUID,
    user_service: UsersAdminService = Depends(get_user_admin_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.delete(user_id)


@users_id_router.get("/{user_id}", response_model=RetrieveExtendedUser)
@check_access_endpoint(roles={settings.service_role})
async def get_user(
    user_id: UUID,
    user_service: UsersAdminService = Depends(get_user_admin_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await user_service.get_by_id(user_id)


@users_id_router.get(
    "/{user_id}/login_history",
    response_model=RetrieveUserAuthHistoryPaginator,
)
@check_access_endpoint()
async def get_login_history(
    user_id: UUID,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: UserAuthHistoryService = Depends(get_user_auth_history_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    results = await service.get_list(paginated_params, filters={"user_id": user_id})
    count = await service.count(filters={"user_id": user_id})
    return Paginations.calculate_pages(results, count, paginated_params)
