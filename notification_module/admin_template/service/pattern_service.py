from typing import Any
from uuid import UUID

from fastapi import Depends
from jinja2 import Template as PatternTemplate

from core.config import settings
from models.models import CRUDPatternModel, MongoPatternModel, User, PatternListModel
from fastapi.exceptions import HTTPException
from database.mongo_db import get_db_client
from database.abstract_database import AbstractDataBase
from service.auth_service import AuthService, get_auth_service


class PatternService:
    def __init__(self, database, auth_service):
        self.database: AbstractDataBase = database
        self.auth_service: AuthService = auth_service

    async def save_pattern(self, pattern: CRUDPatternModel) -> UUID:
        """
        Save pattern to the database.

        Args:
            pattern (CRUDPatternModel): The pattern data to be saved.

        Returns:
            UUID: The UUID of the saved pattern.
        """
        return await self.database.create(pattern)

    async def get_single_pattern(self, pattern_id: UUID) -> CRUDPatternModel:
        """
        Retrieves a single pattern from the database based on the pattern ID.

        Args:
            pattern_id (str): The UUID of the pattern to retrieve.

        Returns:
            CRUDPatternModel: The retrieved pattern as a CRUDPatternModel object.

        Raises:
            HTTPException: If the pattern is not found, raises HTTPException with status code 404.
        """
        pattern: MongoPatternModel | None = await self.database.get(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404)
        return CRUDPatternModel(**pattern.model_dump())

    async def render_pattern(self, pattern_id: UUID, user_id: str, variables: dict[str, Any]) -> CRUDPatternModel:
        data: User = await self.get_user_info(user_id)
        variables.update(data.model_dump())
        pattern: CRUDPatternModel = await self.get_single_pattern(pattern_id)
        return CRUDPatternModel(
            subject=PatternTemplate(pattern.subject).render(**variables),
            content=PatternTemplate(pattern.content).render(**variables),
        )

    async def update_pattern(
        self,
        pattern_id: UUID,
        pattern: CRUDPatternModel,
    ) -> None:
        """
        Updates pattern in the database based on the pattern ID.

        Args:
            pattern_id (UUID): The UUID of the pattern to update.
            pattern (CRUDPatternModel): The updated pattern data.

        Raises:
            HTTPException: If the pattern is not found, raises HTTPException with status code 404.
        """
        pattern: MongoPatternModel | None = await self.database.update(
            pattern_id,
            pattern,
        )
        if not pattern:
            raise HTTPException(status_code=404)

    async def delete_pattern(self, pattern_id: UUID) -> None:
        """
        Deletes a pattern from the database based on the pattern ID.

        Args:
            pattern_id (UUID): The UUID of the pattern to delete.

        Raises:
            HTTPException: If the pattern is not found, raises HTTPException with status code 404.
        """
        pattern = await self.database.delete(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404)

    async def get_all_patterns(self) -> list[PatternListModel]:
        """
        Retrieves all patterns from the database.

        Returns:
            List[CRUDPatternModel]: A list of all patterns retrieved from the database.
        """
        return await self.database.get_all()

    async def get_user_info(self, user_id: str, request_id: str = None) -> User:
        """
        Gets user information.

        Arguments:
            user_id (UUID): User identifier
            request_id (str): Unique request ID

        Returns:
            (User): User information
        """
        async with self.auth_service as auth:
            if request_id:
                auth.request_id = request_id
            url = f"{settings.url.user_info_url}/{user_id}"
            return await auth.get_query(url, User)


def get_pattern_service(
    mongo_db=Depends(get_db_client),
    auth_service: AuthService = Depends(get_auth_service),
) -> PatternService:
    """
    Function to get an instance of the PatternService.

    Returns:
        PatternService: An instance of the PatternService.
    """
    return PatternService(mongo_db, auth_service)
