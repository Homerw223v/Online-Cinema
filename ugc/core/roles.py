from uuid import UUID

from pydantic import BaseModel


def is_owner_permission(model: BaseModel, user_id: UUID) -> None:
    if getattr(model, "user_id", ...) != user_id:
        raise PermissionError("Permission error. User is not owner entity")
