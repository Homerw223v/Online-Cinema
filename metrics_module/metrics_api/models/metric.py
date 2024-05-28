from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class APIMetricModel(BaseModel):
    url: str
    action: str
    information: str


class KafkaMetricsModel(APIMetricModel):
    user_id: UUID | None = None
    timestamp: datetime = datetime.utcnow()
    url: str
    action: str
    information: str
