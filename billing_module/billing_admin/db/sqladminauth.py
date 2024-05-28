import datetime

import aiohttp
import jwt
from async_fastapi_jwt_auth import AuthJWT
from core.config import JWTAuthSettings, settings
from fastapi import HTTPException, Request, status
from fastapi.datastructures import FormData
from jwt.exceptions import ExpiredSignatureError
from models.token import TokenInfo
from sqladmin.authentication import AuthenticationBackend


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """
        Method to authenticate and create session token for admin user.

        Args:
            request (Request): Request object.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        x_request_id = request.headers.get("X-Request-Id")
        form: FormData = await request.form()
        username, password = form["username"], form["password"]
        access_token: str = await self.check_user_credentials(
            username,
            password,
            x_request_id,
        )
        token_payload: TokenInfo = await self.get_token_payload(access_token)
        if "admin" in token_payload.roles:  # admin everything is allowed
            session_token: str = await self.create_session_token(token_payload.user)
            request.session.update({"token": session_token})
            return True
        return False

    @staticmethod
    async def check_user_credentials(
        username: str,
        password: str,
        x_request_id: str,
    ) -> str:
        """
        Method to check user credentials and return access token.

        Args:
            username (str): User's username.
            password (str): User's password.
            x_request_id (str): User's x_request_id
        Returns:
            str: Access token.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                str(settings.auth.login_redirect_url),
                data={
                    "username": username,
                    "password": password,
                },
                headers={"X-Request-Id": x_request_id},
            ) as resp:
                response = await resp.json()
                if access_token := response.get("access_token"):
                    return access_token
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=response.get("detail", "Try again"),
                )

    @staticmethod
    async def get_token_payload(token: str) -> TokenInfo:
        """
        Method to decode the token and return token payload.

        Args:
            token (str): Access token.

        Returns:
            TokenInfo: Token payload.
        """
        token_data: dict = jwt.decode(token, options={"verify_signature": False})
        return TokenInfo(**token_data)

    @staticmethod
    async def create_session_token(subject: str) -> str:
        """
        Method to create a session token based on the subject.

        Args:
            subject (str): Subject for the token.

        Returns:
            str: Session token.
        """
        auth = AuthJWT()
        auth.load_config(JWTAuthSettings)
        return await auth.create_access_token(
            subject=subject,
            expires_time=datetime.timedelta(seconds=settings.auth_jwt.lifetime),
        )

    @staticmethod
    async def logout(request: Request) -> bool:
        """
        Method to clear session token on logout.

        Args:
            request (Request): Request object.

        Returns:
            bool: Always returns True.
        """
        request.session.clear()
        return True

    @staticmethod
    async def authenticate(request: Request) -> bool:
        """
        Method to authenticate the request based on the session token.

        Args:
            request (Request): Request object.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        token: str = request.session.get("token")
        if not token:
            return False
        try:
            jwt.decode(
                token,
                settings.auth_jwt.authjwt_secret_key,
                algorithms=settings.auth_jwt.algorithm,
            )
        except ExpiredSignatureError:
            request.session.clear()
            return False
        return True
