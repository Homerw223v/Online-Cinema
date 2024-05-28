from aio_pika.abc import AbstractChannel

broker_chanel: AbstractChannel


async def get_broker_chanel():
    return broker_chanel # noqa!
