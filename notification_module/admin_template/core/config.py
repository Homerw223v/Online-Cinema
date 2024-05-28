import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="celery_")
    broker_dsn: str
    notification_user: str
    notification_group: str
    redbeat_default_task: str = "redbeat:celery.backend_cleanup"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: str


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    root_path: str
    project_name: str
    project_summary: str


class UserInfoSettings(BaseSettings):
    user_info_url: HttpUrl


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    login_url: HttpUrl
    refresh_url: HttpUrl
    username: str
    password: str


class AuthRedirect(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    base_url: HttpUrl
    login_redirect_url: HttpUrl


class SentrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="sentry_", extra="allow")
    dsn: HttpUrl | None = None
    enable_tracing: bool = False


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool = bool(os.getenv("LOGSTASH_ENABLE"))
    model_config = SettingsConfigDict(env_prefix="logstash_")


class MongoDBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mongodb_")
    dsn: str


class AppSettings:
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    auth = AuthSettings()
    auth_redirect = AuthRedirect()
    redis = RedisSettings()
    url = UserInfoSettings()
    app = FastApiSettings()
    mongo_db = MongoDBSettings()
    jaeger = JaegerSetting()
    sentry = SentrySettings()
    celery = CelerySettings()
    logstash = LogstashSettings()
    service_role: str = "service"


settings = AppSettings()


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.app.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
        BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())),
    )  # noqa!


if settings.tracer_enable:
    configure_tracer()
