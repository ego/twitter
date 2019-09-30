"""API test."""
import asyncio
import logging

import pytest

API_URLS = [
    "/api/v1/tweets/",
    "/api/v1/tweets/1/",
    "/api/v1/statistic/top/hashtags/2019-09-09/2019-09-10/",
    "/api/v1/statistic/top/authors/2019-09-09/2019-09-10/",
    "/api/v1/statistic/tweets/2019-09-09/2019-09-10/",
]


@pytest.mark.parametrize(
    "test_input,expected", list(zip(API_URLS, [200] * len(API_URLS)))
)
async def test_api_urls(pg_engine, test_app, test_input, expected):
    """Test API URLS."""
    await asyncio.sleep(3)
    count = 10
    while count > 0:
        logging.debug("test_tweets %s", count)
        resp = await test_app.request("GET", test_input)
        assert resp.status == expected
        json_data = await resp.json()
        if not json_data:
            count -= 1
            await asyncio.sleep(5)
        else:
            break
