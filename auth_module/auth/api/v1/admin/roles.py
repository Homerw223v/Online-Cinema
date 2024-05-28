from typing import Any
from uuid import UUID

from api.v1.admin.models import ExtendedRole, RetrieveExtendedRole, RetrieveRolePaginator
from api.v1.dependencies import paginator_params_dep
from api.v1.models import HttpException, PaginatedParams, Paginations
from core.config import settings
from core.dependencies import check_access_endpoint, oauth2_scheme, token_payload_dep
from fastapi import APIRouter, Depends, status
from services.repository import RolesService
from services.services import get_role_service

from models.tokens import TokenInfo

roles_router = APIRouter(
    prefix="/api/v1/admin/roles",
    tags=["admin/roles"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
    },
)

roles_id_router = APIRouter(
    prefix="/api/v1/admin/roles",
    tags=["admin/roles"],
    dependencies=[Depends(oauth2_scheme)],
    responses={
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": HttpException,
            "description": "Gateway timeout",
        },
        status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Not Found"},
    },
)


@roles_router.post(
    "/",
    response_model=RetrieveExtendedRole,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def create_role(
    entity: ExtendedRole,
    service: RolesService = Depends(get_role_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.create(entity)


@roles_router.get("/", response_model=RetrieveRolePaginator)
@check_access_endpoint()
async def get_roles_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    service: RolesService = Depends(get_role_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    results = await service.get_list(paginated_params, filters={})
    count = await service.count(filters={})
    return Paginations.calculate_pages(results, count, paginated_params)


@roles_id_router.put(
    "/{role_id}",
    response_model=RetrieveExtendedRole,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HttpException,
            "description": "Already exists",
        },
    },
)
@check_access_endpoint()
async def update_role(
    role_id: UUID,
    entity: ExtendedRole,
    service: RolesService = Depends(get_role_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.update(role_id, entity)


@roles_router.delete("/{role_id}")
@check_access_endpoint()
async def delete_role(
    role_id: UUID,
    service: RolesService = Depends(get_role_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.delete(role_id)


@roles_router.get("/{role_id}", response_model=RetrieveExtendedRole)
@check_access_endpoint(roles={settings.service_role})
async def get_role(
    role_id: UUID,
    service: RolesService = Depends(get_role_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> Any:
    return await service.get_by_id(role_id)
