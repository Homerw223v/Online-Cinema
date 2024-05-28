import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


# Настройки Redis
class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


# Настройки Elasticsearch
class ElasticSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="elastic_")
    base_url: HttpUrl


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    base_url: HttpUrl
    login_redirect_url: HttpUrl
    login_url: HttpUrl
    refresh_url: HttpUrl
    username: str
    password: str


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: str
    project_name: str = "Auth Service"
    project_summary: str = ""
    root_path: str = ""
    check_trace_id: bool = True


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool = bool(os.getenv("LOGSTASH_ENABLE"))
    model_config = SettingsConfigDict(env_prefix="logstash_")


class BillingService(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="billing_")
    user_subscription_list_url: HttpUrl


class AppSettings:
    elastic = ElasticSettings()
    redis = RedisSettings()
    auth = AuthSettings()
    logstash = LogstashSettings()
    jaeger = JaegerSetting()
    app = FastApiSettings()
    billing = BillingService()
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


settings = AppSettings()


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.app.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())))


if settings.tracer_enable:
    configure_tracer()
