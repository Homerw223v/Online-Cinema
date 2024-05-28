from http import HTTPStatus
from typing import Any

import pytest
from functional.srs.base_test import BaseTestAPI
from functional.testdata.elastic_indexes import index_movie
from functional.testdata.films_data import films_data
from functional.utils.api_models import DataBaseFilm, Films
from functional.utils.test_data_helpers import get_by_uuid, get_films_by_genre, sort_films_by_rating, transform_data
from pydantic import BaseModel


@pytest.mark.usefixtures("db_write_films_data")
class TestFilms(BaseTestAPI):
    index = index_movie["index"]

    @pytest.mark.parametrize(
        "path, request_params, model",
        [
            ("/api/v1/films", {}, Films),
            ("/api/v1/films/search", {}, Films),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_validate(self, api_request, path: str, request_params: dict, model: BaseModel):
        await super().test_validate(api_request, path, request_params, model)

    @pytest.mark.parametrize(
        "path",
        [
            ("/api/v1/films"),
            ("/api/v1/films/search"),
        ],
    )
    @pytest.mark.parametrize(
        "request_params, expected_answer",
        [
            ({"page_size": 1, "page_number": 1}, {"count": 5, "total_pages": 5, "next": 2, "prev": None, "page": 1}),
            ({"page_size": 2, "page_number": 2}, {"count": 5, "total_pages": 3, "next": 3, "prev": 1, "page": 2}),
            (
                {"page_size": 10, "page_number": 1},
                {"count": 5, "total_pages": 1, "next": None, "prev": None, "page": 1},
            ),
            ({}, {"count": 5, "total_pages": 1, "next": None, "prev": None, "page": 1}),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_paginator(self, api_request, path: str, request_params: dict, expected_answer: Any):
        await super().test_paginator(api_request, path, request_params, expected_answer)

    @pytest.mark.parametrize(
        "path, request_params, status_response",
        [
            ("/api/v1/films", {"page_size": -1, "page_number": 1}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/films", {"page_size": 1, "page_number": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_status_response(self, api_request, path: str, request_params: dict, status_response: HTTPStatus):
        await super().test_status_response(api_request, path, request_params, status_response)

    @pytest.mark.parametrize(
        "path, request_params, result_count",
        [
            ("/api/v1/films", {}, 5),
            ("/api/v1/films", {"genre": "56b541ab-4d66-4021-8708-397762bff2d4"}, 2),
            ("/api/v1/films/search", {"query": ""}, 5),
            ("/api/v1/films/search", {"query": "00af52ec-9345-4d66-adbe-50eb917f463a"}, 1),
            ("/api/v1/films/search", {"query": "Star"}, 4),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_count(self, api_request, path: str, request_params: dict, result_count: int):
        await super().test_count(api_request, path, request_params, result_count)

    @pytest.mark.parametrize(
        "path, request_params, expected_answer",
        [
            (
                "/api/v1/films",
                {"page_size": 3, "page_number": 1, "sort": "-imdb_rating"},
                {
                    "count": 5,
                    "total_pages": 2,
                    "next": 2,
                    "prev": None,
                    "page": 1,
                    "results": sort_films_by_rating(transform_data(films_data, DataBaseFilm))[:3],
                },
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_equal(self, api_request, path: str, request_params: dict, expected_answer: Any):
        pass

    @pytest.mark.parametrize(
        "path, request_params, expected_answer",
        [
            (
                "/api/v1/films",
                {"page_size": 3, "page_number": 1, "sort": "-imdb_rating"},
                sort_films_by_rating(transform_data(films_data, DataBaseFilm))[:3],
            ),
            (
                "/api/v1/films",
                {"page_size": 3, "page_number": 2, "sort": "-imdb_rating"},
                sort_films_by_rating(transform_data(films_data, DataBaseFilm))[3:6],
            ),
            (
                "/api/v1/films/search",
                {"query": "00e2e781-7af9-4f82-b4e9-14a488a3e184"},
                [get_by_uuid(films_data, DataBaseFilm, "00e2e781-7af9-4f82-b4e9-14a488a3e184")],
            ),
            (
                "/api/v1/films",
                {"genre": "56b541ab-4d66-4021-8708-397762bff2d4", "sort": "-imdb_rating"},
                sort_films_by_rating(get_films_by_genre("56b541ab-4d66-4021-8708-397762bff2d4")),
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_equal_results(self, api_request, path: str, request_params: dict, expected_answer: Any):
        await super().test_equal_results(api_request, path, request_params, expected_answer)

    @pytest.mark.parametrize(
        "path, request_params, load_data",
        [
            (
                "/api/v1/films/search",
                {"query": "01f81c66-d968-4375-bbb0-65103aa21400"},
                {
                    "id": "01f81c66-d968-4375-bbb0-65103aa21400",
                    "imdb_rating": 9.9,
                    "genre": [],
                    "genre_names": [],
                    "title": "Test Film",
                    "description": None,
                    "directors_names": [],
                    "actors_names": [],
                    "writers_names": [],
                    "directors": [],
                    "actors": [],
                    "writers": [],
                },
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_cache(self, cache_client, db_client, api_request, path: str, request_params: dict, load_data: dict):
        await super().test_cache(cache_client, db_client, api_request, path, request_params, load_data)
