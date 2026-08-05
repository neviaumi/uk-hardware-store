import pytest

from app.crawlers.gsf_car_parts_crawler import gsf_car_parts_crawler
from tests.crawler import (
    TEST_CAR_PLATE,
    TEST_SEARCH_CAR_PART,
    TEST_SEARCH_KEYWORD,
)
from tests.mock_server import mock_response_data

pytestmark = pytest.mark.anyio


async def test_product_search(mock_server):
    mock_server.expect_request("/gsfcarparts/catalogsearch/result/").respond_with_data(
        mock_response_data("gsf_car_parts_search.html")
    )
    results = await gsf_car_parts_crawler.product_search(TEST_SEARCH_KEYWORD)
    assert isinstance(results, list)
    assert len(results) > 0
    first_item = results[0]
    assert first_item.source == "GSF Car Parts"
    assert first_item.title != ""
    assert first_item.price.startswith("£")
    assert first_item.url.startswith(mock_server.url_for("/gsfcarparts"))


async def test_car_parts_product_search(mock_server):
    mock_server.expect_request("/gsfcarparts/catalogsearch/result/").respond_with_data(
        mock_response_data("gsf_car_parts_search.html")
    )
    results = await gsf_car_parts_crawler.car_parts_product_search(
        TEST_CAR_PLATE, TEST_SEARCH_CAR_PART
    )
    assert isinstance(results, list)
    assert len(results) > 0
    first_item = results[0]
    assert first_item.source == "GSF Car Parts"
    assert first_item.title != ""
    assert first_item.price.startswith("£")
    assert first_item.url.startswith(mock_server.url_for("/gsfcarparts"))


async def test_product_detail(mock_server):
    path = "/gsfcarparts/products/autoglym-interior-kit"
    mock_server.expect_request(path).respond_with_data(
        mock_response_data("gsf_car_parts_detail.html")
    )
    url = mock_server.url_for(path)
    result = await gsf_car_parts_crawler.product_detail(url)
    assert result.source == "GSF Car Parts"
    assert "Autoglym Interior Kit" in result.title
    assert result.price.startswith("£")
    assert result.description != ""
    assert result.detail != ""
