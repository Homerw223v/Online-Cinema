from models import SingleMessage, GroupMessage
from json import loads # noqa!

import asyncio

import aio_pika
from models import ProcessingMessage, Role, WorkerType
from config import settings
from services.auth import AuthService
from services.message_db import MongoMessageStorage


async def main() -> None:
    async def process_message(
        message: aio_pika.abc.AbstractIncomingMessage,
    ) -> None:
        async with message.process():
            msg = SingleMessage(incoming_msg_id=message.message_id, **loads(message.body.decode()))
            message_id = await storage.insert(msg)
            processing_message = ProcessingMessage(
                request_id=msg.request_id,
                msg_id=message_id,
                user_id=msg.user_id,
                pattern_id=msg.pattern_id,
                urgently=msg.urgently,
            )
            routing_key = msg.worker if msg.worker == WorkerType.email else f"{msg.worker}.{msg.user_id}"
            await exchange.publish(
                aio_pika.Message(body=processing_message.model_dump_json().encode()),
                routing_key=routing_key,
            )

    async def process_group_messages(
        message: aio_pika.abc.AbstractIncomingMessage,
    ) -> None:
        async with message.process():
            group_msg = GroupMessage.model_validate_json(message.body.decode())
            auth_service.request_id = group_msg.request_id
            group_info_url = f'{settings.url.group_info_url}{group_msg.group_id}'
            group_members = (await auth_service.get_query(group_info_url, Role)).users
            for user_id in group_members:
                msg = SingleMessage(
                    request_id=group_msg.request_id,
                    incoming_msg_id=message.message_id,
                    pattern_id=group_msg.pattern_id,
                    user_id=user_id,
                    data=group_msg.data,
                    worker=group_msg.worker,
                )
                message_id = await storage.insert(msg)
                processing_message = ProcessingMessage(
                    request_id=group_msg.request_id,
                    msg_id=message_id,
                    user_id=user_id,
                    pattern_id=group_msg.pattern_id,
                    urgently=group_msg.urgently,
                )
                routing_key = msg.worker if msg.worker == WorkerType.email else f"{msg.worker}.{user_id}"
                await exchange.publish(
                    aio_pika.Message(body=processing_message.model_dump_json().encode()),
                    routing_key=routing_key,
                )

    broker_connection = await aio_pika.connect_robust(str(settings.broker.dsn))
    storage = MongoMessageStorage(str(settings.mongo_db.dsn), settings.mongo_db.db_name)
    await storage.init_model()
    auth_service = AuthService(**settings.auth.model_dump()).connections()

    channel = await broker_connection.channel()
    await channel.set_qos(prefetch_count=100)
    exchange = await channel.declare_exchange(settings.broker.worker_exchange_name)
    await channel.declare_exchange(name=settings.broker.incoming_message_exchange_name)
    single_message_queue = await channel.declare_queue(settings.broker.single_message_queue_name, auto_delete=True)
    await single_message_queue.bind(
        exchange=settings.broker.incoming_message_exchange_name, routing_key=settings.broker.single_message_routing_key,
    )
    await single_message_queue.consume(process_message)

    group_message_queue = await channel.declare_queue(settings.broker.group_message_queue_name, auto_delete=True)
    await group_message_queue.bind(
        exchange=settings.broker.incoming_message_exchange_name, routing_key=settings.broker.group_message_routing_key,
    )
    await group_message_queue.consume(process_group_messages)

    try: # noqa!
        await asyncio.Future()
    finally:
        await broker_connection.close()
        await auth_service.close()


if __name__ == "__main__":
    asyncio.run(main())
