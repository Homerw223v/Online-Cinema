import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorClient
from database.abstract_database import AbstractDataBase
from models.models import MongoPatternModel, CRUDPatternModel, PatternListModel

mongo: AsyncIOMotorClient | None = None


class MongoDatabase(AbstractDataBase):
    model = MongoPatternModel

    async def create(self, model: CRUDPatternModel):
        pattern = self.model(
            **model.model_dump(),
            pattern_id=uuid.uuid4(),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        await pattern.insert()
        return pattern.pattern_id

    async def get(self, pattern_id: uuid.UUID):
        return await self.model.find_one(self.model.pattern_id == pattern_id)

    async def update(self, pattern_id: uuid.UUID, model: CRUDPatternModel):
        pattern = await self.model.find_one(self.model.pattern_id == pattern_id)
        if pattern:
            return await pattern.set(
                {
                    self.model.subject: model.subject,
                    self.model.content: model.content,
                    self.model.updated_at: datetime.datetime.utcnow(),
                },
            )

    async def delete(self, pattern_id: uuid.UUID):
        pattern = await self.model.find_one(self.model.pattern_id == pattern_id)
        if pattern:
            return await pattern.delete()

    async def get_all(self) -> list[PatternListModel]:
        return await self.model.find(projection_model=PatternListModel).to_list()


async def get_db_client() -> MongoDatabase:
    return MongoDatabase()  # noqa
