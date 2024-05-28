from functools import wraps
from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core.config import AppSettings
from db.models import Users
from db.postgres import async_session
from models.tokens import TokenInfo
from models.users import UserAuthHistory
from services.repository import UserAuthHistoryService, UsersAdminService

AuthJWTDep = Annotated[AuthJWT, Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AppSettings.auth.login_method)
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=AppSettings.auth.login_method,
    auto_error=False,
)


async def token_payload_dep(request: Request) -> TokenInfo:
    auth = AuthJWT(request)
    await auth.jwt_required()
    token_data = await auth.get_raw_jwt()
    return TokenInfo(**token_data)


async def optional_token_payload_dep(
    request: Request,
    token=Depends(optional_oauth2_scheme),
) -> TokenInfo | None:
    auth = AuthJWT(request)
    try:
        await auth.jwt_required()
    except Exception:
        return None
    token_data = await auth.get_raw_jwt()
    return TokenInfo(**token_data)


async def check_auth_dep(
    request: Request,
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Users:
    async with async_session() as session:
        user_serivce = UsersAdminService(session)
        auth_history_service = UserAuthHistoryService(session)

        try:
            user = await user_serivce.get_by_login(auth_data.username)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(auth_data.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        await logging_user_auth(user, request, auth_history_service)
    return user


async def logging_user_auth(
    user: Users,
    request: Request,
    auth_history_service: UserAuthHistoryService,
) -> None:
    """Write to db log about login"""
    if request.headers.get("X-Forwarded-For"):
        client_ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    else:
        client_ip = request.client.host
    await auth_history_service.create(
        UserAuthHistory(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        ),
    )


def check_access_endpoint(  # noqa
    roles: set[str] = set(),
    permissions: set[str] = set(),
):  # noqa
    def inner(func):  # noqa
        @wraps(func)
        async def view_method(*args, **kwargs):  # noqa
            token_payload: TokenInfo | None = kwargs.get("token_payload")
            if token_payload is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="token depends error",
                )
            if "admin" not in token_payload.roles:  # admin everything is allowed
                if not (roles & token_payload.roles or permissions & token_payload.permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden",
                    )
            return await func(*args, **kwargs)

        return view_method

    return inner


def check_access_personal_account(func):  # noqa
    @wraps(func)
    async def view_method(*args, **kwargs):  # noqa
        token_payload: TokenInfo | None = kwargs.get("token_payload")
        user_id = kwargs.get("user_id")
        if token_payload.user != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden to edit someone else's personal account",
            )
        return await func(*args, **kwargs)

    return view_method
