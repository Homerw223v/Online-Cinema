"""Settings for sqlite to postgres module."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresFrom(BaseSettings):
    dbname: str
    user: str
    password: str
    host: str
    port: str

    model_config = SettingsConfigDict(env_prefix="from_postgres_")


class PostgresTo(BaseSettings):
    dbname: str
    user: str
    password: str
    host: str
    port: str

    model_config = SettingsConfigDict(env_prefix="to_postgres_")


class ETLSettings(BaseSettings):
    batch_size: int
    table_name_to: str
    query_from: str
    sleep_time: int


class Settings:
    from_postgres = PostgresFrom()
    to_postgres = PostgresTo()
    etl_settings = ETLSettings()


settings = Settings()
