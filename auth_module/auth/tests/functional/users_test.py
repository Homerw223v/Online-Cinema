from http import HTTPStatus

import pytest
import pytest_asyncio

from tests.functional.crud_base_test import BaseTestCRUD
from tests.functional.test_data.helper_user import not_exists_uuid
from tests.functional.test_data.users import changed_user, retrieve_changed_user, retrieve_user, user, user_credentials

obj = user
credentials = user_credentials
retrieve_obj = retrieve_user
changed_obj = changed_user
retrieve_changed_obj = retrieve_changed_user


@pytest.mark.usefixtures("create_superuser")
class TestUser(BaseTestCRUD):
    url = "api/v1/users/"
    entities_ids = []

    @pytest_asyncio.fixture(scope="session")
    async def user_auth_headers(self, client):
        response = await client.post("login", data=user_credentials)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        return {
            "Authorization": f'Bearer {data["access_token"]}',
        }

    @pytest.mark.parametrize(
        "entity, retrieve_entity",
        [
            (obj, retrieve_obj),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_create(self, client, entity, retrieve_entity):
        await super().test_create(client, {}, entity, retrieve_entity)

    @pytest.mark.parametrize(
        "retrieve_entity",
        [retrieve_obj],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_get(self, client, user_auth_headers, retrieve_entity):
        await super().test_get(client, user_auth_headers, retrieve_entity)

    @pytest.mark.asyncio(scope="session")
    async def test_history(self, client, user_auth_headers):
        response = await client.get(
            f"{self.url}{self.entities_ids[0]}/login_history",
            headers=user_auth_headers,
        )
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data["results"]) == 1

    @pytest.mark.parametrize(
        "changed_entity, retrieve_entity",
        [
            (changed_obj, retrieve_changed_obj),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_edit(
        self,
        client,
        user_auth_headers,
        changed_entity,
        retrieve_entity,
    ):
        await super().test_edit(
            client,
            user_auth_headers,
            changed_entity,
            retrieve_entity,
        )

    @pytest.mark.asyncio(scope="session")
    async def test_delete(self, client, user_auth_headers):
        await super().test_delete(client, user_auth_headers)

    @pytest.mark.asyncio(scope="session")
    async def test_get_entity_not_found(self, client, user_auth_headers):
        await super().test_get_entity_not_found(client, user_auth_headers)

    @pytest.mark.parametrize(
        "method, url, json",
        [
            ("get", url + "{}", None),  # noqa
            ("get", url + "{}/login_history", None),  # noqa
            ("put", url + "{}", user),  # noqa
            ("delete", url + "{}", None),  # noqa
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_access_personal_account(
        self,
        client,
        helper_auth_headers,
        method,
        url,
        json,
    ):
        response = await client.request(
            method=method,
            url=url.format(not_exists_uuid),
            headers=helper_auth_headers,
            json=json,
        )
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = await client.request(
            method=method,
            url=url.format(self.entities_ids[0]),
            headers=helper_auth_headers,
            json=json,
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
