from contextlib import suppress
from uuid import UUID

import backoff
from bson import ObjectId

from api.v1.models import ExtendedGrade, Grade
from core.config import BackoffSettings
from db.review_db_client import get_db_client
from services.exceptions import AlreadyExistsException, GradeNotFoundException
from services.mongo.collections import film_collection
from services.mongo.mongo_repository import BaseService


class LikeService(BaseService):
    _collection_name = film_collection.name
    _not_found_exception = GradeNotFoundException

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_list(self, film_id=None, user_id=None, size=20) -> list[dict]:
        filter_match = {}
        if film_id:
            filter_match["film_id"] = str(film_id)
        if user_id:
            filter_match["grades.user_id"] = str(user_id)
        result = self._collection.aggregate(
            [
                {"$match": filter_match},
                {"$unwind": {"path": "$grades", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": "$grades._id",
                        "film_id": "$film_id",
                        "user_id": "$grades.user_id",
                        "grade": "$grades.grade",
                    },
                },
            ],
        )
        return await result.to_list(size)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_by_id(self, entity_id: ObjectId) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"grades._id": entity_id}},
                {"$unwind": "$grades"},
                {"$match": {"grades._id": entity_id}},
                {
                    "$project": {
                        "_id": "$grades._id",
                        "film_id": "$film_id",
                        "user_id": "$grades.user_id",
                        "grade": "$grades.grade",
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
    async def create(self, entity: ExtendedGrade) -> dict:
        grade = None
        with suppress(self._not_found_exception):
            grade = await self.find_user_grade(entity.user_id, entity.film_id)
        if grade:
            raise AlreadyExistsException
        self._collection.update_one(
            {"film_id": str(entity.film_id)},
            {
                "$set": {"film_id": str(entity.film_id)},
                "$push": {
                    "grades": {
                        "_id": ObjectId(),
                        "user_id": str(entity.user_id),
                        "grade": entity.grade,
                    },
                },
            },
            upsert=True,
        )
        return await self.find_user_grade(entity.user_id, entity.film_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def update(self, entity_id: ObjectId, entity: Grade) -> dict:
        self._collection.update_one({"grades._id": entity_id}, {"$set": {"grades.$.text": entity.grade}})
        return await self.get_by_id(entity_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def delete(self, entity_id: ObjectId) -> None:
        self._collection.update_one({"grades._id": entity_id}, {"$pull": {"grades": {"_id": entity_id}}})

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def find_user_grade(self, user_id: UUID, film_id: UUID) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"film_id": str(film_id)}},
                {"$unwind": "$grades"},
                {"$match": {"grades.user_id": str(user_id)}},
                {
                    "$project": {
                        "_id": "$grades._id",
                        "film_id": "$film_id",
                        "user_id": "$grades.user_id",
                        "grade": "$grades.grade",
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
    async def get_aggregate_grade(self, film_id: UUID) -> dict:
        result = self._collection.aggregate(
            [
                {"$match": {"film_id": str(film_id)}},
                {"$unwind": "$grades"},
                {
                    "$group": {
                        "_id": None,
                        "avg_grade": {"$avg": "$grades.grade"},
                    },
                },
            ],
        )
        async for row in result:  # noqa
            return row


async def get_like_service():
    yield LikeService(await get_db_client())
