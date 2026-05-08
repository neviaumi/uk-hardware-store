import urllib.parse
from typing import Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, clean_text, remove_spaces

SOURCE_IDENTIFIER = "Screwfix"
SOURCE_DESCRIPTION = "Screwfix offers trade tools, plumbing, electrical, bathrooms, and heating products."


class ProductDetailResponse(BaseModel):
    source: Literal[SOURCE_IDENTIFIER] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £9.99)."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML format."
    )
    description: str = Field(
        description="A brief text summary of the product's features and features."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product."
    )


async def product_detail(url: str) -> ProductDetailResponse:

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    promo_message = selector.css("[data-qaid='promo-message']::text").get()
    bulk_saves = clean_html(selector.css("[data-qaid='bulk-save-table']").get())

    price_parts = selector.css("[data-qaid='pdp-price'] *::text").getall()
    price = "".join(
        [p.strip() for p in price_parts if p.strip() and "inc" not in p.lower()]
    )

    return ProductDetailResponse(
        title=remove_spaces(
            selector.css("[data-qaid='pdp-product-name'] *::text").get() or ""
        ),
        price=price,
        description=selector.css("[data-qaid='pdp-product-overview']::text").get()
        or "",
        detail=clean_html(selector.css("[data-qaid='pdp-tabpanel-2'] table").get())
        or "",
        promo=promo_message if promo_message is not None else bulk_saves,
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
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product."
    )
    description: str = Field(
        description="A brief overview or bullet points describing the product."
    )


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({"search": keyword})
    url = f"{config.SCREWFIX_URL}/search?{query}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    results = []
    for product in selector.css("[data-qaid='product-card']"):
        product_url = product.css("[data-qaid='product_description']::attr(href)").get()
        title = product.css("[data-qaid='product_description'] span::text").get()
        price = product.css("[data-qaid='price']::text").get()

        # Context-level selectors from original crawler
        promo_message_ctx = remove_spaces(
            clean_text(product.css("[data-qaid='promo-banner'] *::text").getall())
        )
        bulk_saves_ctx = remove_spaces(
            clean_text(product.css("[data-qaid='bulksave-banner'] *::text").getall())
        )

        description = clean_html(product.css("[data-qaid='bullets']").get())

        results.append(
            ProductSearchResponse(
                title=remove_spaces(title) if title else "",
                price=price or "",
                url=f"{config.SCREWFIX_URL}{product_url}" if product_url else "",
                promo=promo_message_ctx if promo_message_ctx else bulk_saves_ctx,
                description=description or "",
            )
        )

    return results
