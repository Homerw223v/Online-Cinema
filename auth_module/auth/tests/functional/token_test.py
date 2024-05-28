import os
import time
from datetime import datetime, timedelta
from http import HTTPStatus

import jwt
import pytest
import pytest_asyncio

from tests.functional.test_data.tokens import token_user, token_user_credentials
from tests.functional.utils.tokens_model import AccessTokenPayload, BaseTokenPayload


@pytest_asyncio.fixture(scope="session")
async def create_token_user(client, create_db):
    response = await client.post("api/v1/users/", json=token_user)
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.asyncio(scope="session")
async def test_login(client, create_token_user):
    response = await client.post("login", data=token_user_credentials)
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data.get("access_token")
    assert data.get("refresh_token")


@pytest.mark.asyncio(scope="session")
async def test_logout(client, create_token_user):
    response = await client.post("login", data=token_user_credentials)
    data = response.json()
    token_auth_headers = {"Authorization": f"Bearer {data['access_token']}"}
    auth_refresh_headers = {"Authorization": f"Bearer {data['refresh_token']}"}

    response = await client.delete("logout", headers=token_auth_headers)
    assert response.status_code == HTTPStatus.OK
    response = await client.delete("logout", headers=token_auth_headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = await client.post("refresh", headers=auth_refresh_headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio(scope="session")
async def test_logout_all(client, create_token_user):
    # create 2 active session
    response = await client.post("login", data=token_user_credentials)
    data = response.json()
    auth_access_headers1 = {"Authorization": f"Bearer {data['access_token']}"}
    auth_refresh_headers1 = {"Authorization": f"Bearer {data['refresh_token']}"}

    response = await client.post("login", data=token_user_credentials)
    data = response.json()
    auth_access_headers2 = {"Authorization": f"Bearer {data['access_token']}"}
    auth_refresh_headers2 = {"Authorization": f"Bearer {data['refresh_token']}"}

    # logout all
    response = await client.delete("logout_all_device", headers=auth_access_headers2)
    assert response.status_code == HTTPStatus.OK

    # check 2 session
    response = await client.delete("logout", headers=auth_access_headers1)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = await client.post("refresh", headers=auth_refresh_headers1)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = await client.delete("logout", headers=auth_access_headers2)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = await client.post("refresh", headers=auth_refresh_headers2)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio(scope="session")
async def test_refresh(client, create_token_user):  # noqa
    response = await client.post("login", data=token_user_credentials)
    data = response.json()
    auth_access_headers = {"Authorization": f"Bearer {data['access_token']}"}
    auth_refresh_headers = {"Authorization": f"Bearer {data['refresh_token']}"}

    # check need refresh token
    response = await client.post("refresh", headers=auth_access_headers)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # refresh token
    response = await client.post("refresh", headers=auth_refresh_headers)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    new_auth_access_headers = {"Authorization": f"Bearer {data['access_token']}"}
    new_auth_refresh_headers = {"Authorization": f"Bearer {data['refresh_token']}"}

    # check revoke old tokens
    response = await client.delete("logout", headers=auth_access_headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = await client.post("refresh", headers=auth_refresh_headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # check new tokens
    response = await client.get(
        "check_role",
        params={"role": "test"},
        headers=new_auth_access_headers,
    )
    assert response.status_code == HTTPStatus.OK
    response = await client.post("refresh", headers=new_auth_refresh_headers)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio(scope="session")
async def test_check_role(client, helper_auth_headers, auth_headers):
    params = {"role": "admin"}
    response = await client.get(
        "/check_role",
        params=params,
        headers=helper_auth_headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.text == "false"

    response = await client.get("/check_role", params=params, headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.text == "true"


@pytest.mark.asyncio(scope="session")
async def test_access_token_payload(helper_tokens, helper_uuid):  # noqa
    raw_token_payload = jwt.decode(
        helper_tokens["access_token"],
        options={"verify_signature": False},
    )
    token_payload = AccessTokenPayload(**raw_token_payload)
    assert token_payload.sub == helper_uuid

    # test not before
    time_now = time.time()
    assert int(token_payload.nbf) < time_now
    assert time_now - int(token_payload.exp) < 10  # check delay sec
    assert token_payload.nbf == token_payload.iat

    # access fields
    assert token_payload.type == "access"

    # test expire time
    max_exp_time = datetime.now() + timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN")),
    )
    assert token_payload.exp <= int(time.mktime(max_exp_time.timetuple()))
    # check delay sec
    assert time.mktime(max_exp_time.timetuple()) - int(token_payload.exp) < 20


@pytest.mark.asyncio(scope="session")
async def test_refresh_token_payload(helper_tokens, helper_uuid):  # noqa
    raw_token_payload = jwt.decode(
        helper_tokens["refresh_token"],
        options={"verify_signature": False},
    )
    token_payload = BaseTokenPayload(**raw_token_payload)
    assert token_payload.sub == helper_uuid

    # test not before
    time_now = time.time()
    assert int(token_payload.nbf) < time_now
    assert time_now - int(token_payload.exp) < 10  # check delay sec
    assert token_payload.nbf == token_payload.iat

    # refresh fields
    assert token_payload.type == "refresh"

    # test expire time
    max_exp_time = datetime.now() + timedelta(
        hours=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_HOUR")),
    )
    assert token_payload.exp <= int(time.mktime(max_exp_time.timetuple()))
    # check delay sec
    assert time.mktime(max_exp_time.timetuple()) - int(token_payload.exp) < 20


@pytest.mark.asyncio(scope="session")
async def test_jti_payload(helper_tokens):  # noqa
    raw_access_token_payload = jwt.decode(
        helper_tokens["access_token"],
        options={"verify_signature": False},
    )
    access_token_payload = BaseTokenPayload(**raw_access_token_payload)
    raw_refresh_token_payload = jwt.decode(
        helper_tokens["refresh_token"],
        options={"verify_signature": False},
    )
    refresh_token_payload = BaseTokenPayload(**raw_refresh_token_payload)
    assert access_token_payload.jti == refresh_token_payload.jti
