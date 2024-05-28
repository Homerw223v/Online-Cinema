from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import NoResultFound

from api.v1.dependencies import get_oauth_state_dep
from api.v1.models import OauthProviders, OauthState, Tokens
from core.dependencies import AuthJWTDep, check_auth_dep, oauth2_scheme, optional_token_payload_dep, token_payload_dep
from core.jwt_manage import create_tokens, get_user_by_jti, revoke_all_tokens, revoke_tokens
from core.oauth_provider import OauthProviderFactory
from core.user_oauth import add_provider, del_provider, get_oauth_user
from db.models import Users
from models.tokens import TokenInfo

open_token_router = APIRouter(tags=["tokens"])
token_router = APIRouter(dependencies=[Depends(oauth2_scheme)], tags=["tokens"])


@open_token_router.post("/login")
async def login(
    authorize: AuthJWTDep,
    user: Users = Depends(check_auth_dep),
) -> Tokens:
    access_token, refresh_token = await create_tokens(user)
    return Tokens(access_token=access_token, refresh_token=refresh_token)


@token_router.post("/refresh")
async def refresh(authorize: AuthJWTDep):
    """For accessing /refresh endpoint remember to change access_token with refresh_token in the header
    Authorization: Bearer <refresh_token>
    """
    await authorize.jwt_refresh_token_required()  # check refresh token
    raw_refresh = await authorize.get_raw_jwt()
    # check refresh token in database
    try:
        user = await get_user_by_jti(raw_refresh["jti"])
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    await revoke_tokens(raw_refresh["jti"])

    new_access_token, new_refresh_token = await create_tokens(user)

    return Tokens(access_token=new_access_token, refresh_token=new_refresh_token)


@token_router.delete("/logout")
async def logout(token_payload: TokenInfo = Depends(token_payload_dep)) -> None:
    await revoke_tokens(token_payload.jti)


@token_router.delete("/logout_all_device")
async def logout_all_device(
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> None:
    """Revoke all user's tokens"""
    await revoke_all_tokens(user_id=token_payload.user)


@open_token_router.get("/oauth_add")
async def get_oauth(
    provider: OauthProviders,
    token_payload: TokenInfo | None = Depends(optional_token_payload_dep),
) -> Tokens | None:
    provider = OauthProviderFactory.get_provider(provider)
    return RedirectResponse(
        url=provider.get_redirect_url(token_payload),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@open_token_router.get("/oauth")
async def oauth(
    code: str,
    state: OauthState = Depends(get_oauth_state_dep),
) -> Tokens | None:
    provider = OauthProviderFactory.get_provider(state.provider_name)
    provider_info = await provider.get_user_info(code=code, state=state)
    if provider_info.user_id:
        await add_provider(provider_info)
        return None
    else:
        user = await get_oauth_user(provider_info)

    new_access_token, new_refresh_token = await create_tokens(user)
    return Tokens(access_token=new_access_token, refresh_token=new_refresh_token)


@token_router.delete("/oauth")
async def delete_oauth(
    provider: OauthProviders,
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> None:
    await del_provider(provider_name=provider.value, user_id=UUID(token_payload.user))


@token_router.get("/roles")
async def get_roles(
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> list[str]:
    return token_payload.roles


@token_router.get("/check_role")
async def check_role_in_token(
    role: str,
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> bool:
    """checking for the presence of the transferred role in the token"""
    return role in token_payload.roles


@token_router.get("/user_id")
async def get_verify_token(
    token_payload: TokenInfo = Depends(token_payload_dep),
) -> UUID:
    return UUID(token_payload.user)
