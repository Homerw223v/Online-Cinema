import http

import redbeat
from celery import schedules
from fastapi import HTTPException
from redbeat.schedulers import RedBeatConfig

from core.config import settings
from models.schedule import CreatePeriodicTask, RedbeatTasks
from schedule import celery


class ScheduleService:
    model = redbeat.RedBeatSchedulerEntry

    async def get_task(self, task_name) -> model | None:
        """
        Retrieve a task by task_name.

        Args:
            task_name (str): The name of the task to retrieve.

        Returns:
            RedBeatSchedulerEntry | None: The task if found, None otherwise.
        """
        try:
            return self.model.from_key(
                key="redbeat:%s" % task_name,
                app=celery.celery_app,
            )
        except KeyError:
            return None

    async def create_task(self, task: CreatePeriodicTask) -> None:
        """
        Create a new task.

        Args:
            task (CreatePeriodicTask): The task details to create.

        Raises:
            HTTPException: If the task already exists.

        Returns:
            None
        """
        if not await self.get_task(task.task_name):
            entry = self.model(
                name=task.task_name,
                task=celery.send_message_to_user_with_celery.s().task,
                schedule=await self.get_interval(task.interval_crontab.model_dump()),
                kwargs=await self.dict_for_json(task.task_information.dict()),
                app=celery.celery_app,
            )
            return entry.save()
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST,
            detail="Task %s already exists" % task.task_name,
        )

    @staticmethod
    async def dict_for_json(dictionary: dict) -> dict:
        dictionary['pattern_id'] = str(dictionary['pattern_id'])
        dictionary['entity_id'] = str(dictionary['entity_id'])
        return dictionary

    @staticmethod
    async def get_interval(crontab_time: dict) -> schedules.crontab:
        """
        Get a crontab schedule from a dictionary.

        Args:
            crontab_time (dict): The crontab schedule details.

        Raises:
            HTTPException: If the crontab schedule is invalid.

        Returns:
            schedules.crontab: The crontab schedule.
        """
        try:
            return schedules.crontab(**crontab_time)
        except ValueError as er:
            raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail=str(er))

    async def get_all_tasks(self) -> list[RedbeatTasks]:
        """
        Get all scheduled tasks.

        Returns:
            list[RedbeatTasks]: A list of scheduled tasks.
        """
        schedule_key: str = RedBeatConfig(celery.celery_app).schedule_key
        redis = redbeat.schedulers.get_redis(celery.celery_app)
        task_names: list = redis.zrange(schedule_key, 0, -1, withscores=False)
        tasks = [
            self.model.from_key(key=task_name, app=celery.celery_app).__dict__
            for task_name in task_names
            if task_name != settings.celery.redbeat_default_task
        ]
        return [
            RedbeatTasks(**task, schedule_time=str(task.get("schedule")))
            for task in tasks
        ]

    async def delete_task(self, task_name: str) -> None:
        """
        Delete a task by task_name.

        Args:
            task_name (str): The name of the task to delete.

        Returns:
            None
        """
        if task := await self.get_task(task_name):
            task.delete()

    async def change_execution_time(self, new_task: CreatePeriodicTask):
        """
        Change the execution time of a task.

        Args:
            new_task (CreatePeriodicTask): The updated task details.
        """
        if task := await self.get_task(new_task.task_name):
            setattr(  # noqa
                task,
                "schedule",
                await self.get_interval(new_task.interval_crontab.model_dump()),
            )  # noqa
            task.save()


async def get_schedule_service():
    """
    Get an instance of ScheduleService.

    Returns:
        ScheduleService: An instance of ScheduleService.
    """
    return ScheduleService()
