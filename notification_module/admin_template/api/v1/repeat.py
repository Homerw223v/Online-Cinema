import http

from core.config import settings
from core.dependencies import check_access_endpoint, token_payload_dep
from models.models import TokenInfo
from models.schedule import CreatePeriodicTask, RedbeatTasks
from fastapi import APIRouter, Depends, HTTPException
from service.schedule_service import get_schedule_service, ScheduleService

router = APIRouter(
    prefix="/api/v1/schedule/repeat",
    tags=["schedule"],
)


@router.post("", description="Create a new task")
@check_access_endpoint(roles={settings.service_role})
async def create_schedule_task(
    task: CreatePeriodicTask,
    service: ScheduleService = Depends(get_schedule_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> http.HTTPStatus:
    await service.create_task(task)
    return http.HTTPStatus.CREATED


@router.get("", description="Retrieve all tasks")
@check_access_endpoint(roles={settings.service_role})
async def get_all_schedule_tasks(
    service: ScheduleService = Depends(get_schedule_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> list[RedbeatTasks]:
    return await service.get_all_tasks()


@router.get("/{task_name}", description="Retrieve a single task")
@check_access_endpoint(roles={settings.service_role})
async def get_single_task(
    task_name: str,
    service: ScheduleService = Depends(get_schedule_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
):
    task = await service.get_task(task_name)
    return (
        RedbeatTasks(**task.__dict__, schedule_time=str(task.__dict__.get("schedule")))
        if task
        else HTTPException(status_code=http.HTTPStatus.NOT_FOUND)
    )


@router.delete("", description="Delete task")
@check_access_endpoint(roles={settings.service_role})
async def disable_task(
    task_name: str,
    service: ScheduleService = Depends(get_schedule_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> http.HTTPStatus:
    await service.delete_task(task_name)
    return http.HTTPStatus.OK


@router.put("", description="Change time of the execution of the task")
@check_access_endpoint(roles={settings.service_role})
async def change_interval_time(
    task: CreatePeriodicTask,
    service: ScheduleService = Depends(get_schedule_service),
    token_payload: TokenInfo = Depends(token_payload_dep),
):
    await service.change_execution_time(task)
    return http.HTTPStatus.OK
