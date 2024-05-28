import asyncio
from operator import attrgetter

import aio_pika

from config import settings
from models import Pattern, ProcessingMessage, User
from sender import EmailSender
from services.auth import AuthService
from services.mongo_db import MongoMessageStorage
from utils import EmailMessage, UserTime


async def main() -> None:  # noqa!
    async def process_message(
        message: aio_pika.abc.AbstractIncomingMessage,
    ) -> None:
        async with message.process():
            broker_msg = ProcessingMessage.model_validate_json(message.body.decode())
            auth_service.request_id = broker_msg.request_id
            user_info_url = f"{settings.url.user_info_url}{broker_msg.user_id}"
            user = await auth_service.get_query(user_info_url, User)
            user_time = UserTime(user)
            if broker_msg.urgently or (user.notice_email and user_time.permission_to_send(settings.schedule)):
                pattern_info_url = f"{settings.template.url}{broker_msg.pattern_id}"
                pattern = await auth_service.get_query(pattern_info_url, Pattern)
                if pattern.aggregate:
                    msg_list = await storage.get_messages(broker_msg.user_id, broker_msg.pattern_id)
                    data = {"messages": [msg.data for msg in msg_list]}
                else:
                    msg = await storage.get_by_id(broker_msg.msg_id)
                    msg_list = [msg]
                    data = msg.data
                email_msg = EmailMessage(user, pattern, data)
                await sender.send_message(email_msg)
                await storage.set_state_sent(list(map(attrgetter("id"), msg_list)))
            elif user.notice_email:
                delay = user_time.get_sending_delay(settings.schedule)
                await delayed_exchange.publish(
                    aio_pika.Message(body=message.body, message_id=message.message_id, headers={"x-delay": delay}),
                    routing_key=settings.broker.email_worker_routing_key,
                )

    broker_connection = await aio_pika.connect_robust(str(settings.broker.dsn))
    auth_service = AuthService(**settings.auth.model_dump()).connections()
    storage = MongoMessageStorage(str(settings.mongo_db.dsn), settings.mongo_db.db_name)
    sender = EmailSender(**settings.email.model_dump())
    await sender.connect()
    await storage.init_model()

    channel: aio_pika.abc.AbstractRobustChannel = await broker_connection.channel()
    await channel.set_qos(prefetch_count=1000)
    delayed_exchange = await channel.declare_exchange(
        settings.broker.delayed_exchange_name,
        type="x-delayed-message",
        arguments={"x-delayed-type": "direct"},
    )
    queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
        settings.broker.email_worker_queue_name,
        auto_delete=True,
    )
    await queue.bind(
        exchange=settings.broker.worker_exchange_name,
        routing_key=settings.broker.email_worker_routing_key,
    )
    await queue.consume(process_message)

    await queue.bind(
        exchange=settings.broker.delayed_exchange_name,
        routing_key=settings.broker.email_worker_routing_key,
    )

    try:  # noqa!
        await asyncio.Future()
    finally:
        await broker_connection.close()
        await auth_service.close()
        await sender.close()


if __name__ == "__main__":
    asyncio.run(main())
