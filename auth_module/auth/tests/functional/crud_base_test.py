from abc import ABC, abstractmethod
from http import HTTPStatus

import pytest


@pytest.mark.usefixtures("create_db")
class BaseTestCRUD(ABC):
    @property
    @classmethod
    @abstractmethod
    def url(cls):
        pass  # noqa

    @property
    @classmethod
    @abstractmethod
    def entities_ids(cls) -> list:
        pass  # noqa

    @pytest.mark.asyncio(scope="session")
    async def test_create(self, client, auth_headers, entity, retrieve_entity=None):
        response = await client.post(self.url, json=entity, headers=auth_headers)
        assert response.status_code == HTTPStatus.CREATED

        if retrieve_entity is None:
            retrieve_entity = entity
        data = response.json()
        retrieve_entity["id"] = data["id"]
        self.entities_ids.append(data["id"])
        assert data == retrieve_entity

    @pytest.mark.asyncio(scope="session")
    async def test_get(self, client, auth_headers, retrieve_entity):
        response = await client.get(
            self.url + self.entities_ids[0],
            headers=auth_headers,
        )
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        retrieve_entity["id"] = self.entities_ids[0]
        assert retrieve_entity == data

    @pytest.mark.asyncio(scope="session")
    async def test_edit(
        self,
        client,
        auth_headers,
        changed_entity,
        retrieve_entity=None,
    ):
        response = await client.put(
            self.url + self.entities_ids[0],
            json=changed_entity,
            headers=auth_headers,
        )
        assert response.status_code == HTTPStatus.OK

        if retrieve_entity is None:
            retrieve_entity = changed_entity
        data = response.json()
        retrieve_entity["id"] = self.entities_ids[0]
        assert retrieve_entity == data

    @pytest.mark.asyncio(scope="session")
    async def test_delete(self, client, auth_headers):
        response = await client.delete(
            self.url + self.entities_ids[0],
            headers=auth_headers,
        )
        assert response.status_code == HTTPStatus.OK

    @pytest.mark.asyncio(scope="session")
    async def test_get_entity_not_found(self, client, auth_headers):
        response = await client.get(
            self.url + self.entities_ids[0],
            headers=auth_headers,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
