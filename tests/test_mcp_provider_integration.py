import json

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    get_default_environment,
    stdio_client,
)

from app.mcp_server import Provider
from tests import skip_if_ci
from tests.crawler import TEST_SEARCH_KEYWORD

pytestmark = pytest.mark.anyio


@pytest.fixture
def mcp_server_config():
    with open(".agents/mcp_config.json") as f:
        yield json.load(f)["mcpServers"]


@pytest.fixture
async def mcp_client_session(mcp_server_config):
    env = get_default_environment()
    import os

    if "BROWSERLESS_API_KEY" in os.environ:
        env["BROWSERLESS_API_KEY"] = os.environ["BROWSERLESS_API_KEY"]
    if "BROWSER_PROVIDER" in os.environ:
        env["BROWSER_PROVIDER"] = os.environ["BROWSER_PROVIDER"]

    server_config = (
        mcp_server_config.get("uk-hardware-store-test")
        or mcp_server_config.get("uk-hardware-store")
        or list(mcp_server_config.values())[0]
    )
    if "env" in server_config:
        env.update(server_config["env"])

    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"],
        env=env,
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            yield session


PROVIDERS_TO_TEST = list(Provider)


@pytest.mark.parametrize("provider", PROVIDERS_TO_TEST)
@skip_if_ci
async def test_provider(mcp_client_session, provider):
    """Test the unified search_products tool across all providers."""
    # Call the search_products tool with the ProductsSearchRequest payload
    tool_result = await mcp_client_session.call_tool(
        "search_products",
        {"request": {"keyword": TEST_SEARCH_KEYWORD}, "provider": provider.value},
    )

    assert tool_result.isError is False, f"Tool call for {provider} should not error"
    response = tool_result.structuredContent.get("result", [])
    assert len(response) > 0, f"Tool call response for {provider} should not be empty"

    # Check that each product has expected fields
    for product in response:
        assert "title" in product
        assert "price" in product
        assert "url" in product

    first_product = response[0]
    tool_result = await mcp_client_session.call_tool(
        "get_product_detail",
        {"request": {"product_url": first_product["url"]}, "provider": provider.value},
    )
    assert tool_result.isError is False, f"Tool call for {provider} should not error"
    response = tool_result.structuredContent.get("result", {})
    assert "title" in response


async def test_unsupported_provider(mcp_client_session):
    tool_result = await mcp_client_session.call_tool(
        "search_products",
        {"request": {"keyword": TEST_SEARCH_KEYWORD}, "provider": "unsupported"},
    )
    assert tool_result.isError is True, (
        "Tool call for unsupported provider should error"
    )
    tool_result = await mcp_client_session.call_tool(
        "get_product_detail",
        {
            "request": {
                "product_url": "https://www.diy.com/products/hammer",
            },
            "provider": "unsupported",
        },
    )
    assert tool_result.isError is True, (
        "Tool call for unsupported provider should error"
    )


async def test_get_providers(mcp_client_session):
    """Test the get_providers tool returns name and description for all providers."""
    tool_result = await mcp_client_session.call_tool("get_providers", {})
    assert tool_result.isError is False, "Tool call for get_providers should not error"

    response = tool_result.structuredContent.get("result", [])
    assert len(response) == len(Provider), "get_providers should return all providers"

    for provider_info in response:
        assert "name" in provider_info
        assert "description" in provider_info
        assert len(provider_info["name"]) > 0
        assert len(provider_info["description"]) > 0
