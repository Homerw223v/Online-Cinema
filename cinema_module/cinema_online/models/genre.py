from uuid import UUID

from pydantic import BaseModel

from models.paginations import Paginations


class Genre(BaseModel):
    id: UUID
    name: str


class Genres(Paginations):
    results: list[Genre]
