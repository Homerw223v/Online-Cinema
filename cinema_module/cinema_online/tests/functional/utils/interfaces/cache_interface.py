from abc import ABC, abstractmethod
from typing import Any

from redis.asyncio.client import Redis


class CacheInterface(ABC):
    @abstractmethod
    def __init__(self, client: Any):
        self.client = client

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(self, key: str, value: str, lifetime=300):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def clear_cache(self):
        pass


class RedisCacheInterface(CacheInterface):
    def __init__(self, client: Redis):
        self.client = client

    async def get(self, key: str):
        await self.client.get(key)

    async def set(self, key: str, value: str, lifetime=300):
        await self.client.set(key, value, ex=lifetime)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def clear_cache(self):
        await self.client.flushdb()
