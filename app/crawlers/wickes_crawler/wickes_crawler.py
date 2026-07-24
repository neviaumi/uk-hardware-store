import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, remove_spaces

SOURCE_IDENTIFIER: Final = "Wickes"
SOURCE_DESCRIPTION = "Wickes offers home improvement, DIY, trade building materials, and kitchen/bathroom fittings."


class ProductDetailResponse(BaseModel):
    source: Literal["Wickes"] = Field(
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

    raw_title = selector.css("title::text").get()
    title = (remove_spaces(raw_title.split("|")[0].strip()) if raw_title else "") or ""

    price = selector.css(".main-price__value::text").get()
    description = selector.css(".product-main-info__description::text").get()

    return ProductDetailResponse(
        title=title.strip() if title else "",
        price=price.strip() if price else "",
        description=description.strip() if description else "",
        detail=clean_html(selector.css(".additional-info").get()) or "",
        promo="".join(selector.css(".pdp-price__description *::text").getall()),
    )


class ProductSearchResponse(BaseModel):
    source: Literal["Wickes"] = Field(
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


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({"q": keyword})
    url = f"{config.WICKES_URL}/search?{query}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    results = []
    for product in selector.css("[data-product-code]"):
        product_url = product.css("a::attr(href)").get()
        promo = product.css(".products-list-v2__badge::text").get()
        title = product.css("a::attr(title)").get()
        price = product.css(".product-card__price-value::text").get()

        results.append(
            ProductSearchResponse(
                title=title.strip() if title else "",
                price=price.strip() if price else "",
                url=f"{config.WICKES_URL}{product_url}" if product_url else "",
                promo=promo.strip() if promo and "for" in promo else None,
            )
        )

    return results
