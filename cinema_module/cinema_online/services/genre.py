from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.db_client import get_db_client
from models.genre import Genre, Genres
from services.exceptions import GenreNotFound
from services.services import Service


class GenreService(Service):
    INDEX = "genres"
    NOT_FOUND_EXCEPTION = GenreNotFound

    async def get_by_id(self, entity_id: UUID) -> Genre:
        result = await self.get_query(entity_id)
        return Genre(**result)

    async def get_list(self, *args: Any, **kwargs: Any) -> Genres:
        results = await self.search_query(*args, **kwargs)
        return Genres(**results)


def get_genre_service(
    client: AsyncElasticsearch = Depends(get_db_client),
) -> GenreService:
    return GenreService(client)
