from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, Body

from core.config import settings
from service.pattern_service import get_pattern_service, PatternService
from models.models import CRUDPatternModel, PatternListModel, TokenInfo
from core.dependencies import (
    user_id_dependency,
    check_access_endpoint,
    token_payload_dep,
)

router = APIRouter(
    prefix="/api/v1/patterns",
    tags=["pattern"],
)


@router.post(
    "/",
    description="Create pattern for notification",
    response_model=UUID,
)
@check_access_endpoint(roles={settings.service_role})
async def create_pattern(
    pattern: CRUDPatternModel,
    token_payload: TokenInfo = Depends(token_payload_dep),
    service: PatternService = Depends(get_pattern_service),
) -> UUID:
    return await service.save_pattern(pattern)


@router.get(
    "/",
    description="Get all available patterns",
    response_model=list[PatternListModel],
)
@check_access_endpoint(roles={settings.service_role})
async def get_all_patterns(
    service=Depends(get_pattern_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> list[PatternListModel]:
    return await service.get_all_patterns()


@router.get(
    "/{pattern_id}",
    description="Get single pattern",
)
@check_access_endpoint(roles={settings.service_role})
async def get_single_pattern(
    pattern_id: UUID,
    token_payload: TokenInfo = Depends(token_payload_dep),
    service: PatternService = Depends(get_pattern_service),
) -> CRUDPatternModel:
    return await service.get_single_pattern(pattern_id)


@router.get(
    "/{pattern_id}/render",
    description="Get single pattern",
)
@check_access_endpoint(roles={settings.service_role})
async def get_single_pattern_render(
    pattern_id: UUID,
    data: dict[str, Any] = Body(),
    token_payload: TokenInfo = Depends(token_payload_dep),
    service: PatternService = Depends(get_pattern_service),
    user_id: str | None = Depends(user_id_dependency),
) -> CRUDPatternModel:
    return await service.render_pattern(pattern_id, user_id, data)


@router.put(
    "/{pattern_id}",
    description="Update pattern",
)
@check_access_endpoint(roles={settings.service_role})
async def update_pattern(
    pattern_id: UUID,
    pattern: CRUDPatternModel,
    token_payload: TokenInfo = Depends(token_payload_dep),
    service=Depends(get_pattern_service),
    user_id: UUID | None = Depends(user_id_dependency),
):
    await service.update_pattern(pattern_id, pattern)
    return status.HTTP_200_OK


@router.delete(
    "/{pattern_id}",
    description="Delete pattern.",
)
@check_access_endpoint(roles={settings.service_role})
async def delete_pattern(
    pattern_id: UUID,
    token_payload: TokenInfo = Depends(token_payload_dep),
    service=Depends(get_pattern_service),
):
    await service.delete_pattern(pattern_id)
    return status.HTTP_200_OK
