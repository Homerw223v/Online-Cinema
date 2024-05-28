import logging
from collections.abc import Generator, Iterator
from itertools import chain, islice
from typing import Any

import backoff
import psycopg
from elastic_transport import TransportError
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from psycopg.rows import class_row
from pydantic import BaseModel

from exceptions import ElasticLoadException
from row_factory import BaseClass, ElasticDataClasses, EtlClasses
from settings import DbSettings, ElasticSettings


class PGExtractor:
    def __init__(
        self,
        settings: DbSettings,
        chunk_size: int = 100,
        row_factory: type[BaseClass] | ElasticDataClasses | None = None,
    ):
        self.dsn = settings.dsn
        self.chunk_size = chunk_size
        self.row_factory = row_factory

    @backoff.on_exception(backoff.expo, exception=psycopg.errors.ConnectionTimeout, max_value=120)
    def __enter__(self) -> "PGExtractor":
        self._conn = psycopg.Connection.connect(str(self.dsn), cursor_factory=psycopg.ClientCursor)
        self._cursor = self._conn.cursor()
        self._cursor.itersize = self.chunk_size  # type: ignore
        if self.row_factory:
            self.set_factory(self.row_factory)
        logging.info("The connection to the database is established.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self._cursor.close()
        self._conn.close()
        if exc_type:
            logging.error("An error occurred during the operation.")
            logging.debug("An error occurred during the operation %s: %s", exc_type, exc_val)
        logging.info("The connection to the DBMS is closed.")

    def set_factory(self, factory: type[BaseClass] | ElasticDataClasses) -> None:
        self._cursor.row_factory = class_row(factory)  # type: ignore

    @backoff.on_exception(backoff.expo, exception=psycopg.errors.OperationalError, max_value=120)
    def extract_data(self, query: str, *query_args: Any) -> Generator[Iterator[EtlClasses], None, None]:
        """Метод генерирует итераторы полученных их БД данных"""

        self._cursor.execute(query, query_args)
        yield from self._chunk_generator(self._cursor)

    def _chunk_generator(self, cursor: psycopg.Cursor) -> Generator[Iterator[EtlClasses], None, None]:
        """Метод группирует на итераторы полученные их БД данные"""

        for first_chunk_item in cursor:
            yield chain((first_chunk_item,), islice(cursor, self.chunk_size - 1))


class ElasticLoader:
    def __init__(self, settings: ElasticSettings):
        self.client = Elasticsearch(str(settings.base_url))

    def load_data(self, index_name: str, data: Iterator[Iterator[BaseModel]]) -> None:
        """Метод загрузки данных пачками в ElasticSearch в указанный индекс"""

        bulk_quantity = None
        # Преобразуем генератор в кортеж, чтобы не разряжать генератор при исключениях
        for num, bulk in enumerate(map(tuple, data), start=1):
            self.load_bulk(bulk, index_name)
            bulk_quantity = num
        if not bulk_quantity:
            logging.info("No new data.")

    @backoff.on_exception(backoff.expo, exception=(TransportError), max_value=120)
    def check_index(self, index_name: str) -> bool:
        """Проверка наличия индекса в ElasticSearch"""
        return self.client.indices.exists(index=index_name).body

    def create_index(self, index: dict[str, Any]) -> None:
        self.client.indices.create(**index)

    @backoff.on_exception(backoff.expo, exception=(TransportError, ElasticLoadException), max_value=120)
    def load_bulk(self, bulk: tuple, index_name: str) -> None:
        for _ in streaming_bulk(  # noqa
            client=self.client,
            index=index_name,
            actions=self._row_generator(bulk),
            yield_ok=False,
            max_retries=50,
        ):
            raise ElasticLoadException

    @staticmethod
    def _row_generator(data: tuple) -> Generator[dict[str, Any], None, None]:
        """Генератор строк для формирования пачки записей"""
        for row in data:
            yield {"_id": str(row.id), "_source": row.model_dump()}
