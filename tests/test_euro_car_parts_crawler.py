import pytest

from app.crawlers.euro_car_parts_crawler import euro_car_parts_crawler
from tests import integration_test
from tests.crawler import TEST_SEARCH_KEYWORD
from tests.mock_server import mock_response_data

pytestmark = pytest.mark.anyio


async def test_product_search(mock_server):
    mock_server.expect_request("/eurocarparts/search/oil").respond_with_data(
        mock_response_data("product_search_euro_car_parts.html")
    )
    results = await euro_car_parts_crawler.product_search("oil")
    assert isinstance(results, list)
    assert len(results) == 19
    first_item = results[0]
    assert first_item.title == "Sealey Oil Transfer Pump 12V"
    assert first_item.price == "£45.54"
    assert first_item.url.startswith(mock_server.url_for("/eurocarparts"))
    assert first_item.url.endswith("/p/SEATP9312")
    assert first_item.source == "Euro Car Parts"


@integration_test
async def test_euro_car_parts_live_search():
    results = await euro_car_parts_crawler.product_search(TEST_SEARCH_KEYWORD)
    assert isinstance(results, list)
    assert len(results) > 0
    first_item = results[0]
    assert first_item.title
    assert first_item.price
    assert first_item.url
    assert first_item.source == "Euro Car Parts"
