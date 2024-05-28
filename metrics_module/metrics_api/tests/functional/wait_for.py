import asyncio
import logging

import backoff
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from settings import settings

logger = logging.getLogger()


@backoff.on_exception(
    backoff.fibo,
    (KafkaConnectionError,),
    max_value=10,
    max_time=settings.max_time,
)
async def wait_for_kafka():
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=[
            "%s:%s" % (settings.kafka.host, settings.kafka.port),
        ],
    )
    async with kafka_producer as producer:
        await producer.start()


if __name__ == "__main__":
    asyncio.run(wait_for_kafka())
