import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from api.v1 import payment, user_subscriptions, cards
from core.config import AppSettings
from db.postgres import create_database

from core.logger import RequestIdFilter, LOGGING
from services.exceptions import (
    AlreadyExistException,
    DatabaseConnectionError,
    NotFoundException,
)

app_settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    logging_config.dictConfig(LOGGING)
    await create_database()
    yield


tags_metadata = [
    {
        "name": "cards",
        "description": "Operations with user payment methods.",
    },
    {
        "name": "payment",
        "description": "Operations with payment and refund.",
    },
    {
        "name": "user_subscriptions",
        "description": "Operations with user subscription.",
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


app.include_router(payment.payment_router)
app.include_router(user_subscriptions.user_subscriptions_router)
app.include_router(cards.cards_router)


@app.exception_handler(NotFoundException)
async def unicorn_not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:  # noqa
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Entity not found"},
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


@app.exception_handler(AlreadyExistException)
async def already_exists_handler(request: Request, exc: AlreadyExistException) -> JSONResponse:
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
