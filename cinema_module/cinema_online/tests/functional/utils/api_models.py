from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Paginations(BaseModel):
    count: int
    total_pages: int
    next: int | None
    prev: int | None
    page: int
    results: Any


class Genre(BaseModel):
    uuid: UUID
    name: str


class RolesInFilm(BaseModel):
    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str


class ExtendedPerson(BaseModel):
    uuid: UUID
    full_name: str
    films: list[RolesInFilm]


class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float | None


class ExtendedFilm(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float
    description: str | None
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class Films(Paginations):
    results: list[Film]


class Persons(Paginations):
    results: list[Person]


class Genres(Paginations):
    results: list[Genre]


class DataBaseGenre(Genre):
    uuid: str = Field(alias="id")


class DataBasePerson(Person):
    uuid: str = Field(alias="id")


class DataBaseRolesInFilm(RolesInFilm):
    uuid: str = Field(alias="id")


class DataBaseExtendedPerson(ExtendedPerson):
    uuid: str = Field(alias="id")
    films: list[DataBaseRolesInFilm]


class DataBaseFilm(Film):
    uuid: str = Field(alias="id")


class DataBaseExtendedFilm(ExtendedFilm):
    uuid: str = Field(alias="id")
    title: str
    imdb_rating: float
    description: str | None
    genre: list[DataBaseGenre]
    actors: list[DataBasePerson]
    writers: list[DataBasePerson]
    directors: list[DataBasePerson]
