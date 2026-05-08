import urllib.parse
from typing import Literal

from pydantic import BaseModel, Field

import app.config as config
from app.crawlers.browser import create_browser
from app.crawlers.utils import clean_html, clean_text

SOURCE_IDENTIFIER = "The Range"


class ProductDetailResponse(BaseModel):
    source: Literal[SOURCE_IDENTIFIER] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML format."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product."
    )


async def product_detail(url: str) -> ProductDetailResponse:
    async with create_browser() as context:
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_selector("h1#product-dyn-title", timeout=90000)

        # Title is in h1#product-dyn-title
        title_locator = page.locator("h1#product-dyn-title")
        title = (
            (await title_locator.inner_text())
            if await title_locator.count() > 0
            else ""
        )

        # Price for detail is in div#min_price
        price_locator = page.locator("#product-dyn-price #min_price")
        price = (
            (await price_locator.inner_text())
            if await price_locator.count() > 0
            else ""
        )

        promo_locator = page.locator("#product-price-saving")
        promo_text = None
        if await promo_locator.count() > 0:
            promo_text = clean_text(await promo_locator.all_inner_texts())

        desc_locators = page.locator("#product-dyn-desc, #product-specification")
        detail_html = ""
        count = await desc_locators.count()
        if count > 0:
            parts = []
            for i in range(count):
                parts.append(await desc_locators.nth(i).inner_html())
            detail_html = " ".join(parts)

        return ProductDetailResponse(
            title=title.strip(),
            price=price.strip(),
            detail=clean_html(detail_html),
            promo=promo_text,
        )


class ProductSearchResponse(BaseModel):
    source: Literal[SOURCE_IDENTIFIER] = Field(
        description="The source of the search result.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(
        description="The commercial name of the product as shown in search results."
    )
    price: str = Field(
        description="The current retail price, including the currency symbol."
    )
    url: str = Field(
        description="The absolute URL leading to the product's detail page."
    )


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({
        "q": keyword,
        "sort": "relevance",
        "attributes.Available_To_Order": "TRUE",
        "page": "1",
    })
    url = f"{config.THE_RANGE_URL}/search?{query}"

    async with create_browser() as context:
        page = await context.new_page()

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_selector(
            'article[data-testid="product-card"]', timeout=90000
        )

        product_cards = page.locator('article[data-testid="product-card"]')
        results = []

        for card in await product_cards.all():
            name_locator = card.locator('[data-testid="product-name"]')

            title = (
                (await name_locator.inner_text())
                if await name_locator.count() > 0
                else ""
            )
            url_path = (
                (await name_locator.get_attribute("href"))
                if await name_locator.count() > 0
                else ""
            )

            price_locator = card.locator('[class*="priceSection"] span')
            price = (
                (await price_locator.inner_text())
                if await price_locator.count() > 0
                else ""
            )

            results.append(
                ProductSearchResponse(
                    title=title.strip(),
                    price=price.strip(),
                    url=urllib.parse.urljoin(config.THE_RANGE_URL, url_path)
                    if url_path
                    else "",
                )
            )

    return results
