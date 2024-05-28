from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from models.paginations import Paginations


class FilmsSortParam(str, Enum):  # noqa
    imdb_rating_asc = "imdb_rating"
    imdb_rating_desc = "-imdb_rating"


class PaginatedParams(BaseModel):
    page_size: int = Field(ge=1, default=20)
    page_number: int = Field(ge=1, default=1)

    @property
    def offset(self):
        return self.page_size * (self.page_number - 1)


class Genre(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    name: str


class RolesInFilm(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    roles: list[str]


class Person(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    full_name: str


class ExtendedPerson(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    full_name: str
    films: list[RolesInFilm]


class Film(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    title: str
    imdb_rating: float | None


class ExtendedFilm(BaseModel):
    id: UUID = Field(serialization_alias="uuid")
    title: str
    imdb_rating: float
    description: str | None
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]
    subscriptions: list[UUID]


class Films(Paginations):
    results: list[Film]


class Persons(Paginations):
    results: list[Person]


class Genres(Paginations):
    results: list[Genre]


class HttpException(BaseModel):
    detail: str
