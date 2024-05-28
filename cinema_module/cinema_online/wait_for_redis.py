import backoff
from redis import Redis

from core.config import settings


@backoff.on_exception(backoff.expo, exception=Exception, max_value=120)
def check_redis(redis_settings):
    client = Redis.from_url(str(redis_settings.dsn))
    if not client.ping():
        client.close()
        raise ConnectionError


if __name__ == "__main__":
    check_redis(settings.redis)
