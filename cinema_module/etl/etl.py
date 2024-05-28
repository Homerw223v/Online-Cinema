import logging
from datetime import datetime
from threading import Thread
from time import sleep
from typing import Any, Generator, Hashable, Iterator

import backoff
from redis import ConnectionPool as RedisConnectionPool
from redis import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from row_factory import BaseClass
from settings import AppSettings, TableAdapter
from workers import ElasticLoader, PGExtractor


class EtlState:
    PREFIX = "ETL"
    LOCK_KEY = "LOCK"
    MODIFY_KEY = "MODIFY"

    def __init__(self, client_id: Hashable, driver: Redis, lifetime: int):
        self.client_id = client_id
        self.redis = driver
        self.lifetime = lifetime

    @backoff.on_exception(backoff.expo, exception=(ConnectionError, TimeoutError), max_value=120)
    def check_connection(self) -> bool:
        """Проверка соединения с redis"""
        return bool(self.redis.ping())

    def check_block(self) -> bool:
        """Проверка на наличие запущенных экземпляров приложения"""
        process_hash = self.redis.get(f"{self.PREFIX}:{self.LOCK_KEY}")
        return process_hash is not None and hash(self.client_id) != int(process_hash.decode())  # type: ignore

    def set_block(self) -> None:
        """Установка блокировки запуска других экземпляров приложения"""

        if self.check_block():
            self.redis.set(f"{self.PREFIX}:{self.LOCK_KEY}", hash(self.client_id), ex=self.lifetime)

    def unlock_process(self) -> None:
        """Снятие блокировки запуска других экземпляров приложения"""

        if str(hash(self.client_id)).encode() == self.redis.get(f"{self.PREFIX}:{self.LOCK_KEY}"):
            self.redis.delete(f"{self.PREFIX}:{self.LOCK_KEY}")

    def get_modified_dt(self, table_name: str) -> datetime:
        """Получить дату и время последней зарегистрированной модификации таблицы"""

        datetime_string = self.redis.get(f"{self.PREFIX}:{self.MODIFY_KEY}:{table_name}")
        if datetime_string is None:
            return datetime.min
        return datetime.fromisoformat(datetime_string.decode())  # type: ignore

    def set_modified_dt(self, table_name: str, modified_dt: datetime) -> None:
        """Записать дату и время последней зарегистрированной модификации таблицы"""

        self.redis.set(f"{self.PREFIX}:{self.MODIFY_KEY}:{table_name}", modified_dt.isoformat())


class ETLProcess:
    def __init__(
        self,
        app_settings: AppSettings,
        lifetime: int = 10,
    ):
        self.exit_flag = False
        logging.info("Launching the application.")
        self.pg_settings = app_settings.database
        self.elastic_settings = app_settings.elastic
        redis_pool = RedisConnectionPool.from_url(
            url=str(app_settings.redis.dsn),
            socket_timeout=2,
            retry=Retry(ExponentialBackoff(60), -1),  # type: ignore
            retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError],
        )
        redis = Redis(connection_pool=redis_pool)
        self.state = EtlState(id(self), redis, lifetime)
        self.state.check_connection()
        if self.state.check_block():
            logging.error("Attempt to start a duplicate process.")
            raise RuntimeError("Attempt to start a duplicate process.")

        thread = Thread(
            target=self._process_locker,
            args=[EtlState(id(self), Redis(connection_pool=redis_pool), lifetime)],
        )
        thread.start()
        logging.info("The application is running")

    def __del__(self) -> None:
        self.state.unlock_process()

    @backoff.on_exception(backoff.expo, exception=Exception, max_value=120)
    def run(self, adapters: list[TableAdapter], sleep_time: int = 30) -> None:
        """Основной процесс переноса данных"""
        self.loader = ElasticLoader(self.elastic_settings)
        self._create_if_not_exists_index(adapters)
        with PGExtractor(self.pg_settings, row_factory=BaseClass) as id_extractor:
            with PGExtractor(self.pg_settings, row_factory=BaseClass) as link_id_extractor:
                with PGExtractor(self.pg_settings) as data_extractor:
                    while not self.exit_flag:
                        for adapter in adapters:
                            logging.info("Transferring data from %s", adapter.table)
                            modified_dt = self.state.get_modified_dt(adapter.table)
                            base_obj_chunks = id_extractor.extract_data(adapter.get_id_query, modified_dt)
                            # получили измененые объекты
                            self._index_chunk_processing(
                                adapter,
                                base_obj_chunks,  # type: ignore
                                link_id_extractor,
                                data_extractor,
                            )
                            self._update_modified_time(adapter)
                        sleep(sleep_time)

    def _index_chunk_processing(
        self,
        adapter: TableAdapter,
        base_obj_chunks: Generator[Iterator[BaseClass], Any, Any],
        link_id_extractor: PGExtractor,
        data_extractor: PGExtractor,
    ) -> None:
        for chunk in base_obj_chunks:
            chunk_data = [row for row in chunk]  # сохраняем чтобы получить последний объект
            base_ids = ", ".join(f"'{row.id}'" for row in chunk_data)
            for index_adapter in adapter.index_adapters:
                if index_adapter.linking_query:
                    link_data = link_id_extractor.extract_data(index_adapter.linking_query.format(ids=base_ids))
                    link_ids = ", ".join(
                        [", ".join(f"'{row.id}'" for row in chunk) for chunk in link_data],  # type: ignore
                    )
                else:
                    link_ids = base_ids
                data_extractor.set_factory(index_adapter.data_class)
                data = data_extractor.extract_data(index_adapter.get_data_query.format(ids=link_ids))
                self.loader.load_data(index_adapter.index["index"], data)
            self._set_modified_time(adapter, chunk_data[-1].modified)

    def _create_if_not_exists_index(self, adapters: list[TableAdapter]) -> None:
        """Проверка и создание индекса в случае его отсутствия."""
        for adapter in adapters:
            for index_adapter in adapter.index_adapters:
                index_name = index_adapter.index["index"]
                if not self.loader.check_index(index_name):
                    logging.info("Creating an index %s", index_name)
                    self.loader.create_index(index_adapter.index)
                    logging.info("Index %s created.", index_name)

    def _set_modified_time(self, adapter: TableAdapter, new_time: datetime) -> None:
        adapter.new_modified = new_time

    def _update_modified_time(self, adapter: TableAdapter) -> None:
        """Обновление времени последнего перенесенного изменения"""
        last_transform = adapter.new_modified
        if last_transform:
            self.state.set_modified_dt(adapter.table, last_transform)
            logging.info(
                "Data from %s was successfully migrated. Last update %s",
                adapter.table,
                last_transform,
            )
        else:
            logging.info("%s no updated data.", adapter.table)

    def _process_locker(self, state: EtlState) -> None:
        """Периодическое обновление значения для блокировки запуска дублирующих процессов"""
        while not self.exit_flag:
            state.set_block()
            sleep(min(5, self.state.lifetime - 5))
