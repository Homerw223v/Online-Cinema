from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

import backoff
from elasticsearch import ConnectionError

from interfaces.db_interface import DBInterface
from services.exceptions import NotFoundException


class Service(ABC):
    expo_base_sec = 1.2
    backoff_max_time_sec = 3

    @classmethod  # type: ignore[misc]
    @property
    @abstractmethod
    def INDEX(cls):  # type: ignore
        pass  # noqa

    @classmethod  # type: ignore[misc]
    @property
    @abstractmethod
    def NOT_FOUND_EXCEPTION(cls):  # type: ignore
        pass  # noqa

    def __init__(self, client: DBInterface):
        self.client = client

    @backoff.on_exception(
        backoff.expo,
        exception=ConnectionError,
        jitter=backoff.random_jitter,
        base=expo_base_sec,
        max_time=backoff_max_time_sec,
    )
    async def get_query(self, entity_id: UUID) -> dict[str, Any]:
        """Метод возвращает документ по заданному параметру entity_id"""
        try:
            return await self.client.get_query(self.INDEX, entity_id)
        except NotFoundException as ex:  # noqa
            raise self.NOT_FOUND_EXCEPTION from ex

    @backoff.on_exception(
        backoff.expo,
        exception=ConnectionError,
        jitter=backoff.random_jitter,
        base=expo_base_sec,
        max_time=backoff_max_time_sec,
    )
    async def search_query(
        self,
        page_number: int,
        page_size: int,
        query_phrase: str | None = None,
        nested_query: dict[str, UUID] | None = None,
        sort: str = "",
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Метод получения списка документов, возвращает все документы если задан пустой поисковый запрос.

        :param page_number: номер страницы
        :param page_size: размер страницы
        :param query_phrase: фраза для поиска
        :param nested_query: словарь, где ключ название поля для вложенного объекта, значение поля
        :param sort: сортировка, может принимать значения ["imdb_rating", "-imdb_rating"]
        :param fields: список полей возвращаемых из elastic search
        """
        return await self.client.search_query(
            self.INDEX,
            page_number,
            page_size,
            query_phrase,
            nested_query,
            sort,
            fields,
        )
