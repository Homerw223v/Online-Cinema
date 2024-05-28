from abc import ABC, abstractmethod
from math import ceil
from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from opentelemetry import trace

from core.config import AppSettings
from services.exceptions import NotFoundException
from services.query_params import ElasticSearchQueryBuilder, sort_params

tracer = trace.get_tracer(__name__)
app_settings = AppSettings()


class DBInterface(ABC):
    @abstractmethod
    def __init__(self, elastic: Any):
        self.client = elastic

    @abstractmethod
    async def get_query(self, source: str, entity_id: UUID) -> dict[str, Any]:  # noqa
        pass  # noqa

    @abstractmethod
    async def search_query(
        self,
        source: str,
        page_number: int,
        page_size: int,
        query_phrase: str | None = None,
        nested_query: dict[str, UUID] | None = None,
        sort: str = "",
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        pass  # noqa


class ElasticInterface(DBInterface):
    def __init__(self, elastic: AsyncElasticsearch):
        self.client = elastic

    async def get_query(self, source: str, entity_id: UUID) -> dict[str, Any]:
        """Метод возвращает документ по заданному параметру entity_id"""
        with tracer.start_as_current_span("elasticsearch-request"):
            try:
                result = await self.client.get(index=source, id=str(entity_id))
            except NotFoundError as ex:  # noqa
                raise NotFoundException from ex
            return result["_source"]

    async def search_query(
        self,
        source: str,
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
        :param fields: список возвращаемых полей
        """
        with tracer.start_as_current_span("elasticsearch-request"):
            query_builder = ElasticSearchQueryBuilder()
            processed_sort = sort_params.get(sort)
            if nested_query:
                query_builder.add_nested_search_params_id(nested_query)
            else:
                query_builder.add_search_param(query_phrase)
            count_responce = await self.client.count(index=source, body=query_builder.query)  # type: ignore
            item_count = count_responce["count"]
            query_builder.add_pagination(page=page_number, size=page_size)
            result = await self.client.search(
                index=source,
                sort=processed_sort,
                body=query_builder.query,  # type: ignore
                source_includes=fields,
            )
            total_page = ceil(item_count / page_size)
            return {
                "count": item_count,
                "total_pages": total_page,
                "prev": page_number - 1 if page_number > 1 else None,
                "next": page_number + 1 if page_number < total_page else None,
                "page": page_number,
                "results": [doc["_source"] for doc in result["hits"]["hits"]],
            }

    async def close(self):
        await self.client.close()
