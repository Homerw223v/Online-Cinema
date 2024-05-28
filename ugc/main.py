import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from motor.motor_asyncio import AsyncIOMotorClient
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pymongo.errors import DuplicateKeyError
from redis import asyncio as redis_async

from api.v1 import film_timestamp, like, like_review, review
from core.config import AppSettings
from core.logger import RequestIdFilter, LOGGING
from create_index import create_indexes
from db import review_db_client
from services.exceptions import (
    AlreadyExistsException,
    DatabaseConnectionError,
    FilmTimestampNotFoundException,
    GradeNotFoundException,
    LikeNotFoundException,
    NotFoundException,
    ReviewNotFoundException,
)
from services.mongo.collections import film_collection, timestamp_collection

load_dotenv()

app_settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    logging_config.dictConfig(LOGGING)
    redis = redis_async.from_url(
        str(app_settings.redis.dsn),  # type: ignore
        encoding="utf8",
        decode_responses=True,
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    review_db_client.db = AsyncIOMotorClient(str(app_settings.mongo_db.dsn))
    await create_indexes(review_db_client.db, [film_collection, timestamp_collection])
    yield


tags_metadata = [
    {
        "name": "reviews",
        "description": "Operations with reviews.",
    },
    {
        "name": "likes_review",
        "description": "Operations with likes review.",
    },
    {
        "name": "likes",
        "description": "Operations with likes.",
    },
    {
        "name": "film_timestamp",
        "description": "Operations with film timestamp.",
    },
]


app = FastAPI(
    root_path=app_settings.app.root_path,
    title=app_settings.app.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    openapi_tags=tags_metadata,
    summary="Here you can get information about films, genres and people involved in the creation of films",
    version="1.0",
    lifespan=lifespan,
)


app.include_router(like.likes_router)
app.include_router(review.review_router)
app.include_router(like_review.likes_review_router)
app.include_router(film_timestamp.timestamp_router)


@app.exception_handler(NotFoundException)
async def unicorn_not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:  # noqa
    if isinstance(exc, ReviewNotFoundException):
        review_id = request.path_params.get("review_id", "???")
        text = f'Review "{review_id}" not found'
    elif isinstance(exc, GradeNotFoundException):
        grade_id = request.path_params.get("grade_id", "???")
        text = f'Person "{grade_id}" not found'
    elif isinstance(exc, LikeNotFoundException):
        like_id = request.path_params.get("like_id", "???")
        text = f'Like "{like_id}" not found'
    elif isinstance(exc, FilmTimestampNotFoundException):
        timestamp_id = request.path_params.get("timestamp_id", "???")
        text = f'Film timestamp "{timestamp_id}" not found'
    else:
        text = "Not found"
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": text},
    )


@app.exception_handler(ConnectionError)
async def unicorn_elastic_connection_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "DatabaseConnectionError"},
    )


@app.exception_handler(DatabaseConnectionError)
async def unicorn_mongo_connection_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "DatabaseConnectionError"},
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": 'Error changing an entity owned by another user'},
    )


@app.exception_handler(AlreadyExistsException)
async def already_exists_handler(request: Request, exc: AlreadyExistsException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Entity already exists"},
    )


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_error_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Entity already exists"},
    )


@app.middleware("http")
async def before_request(request: Request, call_next):
    response = await call_next(request)
    if app_settings.tracer_enable:
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "X-Request-Id is required"})
    return response


@app.middleware("http")
async def add_log_filter(request: Request, call_next):
    for log_type in ("access", "error"):
        logger = logging.getLogger("uvicorn.%s" % (log_type,))
        logger.addFilter(RequestIdFilter(request))
    return await call_next(request)


@app.get("/healthcheck")
async def health() -> Any:
    return  # noqa


FastAPIInstrumentor.instrument_app(app, excluded_urls="healthcheck")
