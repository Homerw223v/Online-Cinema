import os
from pydantic import HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    dsn: PostgresDsn


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    login_url: HttpUrl
    refresh_url: HttpUrl
    username: str
    password: str


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool = bool(os.getenv("LOGSTASH_ENABLE"))
    model_config = SettingsConfigDict(env_prefix="logstash_")


class PatternSettings(BaseSettings):
    tomorrow_auto_pay: str
    no_active_card: str
    no_auto_pay: str

    model_config = SettingsConfigDict(env_prefix="pattern_")


class RedisSettings(BaseSettings):
    host: str
    port: int
    jobs_key: str
    run_times_key: str

    model_config = SettingsConfigDict(env_prefix="redis_")


class JobSettings(BaseSettings):
    notification_url: str
    payment_status: str
    auto_payment: str

    model_config = SettingsConfigDict(env_prefix="job_")


class AppSettings:
    postgres = PostgresSettings()
    redis = RedisSettings()
    auth = AuthSettings()
    logstash = LogstashSettings()
    job = JobSettings()
    pattern = PatternSettings()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    x_request_id = os.getenv("SERVICE_X_REQUEST_ID")


settings = AppSettings()
