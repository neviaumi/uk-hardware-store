import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client

SOURCE_IDENTIFIER: Final = "Robert Dyas"
SOURCE_DESCRIPTION = "Robert Dyas offers home electricals, garden furniture, DIY tools, kitchenware, and hardware."


class ProductSearchResponse(BaseModel):
    source: Literal["Robert Dyas"] = Field(
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
    url = f"{config.ROBERT_DYAS_URL}/catalogsearch/result/?{query}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    results = []
    for item in selector.css(".product-item-info"):
        raw_title = item.css(
            "a.product-item-link::text, .product-item-name a::text"
        ).get()
        title = raw_title.strip() if raw_title else ""

        raw_url = item.css(
            "a.product-item-link::attr(href), .product-item-name a::attr(href)"
        ).get()
        if raw_url:
            product_url = (
                raw_url
                if raw_url.startswith("http")
                else f"{config.ROBERT_DYAS_URL}{raw_url}"
            )
        else:
            product_url = ""

        raw_price = item.css(
            "[data-price-type='finalPrice'] .price::text, .price::text"
        ).get()
        price = raw_price.strip() if raw_price else ""

        raw_promo = item.css(
            ".product-label::text, .ribbon::text, .action-ribbon::text, .special-price::text"
        ).get()
        promo = raw_promo.strip() if raw_promo else None

        if title or product_url:
            results.append(
                ProductSearchResponse(
                    title=title,
                    price=price,
                    url=product_url,
                    promo=promo,
                )
            )

    return results
