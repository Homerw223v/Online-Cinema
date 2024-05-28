from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class FilmWork:
    id: UUID
    title: str
    description: str
    creation_date: date
    rating: float
    type: str
    created: datetime
    modified: datetime


@dataclass
class SourceFilmWork:
    id: UUID
    title: str
    description: str
    creation_date: date
    file_path: str
    rating: float
    type: str
    created_at: datetime
    updated_at: datetime

    def convert_to_postgres_class(self) -> FilmWork:
        # ignore the field file_path because it is not in the model table
        return FilmWork(
            id=self.id,
            title=self.title,
            description=self.description,
            creation_date=self.creation_date,
            rating=self.rating,
            type=self.type,
            created=self.created_at,
            modified=self.updated_at,
        )


@dataclass
class Person:
    id: UUID
    full_name: str
    created: datetime
    modified: datetime


@dataclass
class SourcePerson:
    id: UUID
    full_name: str
    created_at: datetime
    updated_at: datetime

    def convert_to_postgres_class(self) -> Person:
        return Person(
            id=self.id,
            full_name=self.full_name,
            created=self.created_at,
            modified=self.updated_at,
        )


@dataclass
class PersonFilmWork:
    id: UUID
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime


@dataclass
class SourcePersonFilmWork:
    id: UUID
    person_id: UUID
    film_work_id: UUID
    role: str
    created_at: datetime

    def convert_to_postgres_class(self) -> PersonFilmWork:
        return PersonFilmWork(
            id=self.id,
            person_id=self.person_id,
            film_work_id=self.film_work_id,
            role=self.role,
            created=self.created_at,
        )


@dataclass
class Genre:
    id: UUID
    name: str
    description: str
    created: datetime
    modified: datetime


@dataclass
class SourceGenre:
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    def convert_to_postgres_class(self) -> Genre:
        return Genre(
            id=self.id,
            name=self.name,
            description=self.description,
            created=self.created_at,
            modified=self.updated_at,
        )


@dataclass
class GenreFilmWork:
    id: UUID
    film_work_id: UUID
    genre_id: UUID
    created: datetime


@dataclass
class SourceGenreFilmWork:
    id: UUID
    film_work_id: UUID
    genre_id: UUID
    created_at: datetime

    def convert_to_postgres_class(self) -> GenreFilmWork:
        return GenreFilmWork(
            id=self.id,
            film_work_id=self.film_work_id,
            genre_id=self.genre_id,
            created=self.created_at,
        )
