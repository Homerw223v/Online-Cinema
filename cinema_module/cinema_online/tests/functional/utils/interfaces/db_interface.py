from abc import ABC, abstractmethod
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk


class DBInterface(ABC):
    @abstractmethod
    def __init__(self, client: Any):
        self.client = client

    @abstractmethod
    def create_or_replace_table(self, table_name, table_data):
        pass

    @abstractmethod
    def write_data(self, table_name, data):
        pass

    @abstractmethod
    def delete_entity_by_uuid(self, table_name, uuid):
        pass


class ElasticInterface(DBInterface):
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def create_or_replace_table(self, table_name, table_data):
        if await self.client.indices.exists(index=table_name):
            await self.client.indices.delete(index=table_name)
        await self.client.indices.create(**table_data)

    async def write_data(self, table_name, data):
        bulk_query: list[dict] = []
        for row in data:
            data = {"_index": table_name, "_id": row["id"], "_source": row}
            bulk_query.append(data)
        updated, errors = await async_bulk(client=self.client, actions=bulk_query, refresh="wait_for")
        if errors:
            raise Exception("Error writing to Elasticsearch")  # noqa

    async def delete_entity_by_uuid(self, index, uuid):
        result = await self.client.delete(index=index, id=uuid, refresh="wait_for")
        if result["result"] != "deleted":
            raise Exception("Error deleting from Elasticsearch")  # noqa
