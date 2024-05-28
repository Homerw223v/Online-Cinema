import abc
from uuid import UUID

from models.models import CRUDPatternModel, MongoPatternModel, PatternListModel


class AbstractDataBase(abc.ABC):
    @abc.abstractmethod
    async def get(self, key: UUID) -> MongoPatternModel | None:
        """Getting document from database using key"""
        pass

    @abc.abstractmethod
    async def create(self, model: CRUDPatternModel) -> UUID:
        """Create document in database"""
        pass

    @abc.abstractmethod
    async def update(
        self,
        key: UUID,
        model: CRUDPatternModel,
    ) -> MongoPatternModel | None:
        """Update document in database"""
        pass

    @abc.abstractmethod
    async def delete(self, key: UUID) -> None:
        """Delete document from database"""
        pass

    @abc.abstractmethod
    async def get_all(self) -> list[PatternListModel] | None:
        """Retrieve all documents from database"""
        pass
