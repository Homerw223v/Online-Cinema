import os

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: str
    project_name: str = "Billing Admin"
    project_summary: str = ""
    root_path: str
    sqladmin_secret_key: str


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    dsn: PostgresDsn


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool = bool(os.getenv("LOGSTASH_ENABLE"))
    model_config = SettingsConfigDict(env_prefix="logstash_")


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    base_url: HttpUrl
    login_redirect_url: HttpUrl


class JWTAuthSettings(BaseSettings):
    authjwt_secret_key: str
    lifetime: int
    algorithm: str

    model_config = SettingsConfigDict(env_prefix="jwt_")


class settings:
    redis = RedisSettings()
    postgres = PostgresSettings()
    app = FastApiSettings()
    auth = AuthSettings()
    jaeger = JaegerSetting()
    logstash = LogstashSettings()
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auth_jwt = JWTAuthSettings()


settings = settings()


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.app.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())),
    )


if settings.tracer_enable:
    configure_tracer()
