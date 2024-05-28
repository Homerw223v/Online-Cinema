from functools import cached_property

from pydantic import BaseModel, ConfigDict, Field, computed_field


class TokenInfo(BaseModel):
    user: str = Field(validation_alias="sub")
    roles_list: str = Field(validation_alias="roles", exclude=True)
    permissions_list: str = Field(validation_alias="permissions", exclude=True)
    jti: str
    exp: int

    @computed_field
    @cached_property
    def roles(self) -> set[str]:
        return set(filter(None, self.roles_list.split(",")))

    @computed_field
    @cached_property
    def permissions(self) -> set[str]:
        return set(filter(None, self.permissions_list.split(",")))

    model_config = ConfigDict(arbitrary_types_allowed=True)
