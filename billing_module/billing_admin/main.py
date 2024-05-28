import logging
from contextlib import asynccontextmanager
from logging import config as logging_config

from api.v1 import subscriptions, users
from core.config import settings
from core.logger import LOGGING, RequestIdFilter
from db import postgres
from db.sqladmin import (
    HistoryAdmin,
    SubscribersAdmin,
    TariffsAdmin,
    TransactionsAdmin,
    UserCardAdmin,
    UserFreezeSubscriptionAdmin,
    UserSubscriptionAdmin,
)
from db.sqladminauth import AdminAuth
from redis import asyncio as redis_async
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from db import redis
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqladmin import Admin


@asynccontextmanager
async def lifespan(_):
    logging_config.dictConfig(LOGGING)
    redis.redis_interface = redis_async.from_url(
        str(settings.redis.dsn),  # type: ignore
        encoding="utf8",
        decode_responses=True,
    )
    await postgres.create_database()
    yield
    await redis.redis_interface.close()
    # await postgres.purge_database()


app = FastAPI(
    root_path=settings.app.root_path,  # noqa
    title=settings.app.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    summary=settings.app.project_summary,
    version="0.1",
    lifespan=lifespan,
)

app.include_router(users.user_router)
app.include_router(subscriptions.subscription_router)

sql_auth = AdminAuth(secret_key=settings.app.sqladmin_secret_key)
sqladmin = Admin(app, postgres.engine, authentication_backend=sql_auth)

sqladmin.add_view(TariffsAdmin)
sqladmin.add_view(TransactionsAdmin)
sqladmin.add_view(UserSubscriptionAdmin)
sqladmin.add_view(UserFreezeSubscriptionAdmin)
sqladmin.add_view(SubscribersAdmin)
sqladmin.add_view(HistoryAdmin)
sqladmin.add_view(UserCardAdmin)


@app.middleware("http")
async def before_request(request: Request, call_next):
    response = await call_next(request)
    if settings.tracer_enable:
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
    return response


@app.middleware("http")
async def add_log_filter(request: Request, call_next):
    for log_type in ("access", "error"):
        logger = logging.getLogger("uvicorn.%s" % (log_type,))
        logger.addFilter(RequestIdFilter(request))
    return await call_next(request)


@app.get("/healthcheck")
async def health() -> None:
    return  # noqa


FastAPIInstrumentor.instrument_app(app, excluded_urls="healthcheck")
