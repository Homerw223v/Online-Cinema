from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.db_client import get_db_client
from models.person import ExtendedPerson, Persons
from services.exceptions import PersonNotFound
from services.services import Service


class PersonService(Service):
    INDEX = "persons"
    NOT_FOUND_EXCEPTION = PersonNotFound

    async def get_by_id(self, entity_id: UUID) -> ExtendedPerson:
        result = await self.get_query(entity_id)
        return ExtendedPerson(**result)

    async def get_list(self, *args: Any, **kwargs: Any) -> Persons:
        results = await self.search_query(*args, **kwargs)
        return Persons(**results)


def get_person_service(
    client: AsyncElasticsearch = Depends(get_db_client),
) -> PersonService:
    return PersonService(client)
