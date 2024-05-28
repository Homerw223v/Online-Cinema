import os

import dotenv
from functional.logger import LOGGING
from pydantic import HttpUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv()


# Настройки Redis
class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    dsn: RedisDsn


# Настройки Elasticsearch
class ElasticSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="elastic_")
    base_url: HttpUrl


# Настройки Elasticsearch
class FastApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fastapi_")
    host: HttpUrl
    root_path: str


class AppSettings:
    elastic = ElasticSettings()
    redis = RedisSettings()
    fast_api = FastApiSettings()
    logging = LOGGING
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


settings = AppSettings()
