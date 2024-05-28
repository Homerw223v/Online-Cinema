from datetime import date, datetime, time, timedelta, timezone

from jinja2 import Template

from config import ScheduleSettings, settings
from models import User


class UserTime:
    def __init__(self, user: User):
        tz = timezone(timedelta(minutes=user.timezone_min))
        self.current_time = datetime.now(tz=tz)

    def permission_to_send(self, schedule: ScheduleSettings):
        return schedule.start <= time(hour=self.current_time.hour, minute=self.current_time.minute) <= schedule.stop

    def get_sending_delay(self, schedule: ScheduleSettings):
        return (datetime.combine(date.today(), schedule.start) - self.current_time).seconds


class EmailMessage:
    def __init__(self, user, pattern, data):
        self.from_email = settings.email.sender
        self.to_email = user.email
        self.subject = Template(pattern.subject).render(**user.model_dump(), **data)
        self.content = Template(pattern.content).render(**user.model_dump(), **data)
