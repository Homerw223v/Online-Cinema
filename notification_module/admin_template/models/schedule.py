from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Information(BaseModel):
    pattern_id: UUID
    worker: str


class RepeatInformation(Information):
    entity_id: UUID
    send_to: str


class ScheduleInformation(RepeatInformation):
    time: datetime


class CrontabSchedule(BaseModel):
    minute: str | int = "*"
    hour: str | int = "*"
    day_of_week: str | int = "*"
    day_of_month: str | int = "*"
    month_of_year: str | int = "*"


class Task(BaseModel):
    task_name: str


class CreatePeriodicTask(Task):
    interval_crontab: CrontabSchedule
    task_information: RepeatInformation


class RedbeatTasks(BaseModel):
    task_name: str = Field(validation_alias="name")
    task: str
    args: list | None
    kwargs: dict | None
    schedule_time: str
    last_run_at: datetime
    total_run_count: int
    enabled: bool
