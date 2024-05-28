import uuid

from psycopg2.extensions import connection as _connection
from psycopg2.extras import execute_batch
from psycopg2 import DataError, IntegrityError, OperationalError
from dataclasses import asdict, dataclass, fields

from settings import settings
from tables import Subscriptions
from log import logger


class PostgresETL:
    def __init__(self, pg_from, pg_to):
        self.pg_from: _connection = pg_from
        self.pg_to: _connection = pg_to

    def extract_data(self):
        """
        Extract data from the source database in batches.

        Yields:
            films (list): List of Subscriptions objects extracted from the source database.
        """
        with self.pg_from.cursor("subscriptions_from_cursor") as cur:
            cur.execute(settings.etl_settings.query_from)
            query_result = cur.fetchall()
            return [Subscriptions(**subscription) for subscription in query_result]

    def load_data(self, data):
        """
        Load data into the destination database and update 'is_active' flag for missing records.

        Args:
            data (generator): Generator yielding lists of Subscriptions objects.
        """
        with self.pg_to.cursor() as cur:
            try:  # noqa
                cur.execute(
                    f"""UPDATE content.{settings.etl_settings.table_name_to}
                        SET is_active = false
                        WHERE {settings.etl_settings.table_name_to}.id NOT IN ('{uuid.uuid4()}')""",
                )
                if data:
                    query: str = self._create_sql_query(data[0])
                    rows: list = [asdict(record) for record in data]
                    execute_batch(cur, query, rows)
            except (OperationalError, DataError, IntegrityError) as ut:
                logger.error(ut)
            else:
                self.pg_to.commit()

    @staticmethod
    def _create_sql_query(row: dataclass) -> str:
        """
        Create SQL query to insert rows in Postgres.

        Args:
            row (dataclass): Class with column names

        Returns:
            query (str): Query string
        """
        col_names: str = ", ".join([field.name for field in fields(row)])
        placeholders: str = ", ".join(f"%({field.name})s" for field in fields(row))
        return f"""INSERT INTO content.{settings.etl_settings.table_name_to} ({col_names})
                   VALUES ({placeholders})
                   ON CONFLICT (id) DO UPDATE
                   SET name = EXCLUDED.name, is_active = EXCLUDED.is_active"""
