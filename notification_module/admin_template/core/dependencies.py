from functools import wraps
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models.models import TokenInfo
from core.config import settings

optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=str(settings.auth_redirect.login_redirect_url),
    auto_error=False,
)


async def user_id_dependency(
    token=Depends(optional_oauth2_scheme),
) -> UUID | None:
    """
    Function to get user_id from token

    Parameters:
    - token: The token extracted from the request using the OAuth2 scheme.

    Returns:
    - Optional[UUID]: Returns the UUID of user if token exists, otherwise returns None.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = jwt.decode(token, options={"verify_signature": False}).get("sub")
    return UUID(user_id) if user_id else None


async def token_payload_dep(
    token=Depends(optional_oauth2_scheme),
) -> TokenInfo:
    token_data = jwt.decode(token, options={"verify_signature": False})
    return TokenInfo(**token_data)


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
                if not (
                    roles & token_payload.roles
                    or permissions & token_payload.permissions
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden",
                    )
            return await func(*args, **kwargs)

        return view_method

    return inner
