from uuid import UUID

from pydantic import BaseModel


class OauthUserData(BaseModel):
    user_id: UUID | None
    provider_name: str
    client_id: str
    email: str
    first_name: str
    last_name: str
