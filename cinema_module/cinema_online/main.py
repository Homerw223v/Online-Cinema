import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import Any

from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch, ConnectionError
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from redis import asyncio as redis_async

from api.v1 import film, genre, person
from core.config import AppSettings
from core.logger import RequestIdFilter, LOGGING
from core.permission import NoNecessaryRoleError
from db import db_client
from interfaces.db_interface import ElasticInterface
from services import auth
from services.exceptions import (
    FilmNotFound,
    GenreNotFound,
    NotFoundException,
    PersonNotFound,
)

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
    db_client.db = ElasticInterface(AsyncElasticsearch(hosts=[str(app_settings.elastic.base_url)]))  # type: ignore
    auth.auth_interface = auth.AuthService(**app_settings.auth.model_dump()).connections()
    yield
    await redis.close()
    await db_client.db.close()
    await auth.auth_interface.close()


tags_metadata = [
    {
        "name": "films",
        "description": "Operations with films.",
    },
    {
        "name": "genres",
        "description": "Operations with genres.",
    },
    {
        "name": "persons",
        "description": "Operations with persons.",
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


app.include_router(film.film_router)
app.include_router(genre.genre_router)
app.include_router(person.person_router)


@app.exception_handler(NotFoundException)
async def unicorn_not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:  # noqa
    if isinstance(exc, FilmNotFound):  # noqa
        film_id = request.path_params.get("film_id", "???")
        text = f'Film "{film_id}" not found'
    elif isinstance(exc, GenreNotFound):
        genre_id = request.path_params.get("genre_id", "???")
        text = f'Genre "{genre_id}" not found'
    elif isinstance(exc, PersonNotFound):
        person_id = request.path_params.get("person_id", "???")
        text = f'Person "{person_id}" not found'
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


@app.exception_handler(NoNecessaryRoleError)
async def no_necessary_role_error_handler(request: Request, exc: NoNecessaryRoleError) -> JSONResponse:
    if exc.required_roles != "":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": f'Buy any of the subscriptions "{exc.required_roles}" to watch the movie'},
        )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": 'Permission denied'},
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
