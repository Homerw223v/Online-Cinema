import logging
from contextlib import asynccontextmanager
from logging import config as logging_config

import aio_pika
import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from api.v1.notify import notify_router
from core.config import settings
from core.logger import LOGGING, RequestIdFilter
from db import rabbit

if settings.sentry.dsn:
    sentry_sdk.init(**settings.sentry.model_dump())


@asynccontextmanager
async def lifespan(_):
    rabbit.rabbit_connection = await aio_pika.connect_robust(str(settings.rabbit.dsn))
    rabbit.rabbit_channel = await rabbit.rabbit_connection.channel()
    rabbit.rabbit_exchange = await rabbit.rabbit_channel.declare_exchange(name=settings.rabbit.exchange)
    logging_config.dictConfig(LOGGING)
    yield
    await rabbit.rabbit_connection.close()


tags_metadata = [
    {
        "name": "notify",
        "description": "Send notify to user",
    },
]

app = FastAPI(
    root_path=settings.app.root_path,
    title=settings.app.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    openapi_tags=tags_metadata,
    summary=settings.app.project_summary,
    version="0.1",
    lifespan=lifespan,
)

app.include_router(notify_router)


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
