from uuid import UUID

import backoff
from bson import ObjectId

from api.v1.models import ExtendedReviewGrade, Grade
from core.config import BackoffSettings
from db.review_db_client import get_db_client
from services.exceptions import AlreadyExistsException, LikeNotFoundException, NotFoundException
from services.mongo.collections import film_collection
from services.mongo.mongo_repository import BaseService


class ReviewLikeService(BaseService):
    _collection_name = film_collection.name
    _not_found_exception = LikeNotFoundException

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_list(self, film_id=None, user_id=None, size=20) -> list[dict]:
        filter_match = {}
        if film_id:
            filter_match["film_id"] = str(film_id)
        if user_id:
            filter_match["reviews.grades.user_id"] = str(user_id)
        result = self._collection.aggregate(
            [
                {"$match": filter_match},
                {"$unwind": "$reviews.grades"},
                {
                    "$project": {
                        "_id": "$reviews.grades._id",
                        "film_id": "$film_id",
                        "review_id": "$reviews._id",
                        "user_id": "$reviews.grades.user_id",
                        "grade": "$reviews.grades.grade",
                    },
                },
            ],
        )
        return await result.to_list(size)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_by_id(self, entity_id: ObjectId) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"reviews.grades._id": entity_id}},
                {"$unwind": "$reviews.grades"},
                {"$match": {"reviews.grades._id": entity_id}},
                {
                    "$project": {
                        "_id": "$reviews.grades._id",
                        "film_id": "$film_id",
                        "review_id": "$reviews._id",
                        "user_id": "$reviews.grades.user_id",
                        "grade": "$reviews.grades.grade",
                    },
                },
            ],
        )
        try:
            entity = await anext(result)
        except StopAsyncIteration:  # noqa
            raise self._not_found_exception
        return entity

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def create(self, entity: ExtendedReviewGrade) -> dict:
        try:
            await self.find_user_review_grade(entity.review_id, entity.user_id)
        except NotFoundException:
            self._collection.update_one(
                {"reviews._id": entity.review_id},
                {
                    "$push": {
                        "reviews.$.grades": {
                            "_id": ObjectId(),
                            "user_id": str(entity.user_id),
                            "grade": entity.grade,
                        },
                    },
                },
            )
            return await self.find_user_review_grade(entity.review_id, entity.user_id)
        raise AlreadyExistsException

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def update(self, entity_id: ObjectId, entity: Grade) -> dict:
        self._collection.update_one(
            {"reviews.grades._id": entity_id},
            {"$set": {"reviews.grades.$.grade": entity.grade}},
        )
        return await self.get_by_id(entity_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def delete(self, entity_id: ObjectId) -> None:
        self._collection.update_one(
            {"reviews.grades._id": entity_id},
            {"$pull": {"reviews.grades.$": {"_id": entity_id}}},
        )

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def find_user_review_grade(self, review_id: ObjectId, user_id: UUID) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"reviews._id": review_id}},
                {"$unwind": "$reviews.grades"},
                {"$match": {"reviews.grades.user_id": str(user_id)}},
                {
                    "$project": {
                        "_id": "$reviews.grades._id",
                        "film_id": "$film_id",
                        "review_id": "$reviews._id",
                        "user_id": "$reviews.grades.user_id",
                        "grade": "$reviews.grades.grade",
                    },
                },
            ],
        )
        try:
            entity = await anext(result)
        except StopAsyncIteration:  # noqa
            raise self._not_found_exception
        return entity

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_aggregate_grade(self, review_id: ObjectId) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"reviews._id": review_id}},
                {"$unwind": "$reviews.grades"},
                {
                    "$group": {
                        "_id": None,
                        "likes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 10]}}},
                        "dislikes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 0]}}},
                    },
                },
            ],
        )
        async for row in result:  # noqa
            return row


async def get_review_like_service():
    yield ReviewLikeService(await get_db_client())
