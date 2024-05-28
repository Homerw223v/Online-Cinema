from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    host: str
    port: str

    model_config = SettingsConfigDict(env_prefix="KAFKA_")


class TestSettings(BaseSettings):
    test_base_url: str
    max_time: int = 140
    kafka: KafkaSettings = KafkaSettings()


settings = TestSettings()
