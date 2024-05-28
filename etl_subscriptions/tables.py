"""Classes for each table in database."""
from uuid import UUID

from dataclasses import dataclass


@dataclass
class Subscriptions:
    id: UUID
    name: str
    is_active: bool = True
