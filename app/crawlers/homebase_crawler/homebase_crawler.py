import urllib.parse
from typing import Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, clean_text

SOURCE_IDENTIFIER = "Homebase"
SOURCE_DESCRIPTION = (
    "Homebase offers home enhancement, garden supplies, decorating, and DIY products."
)


class ProductDetailResponse(BaseModel):
    source: Literal[SOURCE_IDENTIFIER] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £10.99)."
    )
    detail: str = Field(
        description="Comprehensive product specifications or item details in HTML format."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product."
    )


async def product_detail(url: str) -> ProductDetailResponse:
    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    # Title is in h1.name
    title = selector.css("h1.name::text").get() or ""
    # Price for detail is in .pdp-price
    price = (
        selector.css(".pdp-price::text").get()
        or selector.css("[itemprop='price']::attr(content)").get()
        or ""
    )

    # If title still empty, try data attribute on a parent div
    if not title:
        title = (
            selector.css(".product-details-container::attr(data-product-name)").get()
            or ""
        )

    promo_node = selector.css(".product-promo")
    promo_text = (
        clean_text(promo_node[0].css("*::text").getall()) if promo_node else None
    )

    return ProductDetailResponse(
        title=title.strip(),
        price=price.strip(),
        detail=clean_html(selector.css(".product-description").get()),
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
    query = urllib.parse.urlencode(
        {
            "text": keyword,
        }
    )
    url = f"{config.HOMEBASE_URL}/search?{query}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)
    results = []

    for item in selector.css(".product-item"):
        title = (
            item.css("::attr(data-product-name)").get()
            or item.css("a.product-link.name::text").get()
            or ""
        )
        url_path = (
            item.css("::attr(data-url)").get()
            or item.css("a.product-link.name::attr(href)").get()
            or ""
        )
        price = (
            item.css("::attr(data-price-formatted-value)").get()
            or item.css(".price::text").get()
            or ""
        )

        results.append(
            ProductSearchResponse(
                title=title.strip(),
                price=price.strip(),
                url=f"{config.HOMEBASE_URL}{url_path}" if url_path else "",
            )
        )

    return results
