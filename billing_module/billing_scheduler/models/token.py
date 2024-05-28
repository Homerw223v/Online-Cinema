from pydantic import BaseModel, computed_field
import jwt

inaccuracy_sec = 5


class Tokens(BaseModel):
    access_token: str
    refresh_token: str

    @computed_field
    @property
    def access_expire(self) -> int:
        return int(jwt.decode(self.access_token, options={"verify_signature": False})['exp']) - inaccuracy_sec
