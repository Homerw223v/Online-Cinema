from datetime import datetime
from uuid import UUID

import backoff
from bson import ObjectId

from api.v1.models import ExtendedReview, PaginatedParams, Review
from core.config import BackoffSettings
from db.review_db_client import get_db_client
from services.exceptions import AlreadyExistsException, NotFoundException, ReviewNotFoundException
from services.mongo.collections import film_collection
from services.mongo.mongo_repository import BaseService


class ReviewService(BaseService):
    _collection_name = film_collection.name
    _not_found_exception = ReviewNotFoundException

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_list(self, paginated_params: PaginatedParams, film_id=None, user_id=None) -> list[dict]:
        filter_match = {}
        if film_id:
            filter_match["film_id"] = str(film_id)
        if user_id:
            filter_match["reviews.user_id"] = str(user_id)
        result = self._collection.aggregate(
            [
                {"$match": filter_match},
                {"$unwind": "$reviews"},
                {
                    "$project": {
                        "_id": "$reviews._id",
                        "film_id": "$film_id",
                        "user_id": "$reviews.user_id",
                        "text": "$reviews.text",
                        "created": "$reviews.created",
                    },
                },
                {"$skip": paginated_params.offset},
            ],
        )
        return await result.to_list(paginated_params.page_size)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_by_id(self, entity_id: ObjectId) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"reviews._id": entity_id}},
                {"$unwind": "$reviews"},
                {"$match": {"reviews._id": entity_id}},
                {"$unwind": {"path": "$reviews.grades", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": "$reviews._id",
                        "grades": {
                            "$first": {
                                "$first": {
                                    "$filter": {
                                        "input": "$grades",
                                        "as": "grade",
                                        "cond": {"$eq": ["$$grade.user_id", "$reviews.user_id"]},
                                    },
                                },
                            },
                        },
                        "film_id": {"$first": "$film_id"},
                        "user_id": {"$first": "$reviews.user_id"},
                        "text": {"$first": "$reviews.text"},
                        "created": {"$first": "$reviews.created"},
                        "likes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 10]}}},
                        "dislikes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 0]}}},
                    },
                },
                {
                    "$project": {
                        "film_id": "$film_id",
                        "user_id": "$user_id",
                        "text": "$text",
                        "film_grade": "$grades.grade",
                        "created": "$created",
                        "review_grade.likes": "$likes",
                        "review_grade.dislikes": "$dislikes",
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
    async def create(self, entity: ExtendedReview) -> dict:
        try:
            await self.find_user_review(entity.user_id, entity.film_id)
        except NotFoundException:
            self._collection.update_one(
                {"film_id": str(entity.film_id)},
                {
                    "$set": {"film_id": str(entity.film_id)},
                    "$push": {
                        "reviews": {
                            "_id": ObjectId(),
                            "user_id": str(entity.user_id),
                            "text": entity.text,
                            "created": datetime.now(),
                        },
                    },
                },
                upsert=True,
            )
            return await self.find_user_review(entity.user_id, entity.film_id)
        raise AlreadyExistsException

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def update(self, entity_id: ObjectId, entity: Review) -> dict:
        self._collection.update_one({"reviews._id": entity_id}, {"$set": {"reviews.$.text": entity.text}})
        return await self.get_by_id(entity_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def delete(self, entity_id: ObjectId) -> None:
        self._collection.update_one({"reviews._id": entity_id}, {"$pull": {"reviews": {"_id": entity_id}}})

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def find_user_review(self, user_id: UUID, film_id: UUID) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"film_id": str(film_id)}},
                {"$unwind": "$reviews"},
                {"$match": {"reviews.user_id": str(user_id)}},
                {"$unwind": {"path": "$reviews.grades", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": "$reviews._id",
                        "grades": {
                            "$first": {
                                "$first": {
                                    "$filter": {
                                        "input": "$grades",
                                        "as": "grade",
                                        "cond": {"$eq": ["$$grade.user_id", "$reviews.user_id"]},
                                    },
                                },
                            },
                        },
                        "film_id": {"$first": "$film_id"},
                        "user_id": {"$first": "$reviews.user_id"},
                        "text": {"$first": "$reviews.text"},
                        "created": {"$first": "$reviews.created"},
                        "likes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 10]}}},
                        "dislikes": {"$sum": {"$toInt": {"$eq": ["$reviews.grades.grade", 0]}}},
                    },
                },
                {
                    "$project": {
                        "film_id": "$film_id",
                        "user_id": "$user_id",
                        "text": "$text",
                        "film_grade": "$grades.grade",
                        "created": "$created",
                        "review_grade.likes": "$likes",
                        "review_grade.dislikes": "$dislikes",
                    },
                },
            ],
        )
        try:
            entity = await anext(result)
        except StopAsyncIteration:  # noqa
            raise self._not_found_exception
        return entity


async def get_review_service():
    yield ReviewService(await get_db_client())
