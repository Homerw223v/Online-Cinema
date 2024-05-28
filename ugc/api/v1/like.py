from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from api.v1.models import AggregateGrade, ExtendedGrade, Grade, HttpException, ObjectId, RetrieveGrade
from core.dependencies import user_id_dep
from core.roles import is_owner_permission
from services.mongo.like import LikeService, get_like_service

likes_router = APIRouter(
    prefix="/api/v1/likes",
    tags=["likes"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@likes_router.get("/user_like/{film_id}/{user_id}", response_model=RetrieveGrade)
@cache(expire=60)
async def get_user_grade(
    film_id: UUID,
    user_id: UUID,
    like_service: LikeService = Depends(get_like_service),
) -> Any:
    return await like_service.find_user_grade(film_id, user_id)


@likes_router.get("/grade", response_model=AggregateGrade)
@cache(expire=60)
async def get_aggregate_grade(
    film_id: UUID,
    like_service: LikeService = Depends(get_like_service),
) -> Any:
    grade = await like_service.get_aggregate_grade(film_id)
    return grade if grade else AggregateGrade(avg_grade=None)


@likes_router.post(
    "/",
    response_model=RetrieveGrade,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def create(
    like: ExtendedGrade,
    like_service: LikeService = Depends(get_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    is_owner_permission(like, user_id)
    return await like_service.create(like)


@likes_router.put(
    "/{like_id}",
    response_model=RetrieveGrade,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def update(
    like_id: ObjectId,
    like: Grade,
    like_service: LikeService = Depends(get_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    obj = await like_service.get_by_id(like_id)
    is_owner_permission(ExtendedGrade.model_validate(obj), user_id)
    return await like_service.update(like_id, like)


@likes_router.delete("/{like_id}")
async def delete(
    like_id: ObjectId,
    like_service: LikeService = Depends(get_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    grade = await like_service.get_by_id(like_id)
    is_owner_permission(ExtendedGrade.model_validate(grade), user_id)
    return await like_service.delete(like_id)


@likes_router.get("/{like_id}", response_model=RetrieveGrade)
@cache(expire=60)
async def get(
    like_id: ObjectId,
    like_service: LikeService = Depends(get_like_service),
) -> Any:
    return await like_service.get_by_id(like_id)
