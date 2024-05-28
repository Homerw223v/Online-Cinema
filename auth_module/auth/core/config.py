import os
from datetime import timedelta
from functools import cached_property
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import HttpUrl, PostgresDsn, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: str
    project_name: str = "Auth Service"
    project_summary: str = ""
    root_path: str


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="auth_")
    cors_allow_origins_list: list[str] = [""]
    login_method: str
    email_confirm_url: str


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    dsn: PostgresDsn


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="notification_")
    email_pattern: UUID | None = None
    email_confirm_endpoint: HttpUrl | None = None
    email_confirm_ttl_min: int = 15

    @model_validator(mode='before')
    def check_full_model(cls, values):
        v1, v2 = values.get('email_pattern'), values.get('email_confirm_endpoint')
        if any([v1, v2]) is True and all([v1, v2]) is False:
            raise ValueError('there is not enough data for notification')
        return values


class JwtSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jwt_")
    authjwt_secret_key: str
    access_token_expires_min: int = 30
    refresh_token_expires_hours: int = 24
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access"}

    @computed_field
    @cached_property
    def authjwt_access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.access_token_expires_min)

    @computed_field
    @cached_property
    def authjwt_refresh_token_expires(self) -> timedelta:
        return timedelta(hours=self.refresh_token_expires_hours)


class BaseOauth(BaseSettings):
    client_id: str
    client_secret: str
    dialog_oauth_url: HttpUrl
    token_oauth_url: HttpUrl
    user_info_url: HttpUrl
    redirect_url: HttpUrl | None = None
    scope: str | None = None


class OauthYandex(BaseOauth):
    model_config = SettingsConfigDict(env_prefix="oauth_yandex_")
    dialog_oauth_url: HttpUrl = "https://oauth.yandex.ru/authorize"
    token_oauth_url: HttpUrl = "https://oauth.yandex.ru/token"
    user_info_url: HttpUrl = "https://login.yandex.ru/info"


class JaegerSetting(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="jaeger_")
    agent_host_name: str
    agent_port: int = 6831


class OauthVk(BaseOauth):
    model_config = SettingsConfigDict(env_prefix="oauth_vk_")
    dialog_oauth_url: HttpUrl = "https://oauth.vk.com/authorize"
    token_oauth_url: HttpUrl = "https://oauth.vk.com/access_token"
    user_info_url: HttpUrl = "https://api.vk.ru/method/account.getProfileInfo"
    redirect_url: HttpUrl
    scope: str | None = "4194304"  # email


class LogstashSettings(BaseSettings):
    host: str
    port: int
    enable: bool
    model_config = SettingsConfigDict(env_prefix="logstash_")


class SentrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="sentry_", extra="allow")
    dsn: HttpUrl | None = None
    enable_tracing: bool = False


class AppSettings:
    redis = RedisSettings()
    postgres = PostgresSettings()
    jwt = JwtSettings()
    auth = AuthSettings()
    app = FastApiSettings()
    oauth_yandex = OauthYandex()
    oauth_vk = OauthVk()
    jaeger = JaegerSetting()
    tracer_enable = bool(int(os.getenv("TRACER_ENABLE")))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logstash = LogstashSettings()
    sentry: SentrySettings = SentrySettings()
    service_role: str = 'service'
    notification = NotificationSettings()


settings = AppSettings()


@AuthJWT.load_config
def get_config():
    settings.jwt.model_dump()  # serialize computed_field ! NOT DELETE
    return settings.jwt


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.app.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
        BatchSpanProcessor(JaegerExporter(**settings.jaeger.model_dump())),
    )


if settings.tracer_enable:
    configure_tracer()
