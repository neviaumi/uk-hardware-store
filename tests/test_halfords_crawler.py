import pytest

from app.crawlers.halfords_crawler import car_parts_product_search, product_search
from tests import skip
from tests.crawler import TEST_SEARCH_CAR_PART, TEST_SEARCH_KEYWORD

pytestmark = pytest.mark.anyio


@skip
async def test_halfords_search():
    results = await product_search(TEST_SEARCH_KEYWORD)
    print(results)


async def test_halfords_car_parts_search():
    results = await car_parts_product_search("NX60OLA", TEST_SEARCH_CAR_PART)
    print(results)
