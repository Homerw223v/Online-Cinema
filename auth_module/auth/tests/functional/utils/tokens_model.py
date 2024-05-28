from pydantic import BaseModel


class BaseTokenPayload(BaseModel):
    sub: str
    iat: int
    nbf: int
    jti: str
    exp: int
    type: str


class AccessTokenPayload(BaseTokenPayload):
    roles: str
    permissions: str
