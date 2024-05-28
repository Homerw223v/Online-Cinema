from http import HTTPStatus

import pytest
from test_data.metrics_test_data import correct_metrics, not_correct_metrics


@pytest.mark.parametrize(
    "query_data",
    [
        (correct_metrics[0]),
        (correct_metrics[1]),
        (correct_metrics[2]),
        (correct_metrics[3]),
    ],
)
@pytest.mark.asyncio
async def test_metrics_positive_responses(post_aiohttp_response, query_data):
    """
    Test negative case of API calls to '/api/v1/metrics' endpoint with parameters query_data.
    """
    body, status, _ = await post_aiohttp_response(
        "/api/v1/metrics",
        query_data,
    )

    assert status == HTTPStatus.OK


@pytest.mark.parametrize(
    "query_data, loc, msg",
    [
        (not_correct_metrics[0], ["body", "url"], "Field required"),
        (not_correct_metrics[1], ["body", "information"], "Field required"),
    ],
)
@pytest.mark.asyncio
async def test_metrics_negative_responses(
    post_aiohttp_response,
    query_data,
    loc,
    msg,
):
    """
    Test negative case of API calls to '/api/v1/metrics' endpoint with parameters query_data.
    """
    body, status, _ = await post_aiohttp_response(
        "/api/v1/metrics",
        query_data,
    )

    assert status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert body["detail"][0]["loc"] == loc
    assert body["detail"][0]["msg"] == msg
