from aiokafka import AIOKafkaProducer
from fastapi import Depends

from core.broker import get_kafka
from models.metric import KafkaMetricsModel
from service.base_service import Service


class MetricService(Service):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self.producer = producer

    async def send_message(self, metric: KafkaMetricsModel) -> None:
        await self.producer.send_and_wait(
            topic="metrics",
            value=str(metric.model_dump_json()).encode("utf-8"),
        )


def get_metric_service(
    kafka: AIOKafkaProducer = Depends(get_kafka),
) -> MetricService:
    """
    Function to get an instance of the FilmService.

    Args:
        kafka (AIOKafkaProducer): An instance of the AIOKafkaProducer class.

    Returns:
        MetricService: An instance of the MetricService.
    """
    return MetricService(kafka)
