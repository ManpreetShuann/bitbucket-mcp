from __future__ import annotations

import json

import respx
from httpx import Response
from mcp.server.fastmcp import FastMCP

import pytest

from bitbucket_mcp.client import BitbucketClient
from bitbucket_mcp.tools.users import register_tools
from tests.conftest import BASE_URL, SAMPLE_USER, TOKEN, paged_response


@pytest.fixture()
def setup():
    client = BitbucketClient(BASE_URL, TOKEN)
    mcp = FastMCP("test")
    register_tools(mcp, client)
    tools = {t.name: t.fn for t in mcp._tool_manager._tools.values()}
    return client, tools


USERS_PREFIX = "/rest/api/1.0/users"


class TestFindUser:
    async def test_returns_users(self, setup):
        _, tools = setup
        data = paged_response([SAMPLE_USER])
        with respx.mock(base_url=BASE_URL) as router:
            route = router.get(USERS_PREFIX).mock(return_value=Response(200, json=data))
            result = await tools["find_user"](filter="jsmith")
        parsed = json.loads(result)
        assert parsed["values"][0]["name"] == "jsmith"
        assert "filter=jsmith" in str(route.calls[0].request.url)

    async def test_pagination_params(self, setup):
        _, tools = setup
        data = paged_response([])
        with respx.mock(base_url=BASE_URL) as router:
            route = router.get(USERS_PREFIX).mock(return_value=Response(200, json=data))
            await tools["find_user"](filter="test", start=10, limit=5)
        url = str(route.calls[0].request.url)
        assert "start=10" in url
        assert "limit=5" in url

    async def test_empty_filter_returns_error(self, setup):
        _, tools = setup
        result = await tools["find_user"](filter="")
        assert "Error" in result
        assert "empty" in result

    async def test_error_returns_string(self, setup):
        _, tools = setup
        error_body = {"errors": [{"message": "Unauthorized"}]}
        with respx.mock(base_url=BASE_URL) as router:
            router.get(USERS_PREFIX).mock(return_value=Response(401, json=error_body))
            result = await tools["find_user"](filter="test")
        assert "Error" in result
        assert "401" in result
