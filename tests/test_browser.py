import pytest

from app.crawlers.browser import create_browser
from tests import integration_test

pytestmark = pytest.mark.anyio


@integration_test
async def test_create_browser():
    async with create_browser() as browser:
        page = await browser.new_page()
        await page.goto("https://www.google.com/")
        assert await page.title() == "Google"
