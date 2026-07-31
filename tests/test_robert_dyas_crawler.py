import pytest

from app.crawlers.robert_dyas_crawler import robert_dyas_crawler
from tests import integration_test
from tests.crawler import TEST_SEARCH_KEYWORD
from tests.mock_server import mock_response_data

pytestmark = pytest.mark.anyio


async def test_product_search(mock_server):
    mock_server.expect_request("/robertdyas/catalogsearch/result/").respond_with_data(
        mock_response_data("product_search_robert_dyas.html")
    )
    results = await robert_dyas_crawler.product_search(TEST_SEARCH_KEYWORD)
    assert isinstance(results, list)
    assert len(results) == 24
    first_item = results[0]
    assert (
        first_item.title
        == "Costway Low Back Padded Boat Seat with 4 Bolts and Thick Sponge Padding"
    )
    assert first_item.price == "£49.99"
    assert (
        first_item.url
        == "https://www.robertdyas.co.uk/costway-low-back-padded-boat-seat-with-4-bolts-and-thick-sponge-padding"
    )
    assert first_item.source == "Robert Dyas"


@integration_test
async def test_robert_dyas_live_search():
    results = await robert_dyas_crawler.product_search(TEST_SEARCH_KEYWORD)
    assert isinstance(results, list)
    assert len(results) > 0
    first_item = results[0]
    assert first_item.title
    assert first_item.price
    assert first_item.url
    assert first_item.source == "Robert Dyas"


async def test_product_detail(mock_server):
    path = "/robertdyas/vonhaus-cordless-multi-tool-with-carry-case"
    mock_server.expect_request(path).respond_with_data(
        mock_response_data("product_detail_robert_dyas.html")
    )
    url = mock_server.url_for(path)
    result = await robert_dyas_crawler.product_detail(url)
    assert result.title == "Vonhaus Cordless Multi Tool with Carry Case"
    assert result.price == "£36.99"
    assert "Vonhaus Cordless Multi Tool with Carry Case" in result.description
    assert result.source == "Robert Dyas"
    assert result.promo == "Save £11.00"


@integration_test
async def test_robert_dyas_live_product_detail():
    url = "https://www.robertdyas.co.uk/vonhaus-cordless-multi-tool-with-carry-case"
    result = await robert_dyas_crawler.product_detail(url)
    assert result.title
    assert result.price
    assert result.source == "Robert Dyas"
