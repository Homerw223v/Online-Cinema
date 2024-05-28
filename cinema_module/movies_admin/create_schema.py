import os

import psycopg
from dotenv import load_dotenv

if __name__ == "__main__":
    if not os.getenv("EXTERNAL_ENV"):
        load_dotenv()

    pg_connection_dict = {
        "dbname": os.getenv("PG_DB_NAME"),
        "user": os.getenv("PG_DB_USER"),
        "password": os.getenv("PG_DB_PASSWORD"),
        "port": os.getenv("PG_DB_PORT", "5432"),
        "host": os.getenv("PG_DB_HOST", "127.0.0.1"),
    }
    with psycopg.Connection.connect(**pg_connection_dict) as connection:
        with connection.cursor() as cursor:
            sql = 'CREATE SCHEMA IF NOT EXISTS "movies_admin"'
            cursor.execute(sql)
