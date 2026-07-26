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
    with open("mcp.json") as f:
        yield json.load(f)["mcpServers"]


@pytest.fixture
async def mcp_client_session(mcp_server_config):
    env = get_default_environment()
    import os

    if "BROWSERLESS_API_KEY" in os.environ:
        env["BROWSERLESS_API_KEY"] = os.environ["BROWSERLESS_API_KEY"]
    if "BROWSER_PROVIDER" in os.environ:
        env["BROWSER_PROVIDER"] = os.environ["BROWSER_PROVIDER"]

    server_params = StdioServerParameters(
        command=mcp_server_config["test"]["command"],
        args=mcp_server_config["test"]["args"],
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


async def test_robert_dyas_mcp_direct_routing(monkeypatch):
    """Direct unit test for Robert Dyas MCP tool routing without external network calls."""
    from unittest.mock import AsyncMock

    import app.crawlers.robert_dyas_crawler as robert_dyas_crawler
    from app.crawlers.robert_dyas_crawler import (
        ProductDetailResponse,
        ProductSearchResponse,
    )
    from app.mcp_server import (
        ProductDetailRequest,
        ProductsSearchRequest,
        get_product_detail,
        get_providers,
        search_products,
    )

    # 1. Test get_providers contains Robert Dyas
    providers = await get_providers()
    robert_dyas_provider = next(
        (p for p in providers if p.name == Provider.ROBERT_DYAS.value), None
    )
    assert robert_dyas_provider is not None
    assert "Robert Dyas" in robert_dyas_provider.name
    assert len(robert_dyas_provider.description) > 0

    # 2. Test search_products routing for Robert Dyas
    mock_search_result = [
        ProductSearchResponse(
            title="Robert Dyas Drill",
            price="£29.99",
            url="https://www.robertdyas.co.uk/drill",
        )
    ]
    mock_search = AsyncMock(return_value=mock_search_result)
    monkeypatch.setattr(robert_dyas_crawler, "product_search", mock_search)

    search_resp = await search_products(
        provider=Provider.ROBERT_DYAS,
        request=ProductsSearchRequest(keyword="drill"),
    )
    mock_search.assert_called_once_with("drill")
    assert search_resp == mock_search_result

    # 3. Test get_product_detail routing for Robert Dyas
    mock_detail_result = ProductDetailResponse(
        title="Robert Dyas Drill",
        price="£29.99",
        detail="A powerful cordless drill",
        description="Great drill for home DIY projects.",
    )
    mock_detail = AsyncMock(return_value=mock_detail_result)
    monkeypatch.setattr(robert_dyas_crawler, "product_detail", mock_detail)

    detail_resp = await get_product_detail(
        provider=Provider.ROBERT_DYAS,
        request=ProductDetailRequest(product_url="https://www.robertdyas.co.uk/drill"),
    )
    mock_detail.assert_called_once_with("https://www.robertdyas.co.uk/drill")
    assert detail_resp == mock_detail_result
