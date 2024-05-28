from http import HTTPStatus

import pytest

from tests.functional.crud_base_test import BaseTestCRUD
from tests.functional.test_data.roles import changed_role, role

obj = role
retrieve_obj = role
changed_obj = changed_role
retrieve_changed_obj = changed_role


@pytest.mark.usefixtures("create_superuser")
class TestRole(BaseTestCRUD):
    url = "api/v1/admin/roles/"
    entities_ids = []

    @pytest.mark.parametrize(
        "entity, retrieve_entity",
        [
            (obj, retrieve_obj),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_create(self, client, auth_headers, entity, retrieve_entity):
        await super().test_create(client, auth_headers, entity, retrieve_entity)

    @pytest.mark.parametrize(
        "retrieve_entity",
        [retrieve_obj],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_get(self, client, auth_headers, retrieve_entity):
        await super().test_get(client, auth_headers, retrieve_entity)

    @pytest.mark.parametrize(
        "changed_entity, retrieve_entity",
        [
            (changed_obj, retrieve_changed_obj),
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_edit(self, client, auth_headers, changed_entity, retrieve_entity):
        await super().test_edit(client, auth_headers, changed_entity, retrieve_entity)

    @pytest.mark.asyncio(scope="session")
    async def test_delete(self, client, auth_headers):
        await super().test_delete(client, auth_headers)

    @pytest.mark.asyncio(scope="session")
    async def test_get_entity_not_found(self, client, auth_headers):
        await super().test_get_entity_not_found(client, auth_headers)

    @pytest.mark.parametrize(
        "method, url, json",
        [
            ("get", url, None),  # noqa
            ("post", url, changed_obj),  # noqa
            ("get", url + "{}", None),  # noqa
            ("put", url + "{}", changed_obj),  # noqa
            ("delete", url + "{}", None),  # noqa
        ],
    )
    @pytest.mark.asyncio(scope="session")
    async def test_access_admin_roles(
        self,
        client,
        helper_auth_headers,
        method,
        url,
        json,
    ):
        response = await client.request(
            method=method,
            url=url.format(self.entities_ids[0]),
            headers=helper_auth_headers,
            json=json,
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
