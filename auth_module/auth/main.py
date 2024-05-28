import logging
from contextlib import asynccontextmanager
from logging import config as logging_config

import sentry_sdk
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from redis import asyncio as redis_async
from sqlalchemy.exc import NoResultFound

import api.v1.admin.users as admin_users  # noqa
from api.v1.admin.permissions import permissions_id_router, permissions_router
from api.v1.admin.roles import roles_id_router, roles_router
from api.v1.tokens import open_token_router, token_router
from api.v1.users import open_user_router, user_router
from api.v1.email import email_router
from core.config import settings
from core.logger import LOGGING, RequestIdFilter
from core.oauth_provider import OauthProviderFactory, UnknownOauthProviderError
from core.user_oauth import EmptyProfileError
from db import redis
from services.exceptions import AlreadyExistException
from services.repository import DatabaseConnectionError

if settings.sentry.dsn:
    sentry_sdk.init(**settings.sentry.model_dump())


@asynccontextmanager
async def lifespan(_):
    logging_config.dictConfig(LOGGING)
    redis.redis_interface = redis_async.from_url(
        str(settings.redis.dsn),  # type: ignore
        encoding="utf8",
        decode_responses=True,
    )
    yield
    await redis.redis_interface.close()


tags_metadata = [
    {
        "name": "personal_account",
        "description": "Managing your personal account ",
    },
    {
        "name": "admin/users",
        "description": "Manage users",
    },
    {
        "name": "admin/roles",
        "description": "Manage roles",
    },
    {
        "name": "admin/permissions",
        "description": "Manage permissions",
    },
    {
        "name": "tokens",
        "description": "Operation with tokens",
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

app.include_router(open_user_router)
app.include_router(user_router)
app.include_router(email_router)
app.include_router(admin_users.users_router)
app.include_router(admin_users.users_id_router)
app.include_router(roles_router)
app.include_router(roles_id_router)
app.include_router(permissions_router)
app.include_router(permissions_id_router)
app.include_router(open_token_router)
app.include_router(token_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.auth.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(DatabaseConnectionError)
def database_connection_exception_handler(
    request: Request,
    exc: DatabaseConnectionError,
):
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "Database connection timeout"},
    )


@app.exception_handler(NoResultFound)
def database_not_found_exception_handler(request: Request, exc: NoResultFound):
    if request.path_params.get("user_id"):
        message = f'User "{request.path_params.get("user_id")}" not found'
    elif request.path_params.get("role_id"):
        message = f'Role "{request.path_params.get("role_id")}" not found'
    elif request.path_params.get("permission_id"):
        message = f'Permission "{request.path_params.get("permission_id")}" not found'
    else:
        message = "Object not found"
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": message},
    )


@app.exception_handler(AlreadyExistException)
def already_exists_exception_handler(request: Request, exc: AlreadyExistException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Already exists"},
    )


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


@app.exception_handler(EmptyProfileError)
def empty_profile_handler(request: Request, exc: EmptyProfileError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Please fill out the profile before deleting the provider"},
    )


@app.exception_handler(UnknownOauthProviderError)
def unknown_provider_handler(request: Request, exc: UnknownOauthProviderError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": f"Unknown oauth provider. Supported: {OauthProviderFactory.get_all_providers()}",
        },
    )
