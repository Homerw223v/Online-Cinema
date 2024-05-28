from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import pytest
from pydantic import BaseModel


class BaseTestAPI(ABC):
    @property
    @classmethod
    @abstractmethod
    def index(cls):
        pass  # noqa

    @pytest.mark.asyncio(scope="session")
    async def test_count(self, api_request, path: str, request_params: dict[str, str], result_count: int):
        status, data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        assert len(data["results"]) == result_count

    @pytest.mark.asyncio(scope="session")
    async def test_paginator(self, api_request, path: str, request_params: dict, expected_answer: Any):
        status, data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        for key, value in expected_answer.items():
            assert data[key] == value, f"Not match data for key: {key}"

    @pytest.mark.asyncio(scope="session")
    async def test_status_response(self, api_request, path: str, request_params: dict, status_response: HTTPStatus):
        status, data = await api_request(path=path, params=request_params)
        assert status == status_response

    @pytest.mark.asyncio(scope="session")
    async def test_equal(self, api_request, path: str, request_params: dict, expected_answer: Any):
        status, data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        assert expected_answer == data

    @pytest.mark.asyncio(scope="session")
    async def test_equal_results(self, api_request, path: str, request_params: dict, expected_answer: Any):
        status, data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        assert expected_answer == data["results"]

    @pytest.mark.asyncio(scope="session")
    async def test_validate(self, api_request, path: str, request_params: dict, model: BaseModel):
        status, data = await api_request(path=path, params=request_params)
        assert status == HTTPStatus.OK
        model.model_validate(data)

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
        assert not empty_data["results"]
