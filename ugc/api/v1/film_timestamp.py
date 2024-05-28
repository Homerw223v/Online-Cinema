from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.v1.models import ExtendedFilmTimestamp, FilmTimestamp, HttpException, ObjectId, RetrieveFilmTimestamp
from core.dependencies import user_id_dep
from core.roles import is_owner_permission
from services.mongo.film_timestamp import FilmTimestampService, get_film_timestamp_service

timestamp_router = APIRouter(
    prefix="/api/v1/timestamp",
    tags=["film_timestamp"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@timestamp_router.post(
    "/",
    response_model=RetrieveFilmTimestamp,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def create(
    entity: ExtendedFilmTimestamp,
    service: FilmTimestampService = Depends(get_film_timestamp_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    is_owner_permission(entity, user_id)
    return await service.create(entity)


@timestamp_router.put(
    "/{timestamp_id}",
    response_model=RetrieveFilmTimestamp,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def update(
    entity_id: ObjectId,
    entity: FilmTimestamp,
    service: FilmTimestampService = Depends(get_film_timestamp_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    obj = await service.get_by_id(entity_id)
    is_owner_permission(ExtendedFilmTimestamp.model_validate(obj), user_id)
    return await service.update(entity_id, entity)


@timestamp_router.delete("/{timestamp_id}")
async def delete(
    entity_id: ObjectId,
    service: FilmTimestampService = Depends(get_film_timestamp_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    grade = await service.get_by_id(entity_id)
    is_owner_permission(ExtendedFilmTimestamp.model_validate(grade), user_id)
    return await service.delete(entity_id)


@timestamp_router.get("/{timestamp_id}", response_model=RetrieveFilmTimestamp)
async def get(
    entity_id: ObjectId,
    service: FilmTimestampService = Depends(get_film_timestamp_service),
) -> Any:
    return await service.get_by_id(entity_id)
