from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from api.v1.models import AggregateLikes, ExtendedReviewGrade, Grade, HttpException, ObjectId, RetrieveReviewGrade
from core.dependencies import user_id_dep
from core.roles import is_owner_permission
from services.mongo.review_like import ReviewLikeService, get_review_like_service

likes_review_router = APIRouter(
    prefix="/api/v1/likes_review",
    tags=["likes_review"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@likes_review_router.get("/user_like/{review_id}/{user_id}", response_model=RetrieveReviewGrade)
@cache(expire=60)
async def get_user_grade(
    review_id: ObjectId,
    user_id: UUID,
    like_service: ReviewLikeService = Depends(get_review_like_service),
) -> Any:
    return await like_service.find_user_review_grade(review_id, user_id)


@likes_review_router.post(
    "/",
    response_model=RetrieveReviewGrade,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def create(
    like: ExtendedReviewGrade,
    like_service: ReviewLikeService = Depends(get_review_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    is_owner_permission(like, user_id)
    return await like_service.create(like)


@likes_review_router.get("/grade", response_model=AggregateLikes)
@cache(expire=60)
async def get_aggregate_likes(
    review_id: ObjectId,
    like_service: ReviewLikeService = Depends(get_review_like_service),
) -> Any:
    return await like_service.get_aggregate_grade(review_id)


@likes_review_router.put(
    "/{like_id}",
    response_model=RetrieveReviewGrade,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def update(
    like_id: ObjectId,
    like: Grade,
    like_service: ReviewLikeService = Depends(get_review_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    is_owner_permission(like, user_id)
    return await like_service.update(like_id, like)


@likes_review_router.delete("/{like_id}")
async def delete(
    like_id: ObjectId,
    like_service: ReviewLikeService = Depends(get_review_like_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    like = await like_service.get_by_id(like_id)
    is_owner_permission(ExtendedReviewGrade.model_validate(like), user_id)
    return await like_service.delete(like_id)


@likes_review_router.get("/{like_id}", response_model=RetrieveReviewGrade)
@cache(expire=60)
async def get(
    like_id: ObjectId,
    like_service: ReviewLikeService = Depends(get_review_like_service),
) -> Any:
    return await like_service.get_by_id(like_id)
