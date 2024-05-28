import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="rabbit_")
    dsn: AmqpDsn
    exchange: str


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: str
    project_name: str = "Notification Service"
    project_summary: str = ""
    root_path: str


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
    rabbit = RabbitSettings()
    app = FastApiSettings()
    jaeger = JaegerSetting()
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
