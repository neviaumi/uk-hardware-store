import urllib.parse
from typing import Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, remove_spaces

SOURCE_IDENTIFIER = "B&Q"
SOURCE_DESCRIPTION = "B&Q offers DIY tools, garden supplies, home improvement products, and general hardware."


class ProductDetailResponse(BaseModel):
    source: Literal[SOURCE_IDENTIFIER] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £25.00)."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or product details in HTML format."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product."
    )


async def product_detail(url: str) -> ProductDetailResponse:
    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    return ProductDetailResponse(
        title=remove_spaces(
            selector.css("[data-testid='product-name']::text").get() or ""
        ),
        price=selector.css("[data-testid='product-price']::text").get() or "",
        detail=clean_html(selector.css("#product-details").get()),
        promo=selector.xpath(
            '//a[@data-testid="promotion-link"]/preceding-sibling::p/text()'
        ).get(),
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
        description="A brief summary of any active promotion shown in the search snippet."
    )


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({"term": keyword})
    url = f"{config.DIY_DOT_COM_URL}/search?{query}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    results = []
    for product in selector.css("[data-testid='product']"):
        product_url = product.css("[data-testid='product-link']::attr(href)").get()
        title = product.css("[data-testid='product-name']::text").get() or ""
        price = product.css("[data-testid='product-price']::text").get() or ""
        promo = product.css("[data-testid='promotion-msg']::text").get()

        results.append(
            ProductSearchResponse(
                title=remove_spaces(title),
                price=price,
                url=f"{config.DIY_DOT_COM_URL}{product_url}" if product_url else "",
                promo=promo,
            )
        )

    return results
