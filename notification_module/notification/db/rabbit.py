from typing import Any
import aio_pika

rabbit_connection: Any
rabbit_channel: aio_pika.abc.AbstractChannel
rabbit_exchange: aio_pika.exchange.AbstractExchange


def get_rabbit_exchange() -> aio_pika.exchange.AbstractExchange:
    return rabbit_exchange  # noqa
