import os
from datetime import time
from typing import Callable, Type

import backoff
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import AmqpDsn, BaseModel, HttpUrl, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo.errors import AutoReconnect

load_dotenv()


class ScheduleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="schedule_")
    start: time
    stop: time


class BrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="broker_")
    dsn: AmqpDsn
    worker_exchange_name: str = "worker_exchange"
    delayed_exchange_name: str = "delayed_exchange"
    email_worker_queue_name: str = "email_worker_queue"
    email_worker_routing_key: str = "email"


class BackoffSettings(BaseModel):
    wait_gen: Callable = backoff.constant
    exception: Type[Exception] = AutoReconnect
    jitter: Callable = backoff.random_jitter
    interval: float = 0.5
    max_time: float = 2


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    login_url: HttpUrl
    refresh_url: HttpUrl
    username: str
    password: str


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool
    model_config = SettingsConfigDict(env_prefix="logstash_")


class MongoDBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mongodb_")
    dsn: MongoDsn
    db_name: str


class TemplateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="template_")
    url: HttpUrl


class UserInfoSettings(BaseSettings):
    user_info_url: HttpUrl
    group_info_url: HttpUrl


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="email_")
    host: str
    port: int
    sender: str


class AppSettings:
    service_name = os.getenv("SERVICE_NAME")
    email = EmailSettings()
    mongo_db = MongoDBSettings()
    auth = AuthSettings()
    schedule = ScheduleSettings()
    logstash = LogstashSettings()
    jaeger = JaegerSetting()
    broker = BrokerSettings()
    template = TemplateSettings()
    url = UserInfoSettings()
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


settings = AppSettings()


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.service_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())))


if settings.tracer_enable:
    configure_tracer()
