from uuid import UUID

from fastapi import APIRouter, Depends

from core.dependencies import user_id_dependency
from models.metric import APIMetricModel, KafkaMetricsModel
from service.base_service import Service
from service.metric_service import get_metric_service

router = APIRouter(
    prefix="/api/v1/metrics",
    tags=["metrics"],
)


@router.post("", description="Receive information about user actions")
async def sent_metrics(
    metrics: APIMetricModel,
    user_id: UUID | None = Depends(user_id_dependency),
    service: Service = Depends(get_metric_service),
) -> None:
    """
    Endpoint to receive information about user actions to send metrics to the broker.

    Args:
        metrics (APIMetricModel): The metric model containing information about user actions.
        service (Service): The metric service to send the metrics.
        user_id (Optional[UUID]): Return user id or None.

    Returns:
        HTTPStatus: The HTTP status indicating the success of the operation.
    """
    kafka_metrics = KafkaMetricsModel(user_id=user_id, **metrics.model_dump())
    await service.send_message(kafka_metrics)
