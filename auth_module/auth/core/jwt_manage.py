from contextlib import suppress
from datetime import datetime, timedelta
from uuid import uuid4

from async_fastapi_jwt_auth import AuthJWT

from core.config import AppSettings, settings
from db import redis
from db.models import Users
from db.postgres import async_session
from models.tokens import Token
from services.repository import TokensService


@AuthJWT.token_in_denylist_loader
async def check_if_token_in_denylist(decrypted_token) -> bool:
    jti = decrypted_token["jti"]
    entry = await redis.redis_interface.get(jti)
    return entry and entry == "true"


async def revoke_access(jti: str) -> None:
    await redis.redis_interface.setex(
        jti,
        settings.jwt.authjwt_access_token_expires,
        "true",
    )


async def revoke_tokens(jti: str):
    async with async_session() as session:
        with suppress(Exception):
            await TokensService(session).delete_by_jti(jti)
    await revoke_access(jti)


async def create_tokens(user: Users) -> tuple[str, str]:
    auth = AuthJWT()
    access_token_data = {
        "roles": ",".join([role.name for role in user.roles]),
        "permissions": ",".join(permission.name for permission in user.permissions),
    }
    refresh_token_data = {}

    # creating a common jti
    jti = str(uuid4())
    access_token_data["jti"] = jti
    refresh_token_data["jti"] = jti

    async with async_session() as session:
        token_service = TokensService(session)

        access_token = await auth.create_access_token(
            subject=str(user.id),
            user_claims=access_token_data,
        )
        refresh_token = await auth.create_refresh_token(
            subject=str(user.id),
            user_claims=refresh_token_data,
        )

        await token_service.create(Token(jti=jti, user_id=user.id))
        await token_service.delete_user_expire_tokens(
            entity_id=user.id,
            before_created=datetime.now() - timedelta(hours=AppSettings.jwt.refresh_token_expires_hours),
        )

    return access_token, refresh_token


async def revoke_all_tokens(user_id: str) -> None:
    async with async_session() as session:
        tokens = await TokensService(session).get_list(
            paginated_params=None,
            filters={"user_id": user_id},
        )
        for token in tokens:
            await revoke_tokens(token.jti)


async def get_user_by_jti(jti: str):
    async with async_session() as session:
        token_service = TokensService(session)
        token = await token_service.get_by_jti(jti=jti)
        return token.user
