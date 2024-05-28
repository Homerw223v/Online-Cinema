from redis import Redis

redis_interface: Redis


async def get_db_client() -> Redis:
    return redis_interface  # noqa
