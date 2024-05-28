import os

from dotenv import load_dotenv

load_dotenv()


SQL_DB_PATH = os.getenv("SQL_DB_PATH", "db.sqlite")

DSL = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", 5432),
}

BATCH_SIZE = 1000
