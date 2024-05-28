"""Transferring data from sqlite3 to postgres."""

from contextlib import contextmanager
from time import sleep

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from postgres_model import PostgresETL
from log import logger
from settings import settings
import backoff


@contextmanager
def conn_context_postgres(dsn: dict):
    """
    Connect to postgres database.

    Args:
        dsn (dict): Data source name

    Yields:
        conn: Connection object
    """
    conn: _connection = psycopg2.connect(**dsn, cursor_factory=DictCursor)
    yield conn
    conn.close()


@backoff.on_exception(backoff.expo, psycopg2.OperationalError, max_value=10, logger=logger, raise_on_giveup=False)
def transfer_data() -> None:
    """
    Transfer data from SQLite to Postgres.

    Returns: None
    """
    with (
        conn_context_postgres(
            settings.from_postgres.model_dump(),
        ) as postgres_from,
        conn_context_postgres(settings.to_postgres.model_dump()) as postgres_to,
    ):
        while True: # noqa
            postgres_etl: PostgresETL = PostgresETL(postgres_from, postgres_to)
            postgres_data: list = postgres_etl.extract_data()
            postgres_etl.load_data(postgres_data)
            logger.info("ETL completed")
            sleep(settings.etl_settings.sleep_time)


if __name__ == "__main__":
    transfer_data()
