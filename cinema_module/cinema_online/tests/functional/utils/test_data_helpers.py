from operator import itemgetter
from typing import Any

from pydantic import BaseModel
from testdata.films_data import films_data
from utils.api_models import DataBaseFilm


def get_by_uuid(raw_data: list[dict[str, Any]], model: BaseModel, uuid: str) -> dict[str, Any]:
    data = transform_data(raw_data, model)
    for item in data:
        if item["uuid"] == uuid:
            return item
    return {}


def get_films_by_genre(uuid: str) -> list[dict[str, Any]]:
    filtered_data = [item for item in films_data if uuid in (genre["id"] for genre in item["genre"])]  # noqa
    return transform_data(filtered_data, DataBaseFilm)


def sort_films_by_rating(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(data, key=itemgetter("imdb_rating"), reverse=True)


def transform_data(data: list[dict[str, Any]], model: BaseModel):
    return [model.model_validate(item).model_dump() for item in data]
