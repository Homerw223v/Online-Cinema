from uuid import UUID

from pydantic import BaseModel

from models.genre import Genre
from models.paginations import Paginations
from models.person import Person


class Film(BaseModel):
    id: UUID
    title: str
    imdb_rating: float | None


class ExtendedFilm(BaseModel):
    id: UUID
    title: str
    imdb_rating: float | None
    description: str | None
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]
    subscriptions: list[UUID]


class Films(Paginations):
    results: list[Film]
