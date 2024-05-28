from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from api.v1.models import (
    ExtendedRetrieveReview,
    ExtendedReview,
    HttpException,
    ObjectId,
    PaginatedParams,
    RetrieveReview,
    Review,
)
from core.dependencies import paginator_params_dep, user_id_dep
from core.roles import is_owner_permission
from services.mongo.review import ReviewService, get_review_service

review_router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["reviews"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@review_router.get(
    "/",
    response_model=list[RetrieveReview],
    status_code=status.HTTP_201_CREATED,
)
@cache(expire=60)
async def get_list(
    film_id: UUID = None,
    user_id: UUID = None,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    review_service: ReviewService = Depends(get_review_service),
) -> Any:
    return await review_service.get_list(paginated_params, film_id, user_id)


@review_router.get("/{film_id}/{user_id}", response_model=ExtendedRetrieveReview)
@cache(expire=60)
async def find(
    user_id: UUID,
    film_id: UUID,
    review_service: ReviewService = Depends(get_review_service),
) -> Any:
    return await review_service.find_user_review(user_id, film_id)


@review_router.post(
    "/",
    response_model=ExtendedRetrieveReview,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def create(
    review: ExtendedReview,
    review_service: ReviewService = Depends(get_review_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    is_owner_permission(review, user_id)
    return await review_service.create(review)


@review_router.put(
    "/{like_id}",
    response_model=ExtendedRetrieveReview,
    responses={status.HTTP_409_CONFLICT: {"model": HttpException, "description": "Already exists"}},
)
async def update(
    review_id: ObjectId,
    review: Review,
    review_service: ReviewService = Depends(get_review_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    obj = await review_service.get_by_id(review_id)
    is_owner_permission(ExtendedReview.model_validate(obj), user_id)
    return await review_service.update(review_id, review)


@review_router.delete("/{review_id}")
async def delete(
    review_id: ObjectId,
    review_service: ReviewService = Depends(get_review_service),
    user_id: UUID = Depends(user_id_dep),
) -> Any:
    review = await review_service.get_by_id(review_id)
    is_owner_permission(ExtendedReview.model_validate(review), user_id)
    return await review_service.delete(review_id)


@review_router.get("/{review_id}", response_model=ExtendedRetrieveReview)
@cache(expire=60)
async def get(
    review_id: ObjectId,
    review_service: ReviewService = Depends(get_review_service),
) -> Any:
    return await review_service.get_by_id(review_id)
