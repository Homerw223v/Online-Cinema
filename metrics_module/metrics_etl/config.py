from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA_")
    host: str
    topic: str


class ClickHouseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLICK_HOUSE_")
    url: HttpUrl


class Settings(BaseSettings):
    batch_size: int = 1000
    delay: int = 30
    click_house: ClickHouseSettings = ClickHouseSettings()
    kafka: KafkaSettings = KafkaSettings()


settings = Settings()
