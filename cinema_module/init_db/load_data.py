import logging
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import astuple, dataclass, fields
from typing import Any, Generator, Union

import psycopg2
from logger import create_logger
from psycopg2.extensions import connection as _connection
from psycopg2.extensions import cursor
from psycopg2.extras import DictCursor
from settings import BATCH_SIZE, DSL, SQL_DB_PATH
from utils import (
    FilmWork,
    Genre,
    GenreFilmWork,
    Person,
    PersonFilmWork,
    SourceFilmWork,
    SourceGenre,
    SourceGenreFilmWork,
    SourcePerson,
    SourcePersonFilmWork,
)

PG_CLASSES = Union[FilmWork, Genre, Person, PersonFilmWork, GenreFilmWork]
SQL_CLASSES_TYPE = type[SourceFilmWork | SourceGenre | SourcePerson | SourcePersonFilmWork | SourceGenreFilmWork]


@dataclass
class TableInfo:
    table_name: str
    table_class: SQL_CLASSES_TYPE


tables_list = [
    TableInfo("film_work", SourceFilmWork),
    TableInfo("genre", SourceGenre),
    TableInfo("genre_film_work", SourceGenreFilmWork),
    TableInfo("person", SourcePerson),
    TableInfo("person_film_work", SourcePersonFilmWork),
]


@contextmanager
def conn_context(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@contextmanager
def pg_conn_context(**kwargs: Any) -> Generator[_connection, None, None]:
    connection = psycopg2.connect(**kwargs)
    try:
        yield connection
    except Exception as ex:
        connection.rollback()
        raise ex
    finally:
        connection.close()


def batch_insert(
    pg_cursor: cursor,
    table_name: str,
    postgres_data_list: list[PG_CLASSES],
    logger: logging.Logger,
) -> None:
    if not postgres_data_list:
        return
    column_names = ", ".join([field.name for field in fields(postgres_data_list[0])])
    col_count = ", ".join(["%s"] * len(fields(postgres_data_list[0])))
    values_data = ",".join(pg_cursor.mogrify(f"({col_count})", astuple(item)).decode() for item in postgres_data_list)
    query = f"INSERT INTO content.{table_name} ({column_names}) VALUES {values_data} ON CONFLICT (id) DO NOTHING"
    try:
        pg_cursor.execute(query)
    except Exception as ex:
        logger.info(f'Can\'t insert data to table "{table_name}": {ex}')


def load_from_sqlite(
    sqlite_conn: sqlite3.Connection,
    pg_conn: _connection,
    logger: logging.Logger,
) -> None:
    """Основной метод загрузки данных из SQLite в Postgres"""
    with closing(sqlite_conn.cursor()) as curs:
        with pg_conn.cursor() as pg_cursor:
            for table in tables_list:
                try:
                    request = curs.execute(f"SELECT * FROM {table.table_name};")
                except sqlite3.OperationalError as ex:
                    logger.info(f'Error on select table "{table.table_name}": {ex}')
                    continue
                while batch_data := request.fetchmany(BATCH_SIZE):
                    postgres_data_list = [table.table_class(**item).convert_to_postgres_class() for item in batch_data]
                    batch_insert(
                        pg_cursor=pg_cursor,
                        table_name=table.table_name,
                        postgres_data_list=postgres_data_list,
                        logger=logger,
                    )
                pg_conn.commit()


if __name__ == "__main__":
    logger = create_logger("move_bd_data", logging.INFO)
    with conn_context(SQL_DB_PATH) as sqlite_conn:
        with pg_conn_context(**DSL, cursor_factory=DictCursor) as pg_conn:
            load_from_sqlite(sqlite_conn, pg_conn, logger)
