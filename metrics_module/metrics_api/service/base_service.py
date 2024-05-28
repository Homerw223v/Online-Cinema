from abc import ABC, abstractmethod

from models.metric import KafkaMetricsModel


class Service(ABC):
    @abstractmethod
    async def send_message(self, metric: KafkaMetricsModel) -> None:
        """
        Sends a message with metrics to the broker.

        Args:
            metric (MetricModel): The metric model to be sent.

        Returns:
            None
        """
        pass
