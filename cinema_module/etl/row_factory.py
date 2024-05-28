from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BaseClass(BaseModel):
    id: UUID
    modified: datetime | None = None


class PersonInfo(BaseModel):
    id: UUID
    full_name: str


class GenreInfo(BaseModel):
    id: UUID
    name: str


class ElasticFilmData(BaseModel):
    id: UUID
    imdb_rating: float | None
    genre: list[GenreInfo]
    genre_names: list[str]
    title: str | None
    description: str | None
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[PersonInfo]
    actors: list[PersonInfo]
    writers: list[PersonInfo]
    subscriptions: list[UUID]


class ElasticGenreData(BaseModel):
    id: UUID
    name: str


class PersonFilm(BaseModel):
    id: UUID
    roles: list[str]


class ElasticPersonData(BaseModel):
    id: UUID
    full_name: str
    films: list[PersonFilm]


ElasticDataClasses = type[ElasticFilmData | ElasticGenreData | ElasticPersonData]
EtlClasses = BaseClass | ElasticFilmData | ElasticGenreData | ElasticPersonData
