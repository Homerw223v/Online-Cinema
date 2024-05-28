from uuid import UUID

from opentelemetry import trace
from pydantic import BaseModel

from models.film import ExtendedFilm

tracer = trace.get_tracer(__name__)


class NoNecessaryRoleError(Exception):
    def __init__(self, required_roles):
        super().__init__()
        self.required_roles = ", ".join(map(str, required_roles))


def check_film_permission(film: ExtendedFilm, user_roles: list[str], user_subscription: list[str]) -> None:
    if "admin" in user_roles:
        return
    required_subscriptions = film.subscriptions
    if not set(required_subscriptions) & set(user_subscription):
        raise NoNecessaryRoleError(required_subscriptions)


def is_owner_permission(model: BaseModel, user_id: UUID) -> None:
    if getattr(model, "user_id", ...) != user_id:
        raise PermissionError("Permission error. User is not owner entity")
