from http import HTTPStatus
from typing import Any

import pytest
from functional.srs.base_test import BaseTestAPI
from functional.testdata.elastic_indexes import index_genre
from functional.testdata.genres_data import genres_data
from functional.utils.api_models import DataBaseGenre, Films, Genre, Genres
from functional.utils.test_data_helpers import get_by_uuid, get_films_by_genre, sort_films_by_rating
from pydantic import BaseModel


@pytest.mark.usefixtures("db_write_genre_data", "db_write_films_data")
class TestGenre(BaseTestAPI):
    index = index_genre["index"]

    # ! test models answer
    @pytest.mark.parametrize(
        "path, request_params, model",
        [
            ("/api/v1/genres", {}, Genres),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff", {}, Genre),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff/films", {}, Films),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_validate(self, api_request, path: str, request_params: dict, model: BaseModel):
        await super().test_validate(api_request, path, request_params, model)

    # ! test paginator for genres
    @pytest.mark.parametrize("path", [("/api/v1/genres")])
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
    async def test_paginator(
        self,
        api_request,
        path: str,
        request_params: dict[str, str],
        expected_answer: dict[str, int],
    ):
        await super().test_paginator(api_request, path, request_params, expected_answer)

    # ! test paginator for films via genres
    @pytest.mark.parametrize(
        "path",
        [("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff/films")],
    )
    @pytest.mark.parametrize(
        "request_params, expected_answer",
        [
            ({"page_size": 1, "page_number": 1}, {"count": 2, "total_pages": 2, "next": 2, "prev": None, "page": 1}),
            ({"page_size": 1, "page_number": 2}, {"count": 2, "total_pages": 2, "next": None, "prev": 1, "page": 2}),
            (
                {"page_size": 10, "page_number": 1},
                {"count": 2, "total_pages": 1, "next": None, "prev": None, "page": 1},
            ),
            ({}, {"count": 2, "total_pages": 1, "next": None, "prev": None, "page": 1}),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_films_paginator(
        self,
        api_request,
        path: str,
        request_params: dict[str, str],
        expected_answer: dict[str, int],
    ):
        await super().test_paginator(api_request, path, request_params, expected_answer)  # noqa

    # ! test bad status code
    @pytest.mark.parametrize(
        "path, request_params, status_response",
        [
            ("/api/v1/genres", {"page_size": -1, "page_number": 1}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/genres", {"page_size": 1, "page_number": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07fa", {}, HTTPStatus.NOT_FOUND),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07fa/films", {}, HTTPStatus.NOT_FOUND),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07f", {}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07f/films", {}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_status_response(
        self,
        api_request,
        path: str,
        request_params: dict[str, str],
        status_response: int,
    ):
        await super().test_status_response(api_request, path, request_params, status_response)

    # ! test count result for paginator
    @pytest.mark.parametrize(
        "path, request_params, result_count",
        [
            ("/api/v1/genres", {}, 5),
            ("/api/v1/genres", {"page_size": 1, "page_number": 1}, 1),
            ("/api/v1/genres", {"page_size": 3, "page_number": 2}, 2),
            ("/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff/films", {}, 2),
            ("/api/v1/genres/120a21cf-9097-479e-904a-13dd7198c1dd/films", {}, 0),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_count(self, api_request, path: str, request_params: dict[str, str], result_count: int):
        await super().test_count(api_request, path, request_params, result_count)

    # ! test get genre by uuid
    @pytest.mark.parametrize(
        "path, entity_uuid, expected_answer",
        [
            (
                "/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff",
                "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff",
                get_by_uuid(genres_data, DataBaseGenre, "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"),
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_equal(self, api_request, path: str, entity_uuid: dict[str, str], expected_answer: dict[str, int]):
        await super().test_equal(api_request, path, entity_uuid, expected_answer)

    # ! test sorting films by genre (check by uuid films list)
    @pytest.mark.parametrize(
        "path, request_params, expected_answer",
        [
            (
                "/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff/films",
                {},
                sort_films_by_rating(get_films_by_genre("3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff")),
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_equal_results(self, api_request, path: str, request_params: dict, expected_answer: Any):
        await super().test_equal_results(api_request, path, request_params, expected_answer)

    # ! test_cache
    @pytest.mark.parametrize(
        "path, request_params, load_data",
        [
            (
                "/api/v1/genres/00e2e781-7af9-4f82-b4e9-14a488a3e000",
                {},
                {
                    "name": "Action",
                    "id": "00e2e781-7af9-4f82-b4e9-14a488a3e000",
                },
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_cache(self, cache_client, db_client, api_request, path: str, request_params: dict, load_data: dict):
        await db_client.write_data(self.index, [load_data])

        status, cache_data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        assert cache_data

        await db_client.delete_entity_by_uuid(self.index, load_data["id"])

        status, new_data = await api_request(path=path, params=request_params)
        assert cache_data == new_data

        await cache_client.clear_cache()

        status, empty_data = await api_request(path=path, params=request_params)
        assert not empty_data
