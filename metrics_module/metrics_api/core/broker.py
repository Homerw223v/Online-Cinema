from aiokafka import AIOKafkaProducer

kafka_producer: AIOKafkaProducer | None = None


async def get_kafka() -> AIOKafkaProducer:
    return kafka_producer
