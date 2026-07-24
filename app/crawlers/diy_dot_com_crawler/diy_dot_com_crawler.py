import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, remove_spaces

SOURCE_IDENTIFIER: Final = "B&Q"
SOURCE_DESCRIPTION = "B&Q offers DIY tools, garden supplies, home improvement products, and general hardware."


class ProductDetailResponse(BaseModel):
    source: Literal["B&Q"] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £55.00)."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML format."
    )
    description: str = Field(
        description="A brief text summary of the product's key details."
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
        )
        or "",
        price=selector.css("[data-testid='product-price']::text").get() or "",
        detail=clean_html(selector.css("#product-details").get()),
        promo=selector.xpath(
            '//a[@data-testid="promotion-link"]/preceding-sibling::p/text()'
        ).get(),
        description=remove_spaces(
            selector.xpath(
                '//div[@id="product-details"]/preceding-sibling::p/text()'
            ).get()
            or ""
        )
        or "",
    )


class ProductSearchResponse(BaseModel):
    source: Literal["B&Q"] = Field(
        description="The source of the search result.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(
        description="The commercial name of the product as shown in search results."
    )
    price: str = Field(
        description="The current retail price, including currency symbol (e.g., £1.99)."
    )
    url: str = Field(
        description="The relative or absolute URL pointing directly to the product detail page."
    )
    promo: str | None = Field(
        description="Any active promotional offer for the item in search results, if present."
    )


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    search_url = f"{config.DIY_DOT_COM_URL}/search?term={urllib.parse.quote(keyword)}"

    async with http_client.create_client() as client:
        response = await client.get(search_url)

    selector = Selector(text=response.text)

    results = []
    for product in selector.css("[data-testid='product']"):
        product_url = product.css("[data-testid='product-link']::attr(href)").get()
        title = product.css("[data-testid='product-name']::text").get() or ""
        price = product.css("[data-testid='product-price']::text").get() or ""
        promo = product.css("[data-testid='promotion-msg']::text").get()

        results.append(
            ProductSearchResponse(
                title=remove_spaces(title) or "",
                price=price,
                url=f"{config.DIY_DOT_COM_URL}{product_url}" if product_url else "",
                promo=promo,
            )
        )

    return results
