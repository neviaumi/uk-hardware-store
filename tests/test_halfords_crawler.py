import pytest

from app.crawlers.halfords_crawler import (
    car_parts_product_search,
    product_detail,
    product_search,
)
from tests import integration_test
from tests.crawler import TEST_SEARCH_CAR_PART, TEST_SEARCH_KEYWORD

pytestmark = pytest.mark.anyio


@integration_test
async def test_halfords_search():
    results = await product_search(TEST_SEARCH_KEYWORD)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first.title
    assert first.price
    assert first.url


@integration_test
async def test_halfords_car_parts_search():
    results = await car_parts_product_search("NX60OLA", TEST_SEARCH_CAR_PART)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first.title
    assert first.price
    assert first.url


@integration_test
async def test_halfords_product_detail():
    url = "https://www.halfords.com/motoring/car-parts/filtration/oil-filters/m%2Fknecht-oil-filter-501820154-20265420000057.html?isVrnSearch=true"
    result = await product_detail(url)
    assert result.title
    assert result.price
    assert result.source == "Halfords"
    assert result.description
    assert result.detail
    assert len(result.detail) > 0
