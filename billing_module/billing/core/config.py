from dotenv import load_dotenv

load_dotenv()


import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


class YooKassaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="yookassa_")
    account_id: str
    secret_key: str
    redirect_url: HttpUrl


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: str
    project_name: str = "Auth Service"
    project_summary: str = ""
    root_path: str


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    base_url: HttpUrl
    login_redirect_url: HttpUrl


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    dsn: PostgresDsn


class BaseOauth(BaseSettings):
    client_id: str
    client_secret: str
    dialog_oauth_url: HttpUrl
    token_oauth_url: HttpUrl
    user_info_url: HttpUrl
    redirect_url: HttpUrl | None = None
    scope: str | None = None


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool = bool(os.getenv("LOGSTASH_ENABLE"))
    model_config = SettingsConfigDict(env_prefix="logstash_")


class SentrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="sentry_", extra="allow")
    dsn: HttpUrl | None = None
    enable_tracing: bool = False


class AppSettings:
    yookassa = YooKassaSettings()
    redis = RedisSettings()
    postgres = PostgresSettings()
    auth = AuthSettings()
    jaeger = JaegerSetting()
    app = FastApiSettings()
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logstash = LogstashSettings()
    sentry: SentrySettings = SentrySettings()


settings = AppSettings()


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.app.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
        BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())),
    )


if settings.tracer_enable:
    configure_tracer()
