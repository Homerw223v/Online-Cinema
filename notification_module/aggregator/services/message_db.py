from abc import ABC, abstractmethod
from db_models import Message
from models import SingleMessage
from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie


class AbstractMessageStorage(ABC):
    @abstractmethod
    async def get_messages(self, user_id, pattern_id) -> list[Message]:
        pass

    @abstractmethod
    async def get_by_id(self, entity_id) -> Message:
        pass

    @abstractmethod
    async def insert(self, entity):
        pass


class MongoMessageStorage(AbstractMessageStorage):
    model = Message

    def __init__(self, dsn: str, database: str):
        self._client = AsyncIOMotorClient(dsn)
        self._db = self._client[database]

    async def init_model(self):
        await init_beanie(database=self._client.db, document_models=[self.model])

    async def get_by_id(self, entity_id) -> Message:
        return await self.model.get(entity_id)

    async def get_messages(self, user_id, pattern_id) -> list[Message]:
        return await self.model.find(
            self.model.user_id == user_id,
            self.model.pattern_id == pattern_id,
            self.model.state == False, # noqa!
        ).to_list()

    async def insert(self, msg: SingleMessage):
        result = await self.model.find_one(
            self.model.incoming_msg_id == msg.incoming_msg_id, self.model.user_id == msg.user_id,
        ).update(
            {
                "$setOnInsert": {
                    "request_id": msg.request_id,
                    "incoming_msg_id": msg.incoming_msg_id,
                    "pattern_id": msg.pattern_id,
                    "user_id": msg.user_id,
                    "data": msg.data,
                    "worker": msg.worker,
                    "urgently": msg.urgently,
                },
            },
            upsert=True,
        )
        return result.upserted_id
