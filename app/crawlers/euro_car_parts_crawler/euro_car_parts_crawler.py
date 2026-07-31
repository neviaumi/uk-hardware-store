import html
import json
import re
import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client

SOURCE_IDENTIFIER: Final = "Euro Car Parts"
SOURCE_DESCRIPTION = (
    "Euro Car Parts offers car parts, tools, accessories, lubricants, and hardware."
)


class ProductSearchResponse(BaseModel):
    source: Literal["Euro Car Parts"] = Field(
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
        description="Any active promotional offers or discounts associated with the product.",
        default=None,
    )


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"{config.EURO_CAR_PARTS_URL}/search/{encoded_keyword}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    text = response.text
    results: list[ProductSearchResponse] = []
    seen_skus: set[str] = set()

    # 1. Parse via Next.js RSC payload / JSON hits data
    hit_blocks = re.findall(
        r"\"sku\":\"([^\"]+)\".*?\"(?:title\.en-GB|slugName)\":\"([^\"]+)\".*?\"price\":\{\"price\":([\d.]+)",
        text,
    )
    for sku, raw_title, price_val in hit_blocks:
        if sku in seen_skus:
            continue
        seen_skus.add(sku)

        try:
            title = json.loads(f'"{raw_title}"')
        except Exception:
            title = html.unescape(raw_title).strip()

        price = f"£{price_val}" if price_val else ""
        product_url = f"{config.EURO_CAR_PARTS_URL}/p/{sku}"

        if title or product_url:
            results.append(
                ProductSearchResponse(
                    title=title,
                    price=price,
                    url=product_url,
                )
            )

    # 2. Fallback via DOM parsing if JSON payload hits are empty
    if not results:
        selector = Selector(text=text)
        for item in selector.css(
            "[class*='ProductCard'], [class*='productCard'], [class*='product-card'], article"
        ):
            raw_title = item.css(
                "h2::text, h3::text, a[class*='title']::text, [class*='title']::text"
            ).get()
            title = html.unescape(raw_title).strip() if raw_title else ""

            raw_url = item.css("a::attr(href)").get()
            if raw_url:
                product_url = (
                    raw_url
                    if raw_url.startswith("http")
                    else f"{config.EURO_CAR_PARTS_URL}{raw_url}"
                )
            else:
                product_url = ""

            raw_price = item.css("[class*='price']::text, [class*='Price']::text").get()
            price = raw_price.strip() if raw_price else ""

            if title or product_url:
                results.append(
                    ProductSearchResponse(
                        title=title,
                        price=price,
                        url=product_url,
                    )
                )

    return results
