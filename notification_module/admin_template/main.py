import logging
from contextlib import asynccontextmanager
from logging import config as logging_config

import sentry_sdk
from beanie import init_beanie
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from api.v1 import pattern_admin, schedule, repeat
from core.config import settings
from core.logger import LOGGING, RequestIdFilter
from database import mongo_db
from models.models import MongoPatternModel

if settings.sentry.dsn:
    sentry_sdk.init(**settings.sentry.model_dump())


@asynccontextmanager
async def lifespan(_):
    logging_config.dictConfig(LOGGING)
    mongo_db.mongo = AsyncIOMotorClient(settings.mongo_db.dsn)
    await init_beanie(
        database=mongo_db.mongo.db_name,
        document_models=[MongoPatternModel],
    )
    yield


app = FastAPI(
    root_path=settings.app.root_path,
    title=settings.app.project_name,
    summary=settings.app.project_summary,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    version="1.0",
    lifespan=lifespan,
)

app.include_router(pattern_admin.router)
app.include_router(schedule.router)
app.include_router(repeat.router)


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
    return  # noqa!


FastAPIInstrumentor.instrument_app(app, excluded_urls="healthcheck")
