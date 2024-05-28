from uuid import UUID

from pydantic import BaseModel

from models.paginations import Paginations


class RolesInFilm(BaseModel):
    id: UUID
    roles: list[str]


class Person(BaseModel):
    id: UUID
    full_name: str


class ExtendedPerson(BaseModel):
    id: UUID
    full_name: str
    films: list[RolesInFilm]


class Persons(Paginations):
    results: list[Person]
