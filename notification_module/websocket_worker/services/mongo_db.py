from abc import ABC, abstractmethod
from db_models import Message
from models import ProcessingMessage
from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie
from beanie.operators import In, Set


class AbstractMessageStorage(ABC):
    @abstractmethod
    async def get_messages(self, user_id, pattern_id) -> list[Message]:
        pass

    @abstractmethod
    async def get_by_id(self, entity_id) -> Message:
        pass

    @abstractmethod
    async def insert(self, msg: ProcessingMessage):
        pass

    @abstractmethod
    async def set_state_sent(self, entities_ids):
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
            self.model.sent == False, # noqa!
        ).to_list()

    async def insert(self, msg: ProcessingMessage):
        await self.model(**msg.model_dump()).insert()

    async def set_state_sent(self, entities_ids):
        await self.model.find(In(self.model.id, entities_ids)).update(Set({self.model.sent: True}))


message_db: MongoMessageStorage


def get_message_db():
    return message_db # noqa!
