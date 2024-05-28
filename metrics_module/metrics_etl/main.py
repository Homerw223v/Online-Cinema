import asyncio
import json
from itertools import chain

import backoff
from aiochclient import ChClient
from aiohttp import ClientSession
from aiokafka import AIOKafkaConsumer

from config import settings


@backoff.on_exception(backoff.expo, exception=Exception, max_value=120)  # noqa!
async def main():
    async with ClientSession() as session:
        client = ChClient(session, str(settings.click_house.url))
        assert await client.is_alive()
        async for batch in kafka_extractor(delay=settings.delay, size=settings.batch_size):
            await client.execute(
                "INSERT INTO default.metrics (user_id, timestamp, url, action, information) VALUES",
                *batch,
            )


async def kafka_extractor(delay=10, size=1000):
    async with AIOKafkaConsumer(settings.kafka.topic, bootstrap_servers=settings.kafka.host) as consumer:
        while True:  # noqa!
            batch = await consumer.getmany(timeout_ms=delay * 1000, max_records=size)
            yield (
                tuple(json.loads(record.value.decode()).values()) for record in chain.from_iterable(batch.values())
            )  # noqa!


asyncio.run(main())
