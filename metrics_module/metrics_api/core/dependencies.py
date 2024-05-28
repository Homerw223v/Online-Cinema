from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from core.config import settings

optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=str(settings.auth.login_redirect_url),
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
        return None
    user_id = jwt.decode(token, options={"verify_signature": False}).get("sub")
    return UUID(user_id) if user_id else None
