import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Any

from pydantic import HttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from db_queries import Queries
from elastic_indexes import index_genre, index_movie, index_person
from row_factory import ElasticFilmData, ElasticGenreData, ElasticPersonData


@dataclass
class IndexAdapter:
    data_class: type[ElasticFilmData | ElasticGenreData]
    get_data_query: str
    index: dict[str, Any]
    linking_query: str | None = None


@dataclass
class TableAdapter:
    get_id_query: str
    table: str
    index_adapters: list[IndexAdapter]
    new_modified: datetime | None = None


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="pg_db_")
    dsn: PostgresDsn


class ElasticSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="elastic_")
    base_url: HttpUrl


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


class LoggingSettings:
    stream: IO = sys.stdout
    format: str = "%(asctime)s - %(levelname)s - %(message)s"
    level: int = logging.INFO

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "level": self.level,
            "stream": self.stream,
        }


class AppSettings:
    database = DbSettings()
    elastic = ElasticSettings()
    redis = RedisSettings()
    logging = LoggingSettings()


adapters = [
    TableAdapter(
        get_id_query=Queries.FILMWORK_MODIFIED,
        table="filmwork",
        index_adapters=[
            IndexAdapter(
                data_class=ElasticFilmData,
                linking_query=None,
                get_data_query=Queries.FILMWORK_DATA,
                index=index_movie,
            ),
            IndexAdapter(
                data_class=ElasticPersonData,
                linking_query=Queries.PERSON_BY_FILM,
                get_data_query=Queries.PERSON_DATA,
                index=index_person,
            ),
        ],
    ),
    TableAdapter(
        get_id_query=Queries.PERSON_MODIFIED,
        table="person",
        index_adapters=[
            IndexAdapter(
                data_class=ElasticFilmData,
                linking_query=Queries.FILM_BY_PERSON,
                get_data_query=Queries.FILMWORK_DATA,
                index=index_movie,
            ),
            IndexAdapter(
                data_class=ElasticPersonData,
                linking_query=None,
                get_data_query=Queries.PERSON_DATA,
                index=index_person,
            ),
        ],
    ),
    TableAdapter(
        get_id_query=Queries.GENRE_MODIFIED,
        table="genre",
        index_adapters=[
            IndexAdapter(
                data_class=ElasticFilmData,
                linking_query=Queries.FILM_BY_GENRE,
                get_data_query=Queries.FILMWORK_DATA,
                index=index_movie,
            ),
            IndexAdapter(
                data_class=ElasticGenreData,
                linking_query=None,
                get_data_query=Queries.GENRE_DATA,
                index=index_genre,
            ),
        ],
    ),
]
