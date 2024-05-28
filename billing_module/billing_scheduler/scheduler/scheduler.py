from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from core.config import settings

scheduler = AsyncIOScheduler()

jobstores = {
    "default": RedisJobStore(
        jobs_key=settings.redis.jobs_key,
        run_times_key=settings.redis.run_times_key,
        host=settings.redis.host,
        port=settings.redis.port,
    ),
}
scheduler.configure(jobstores=jobstores)
