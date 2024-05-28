from abc import ABC

import backoff
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from api.v1.models import PaginatedParams
from core.config import BackoffSettings
from services.exceptions import NotFoundException


class BaseService(ABC):
    _model = ...
    _collection_name = ...
    _not_found_exception = NotFoundException

    def __init__(self, client: AsyncIOMotorClient):
        self._client = client
        self._db = self._client["review_db"]
        self._collection = getattr(self._db, self._collection_name)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_list(self, paginated_params: PaginatedParams) -> list[_model]:
        return await self._collection.find()

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def get_by_id(self, entity_id: ObjectId) -> _model:
        result = await self._collection.find_one(entity_id)
        if not result:
            raise self._not_found_exception
        return result

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def create(self, document: BaseModel) -> _model:
        inserted_obj = await self._collection.insert_one(document.model_dump(mode="json"))
        return await self.get_by_id(inserted_obj.inserted_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def update(self, entity_id: ObjectId, document: BaseModel) -> _model:
        await self._collection.replace_one({"_id": entity_id}, document.model_dump(mode="json"))
        return await self.get_by_id(entity_id)

    @backoff.on_exception(**BackoffSettings().model_dump())
    async def delete(self, entity_id: ObjectId) -> None:
        await self._collection.delete_one({"_id": entity_id})
