from typing import Any
from uuid import UUID

from fastapi import Depends

from db.db_client import get_db_client
from interfaces.db_interface import DBInterface
from models.film import ExtendedFilm, Films
from services.exceptions import FilmNotFound
from services.services import Service


class FilmService(Service):
    INDEX = "movies"
    NOT_FOUND_EXCEPTION = FilmNotFound

    async def get_by_id(self, entity_id: UUID) -> ExtendedFilm:
        result = await self.get_query(entity_id)
        return ExtendedFilm(**result)

    async def get_list(self, *args: Any, **kwargs: Any) -> Films:
        results = await self.search_query(*args, **kwargs)
        return Films(**results)


def get_film_service(
    client: DBInterface = Depends(get_db_client),
) -> FilmService:
    return FilmService(client)
