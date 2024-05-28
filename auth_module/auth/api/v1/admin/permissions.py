from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.v1.admin.models import ExtendedPermission, RetrieveExtendedPermission, RetrievePermissionsPaginator
from api.v1.dependencies import paginator_params_dep
from api.v1.models import HttpException, PaginatedParams, Paginations
from core.dependencies import check_access_endpoint, oauth2_scheme, token_payload_dep
from models.tokens import TokenInfo
from services.repository import PermissionsService
from services.services import get_permission_service

permissions_router = APIRouter(
    prefix="/api/v1/admin/permissions",
    tags=["admin/permissions"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
    },
)


permissions_id_router = APIRouter(
    prefix="/api/v1/admin/permissions",
    tags=["admin/permissions"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
        status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Not Found"},
    },
)


@permissions_router.post(
    "/",
    response_model=RetrieveExtendedPermission,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def create_permission(
    entity: ExtendedPermission,
    service: PermissionsService = Depends(get_permission_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.create(entity)


@permissions_router.get("/", response_model=RetrievePermissionsPaginator)
@check_access_endpoint()
async def get_permissions_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: PermissionsService = Depends(get_permission_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    results = await service.get_list(paginated_params, filters={})
    count = await service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@permissions_id_router.put(
    "/{permission_id}",
    response_model=RetrieveExtendedPermission,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def update_permission(
    permission_id: UUID,
    entity: ExtendedPermission,
    service: PermissionsService = Depends(get_permission_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.update(permission_id, entity)


@permissions_id_router.delete("/{permission_id}")
@check_access_endpoint()
async def delete_permission(
    permission_id: UUID,
    service: PermissionsService = Depends(get_permission_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.delete(permission_id)


@permissions_id_router.get(
    "/{permission_id}",
    response_model=RetrieveExtendedPermission,
)
@check_access_endpoint()
async def get_permission(
    permission_id: UUID,
    service: PermissionsService = Depends(get_permission_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.get_by_id(permission_id)
