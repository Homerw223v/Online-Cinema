from http import HTTPStatus
from typing import Any

import pytest
from functional.srs.base_test import BaseTestAPI
from functional.testdata.elastic_indexes import index_person
from functional.testdata.person_data import person_data
from functional.utils.api_models import DataBaseExtendedPerson, ExtendedPerson, Films, Persons
from functional.utils.test_data_helpers import get_by_uuid
from pydantic import BaseModel


@pytest.mark.usefixtures("db_write_person_data", "db_write_films_data")
class TestPerson(BaseTestAPI):
    index = index_person["index"]

    @pytest.mark.parametrize(
        "path, request_params, model",
        [
            ("/api/v1/persons", {}, Persons),
            ("/api/v1/persons/search", {}, Persons),
            ("/api/v1/persons/1749841f-0569-49bb-96ce-3f9dd51b42e2", {}, ExtendedPerson),
            ("/api/v1/persons/035c4793-4864-45b8-8d4f-b86b454c60b0/films", {}, Films),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_validate(self, api_request, path: str, request_params: dict, model: BaseModel):
        await super().test_validate(api_request, path, request_params, model)

    @pytest.mark.parametrize(
        "path",
        [
            ("/api/v1/persons"),
            ("/api/v1/persons/search"),
        ],
    )
    @pytest.mark.parametrize(
        "request_params, expected_answer",
        [
            ({"page_size": 1, "page_number": 1}, {"count": 8, "total_pages": 8, "next": 2, "prev": None, "page": 1}),
            ({"page_size": 2, "page_number": 2}, {"count": 8, "total_pages": 4, "next": 3, "prev": 1, "page": 2}),
            (
                {"page_size": 10, "page_number": 1},
                {"count": 8, "total_pages": 1, "next": None, "prev": None, "page": 1},
            ),
            ({}, {"count": 8, "total_pages": 1, "next": None, "prev": None, "page": 1}),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_paginator(self, api_request, path: str, request_params: dict, expected_answer: Any):
        await super().test_paginator(api_request, path, request_params, expected_answer)

    @pytest.mark.parametrize(
        "path, request_params, status_response",
        [
            ("/api/v1/persons", {"page_size": -1, "page_number": 1}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/persons", {"page_size": 1, "page_number": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ("/api/v1/persons/1749841f-0569-49bb-96ce-3f9dd51b42e3", {}, HTTPStatus.NOT_FOUND),
            ("/api/v1/persons/1749841f-0569-49bb-96ce-3f9dd51b42e", {}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_status_response(self, api_request, path: str, request_params: dict, status_response: HTTPStatus):
        await super().test_status_response(api_request, path, request_params, status_response)

    @pytest.mark.parametrize(
        "path, request_params, result_count",
        [
            ("/api/v1/persons", {}, 8),
            ("/api/v1/persons/search", {"query": ""}, 8),
            ("/api/v1/persons/search", {"query": "Martin"}, 1),
            ("/api/v1/persons/035c4793-4864-45b8-8d4f-b86b454c60b0/films", {}, 1),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_count(self, api_request, path: str, request_params: dict, result_count: int):
        await super().test_count(api_request, path, request_params, result_count)

    @pytest.mark.parametrize(
        "path, request_params, expected_answer",
        [
            (
                "/api/v1/persons/1749841f-0569-49bb-96ce-3f9dd51b42e2",
                {},
                get_by_uuid(person_data, DataBaseExtendedPerson, "1749841f-0569-49bb-96ce-3f9dd51b42e2"),
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_equal(self, api_request, path: str, request_params: dict, expected_answer: Any):
        await super().test_equal(api_request, path, request_params, expected_answer)

    @pytest.mark.parametrize(
        "path, request_params, expected_answer",
        [
            (
                "/api/v1/persons/search",
                {"query": "1749841f-0569-49bb-96ce-3f9dd51b42e2"},
                [
                    {"full_name": "Denny Martin Flinn", "uuid": "1749841f-0569-49bb-96ce-3f9dd51b42e2"},
                ],
            ),
            (
                "/api/v1/persons/035c4793-4864-45b8-8d4f-b86b454c60b0/films",
                {},
                [
                    {"imdb_rating": 8.2, "title": "Test Film", "uuid": "01f81c66-d968-4375-bbb0-65103aa214d0"},
                ],
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
                "/api/v1/persons/search",
                {"query": "01377f6d-9767-48ce-9e37-3c81f8a3c734"},
                {
                    "id": "01377f6d-9767-48ce-9e37-3c81f8a3c734",
                    "full_name": "Test Actor",
                    "films": [],
                },
            ),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_cache(self, cache_client, db_client, api_request, path: str, request_params: dict, load_data: dict):
        await super().test_cache(cache_client, db_client, api_request, path, request_params, load_data)
