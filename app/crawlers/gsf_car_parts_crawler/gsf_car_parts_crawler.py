import asyncio
import html
import json
import re
import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, remove_spaces

SOURCE_IDENTIFIER: Final = "GSF Car Parts"
SOURCE_DESCRIPTION = (
    "GSF Car Parts offers car parts, tools, accessories, lubricants, and hardware."
)


class ProductDetailResponse(BaseModel):
    source: Literal["GSF Car Parts"] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £45.54)."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML format."
    )
    description: str = Field(
        description="A brief text summary of the product's key details."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product.",
        default=None,
    )


class ProductSearchResponse(BaseModel):
    source: Literal["GSF Car Parts"] = Field(
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


async def _fetch_with_retry(url: str, retries: int = 2):
    async with http_client.create_client(impersonate="chrome120") as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response
        for attempt in range(retries):
            await asyncio.sleep(0.5)
            response = await client.get(url)
            if response.status_code == 200:
                return response
        return response


async def product_detail(url: str) -> ProductDetailResponse:
    response = await _fetch_with_retry(url)

    text = response.text
    selector = Selector(text=text)

    # 1. Parse via embedded JSON-LD Product schema
    prod_data: dict | None = None
    for script_text in selector.css(
        'script[type="application/ld+json"]::text'
    ).getall():
        try:
            data = json.loads(script_text)
            if isinstance(data, dict) and data.get("@type") == "Product":
                prod_data = data
                break
        except Exception:
            pass

    title = ""
    price = ""
    description = ""
    detail = ""
    promo: str | None = None

    if prod_data:
        raw_name = prod_data.get("name", "")
        title = html.unescape(raw_name).strip() if raw_name else ""

        offers = prod_data.get("offers")
        if isinstance(offers, dict):
            raw_price = offers.get("price")
            if raw_price:
                price = (
                    f"£{raw_price}"
                    if not str(raw_price).startswith("£")
                    else str(raw_price)
                )

            specs = offers.get("priceSpecification", [])
            if isinstance(specs, list):
                for spec in specs:
                    if (
                        isinstance(spec, dict)
                        and spec.get("priceType")
                        == "https://schema.org/StrikethroughPrice"
                    ):
                        strikethrough = spec.get("price")
                        if strikethrough:
                            promo = f"Was £{strikethrough}"
                            break

        raw_desc = prod_data.get("description", "")
        if raw_desc:
            description_text = clean_html(raw_desc)
            description = remove_spaces(description_text) if description_text else ""
            detail = clean_html(raw_desc) or ""

    # Fallbacks if JSON-LD is missing
    if not title:
        raw_h1 = selector.css("h1::text").get()
        if raw_h1:
            title = raw_h1.strip()
        else:
            raw_title = selector.css("title::text").get()
            title = raw_title.split("|")[0].strip() if raw_title else ""

    if not price:
        raw_price = selector.css("[class*='price']::text, .price::text").get()
        if raw_price:
            price = raw_price.strip()

    if not description:
        raw_meta = selector.css("meta[name='description']::attr(content)").get()
        description = raw_meta.strip() if raw_meta else ""

    return ProductDetailResponse(
        title=title,
        price=price,
        detail=detail,
        description=description,
        promo=promo,
    )


def _parse_search_results(text: str) -> list[ProductSearchResponse]:
    selector = Selector(text=text)
    results: list[ProductSearchResponse] = []
    seen_urls: set[str] = set()

    for link in selector.css('a[href*="/products/"]'):
        href = link.css("::attr(href)").get()
        if not href or href in seen_urls:
            continue

        product_url = (
            f"{config.GSF_CAR_PARTS_URL}{href}" if href.startswith("/") else href
        )
        seen_urls.add(href)

        container = link.xpath(
            './ancestor::div[contains(@class, "Card") or contains(@class, "product") or contains(@class, "col") or contains(@class, "item")][1]'
        )
        if not container:
            container = link.xpath("..")

        texts = [t.strip() for t in container.css("*::text").getall() if t.strip()]

        promo: str | None = None
        savings_val: str | None = None
        for i, t in enumerate(texts):
            if (
                t.lower() == "save"
                and i + 1 < len(texts)
                and texts[i + 1].startswith("£")
            ):
                savings_val = texts[i + 1]
                promo = f"Save {savings_val}"
                break

        title = ""
        link_title = link.css("::text").get()
        if link_title and link_title.strip():
            title = link_title.strip()
        else:
            for t in texts:
                if t.lower() not in [
                    "save",
                    "add to basket",
                    "add bundle to basket",
                ] and not t.startswith("£"):
                    title = t
                    break

        price = ""
        for t in texts:
            if re.match(r"^£\s*[\d.]+$", t):
                if savings_val and t == savings_val:
                    continue
                price = t
                break

        if title and price:
            results.append(
                ProductSearchResponse(
                    title=title,
                    price=price,
                    url=product_url,
                    promo=promo,
                )
            )

    return results


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({"q": keyword})
    url = f"{config.GSF_CAR_PARTS_URL}/catalogsearch/result/?{query}"

    response = await _fetch_with_retry(url)

    results = _parse_search_results(response.text)
    if not results and " " in keyword:
        for word in reversed(keyword.split()):
            if len(word) > 2:
                results = await product_search(word)
                if results:
                    break
    return results


async def car_parts_product_search(
    car_plate: str, keyword: str
) -> list[ProductSearchResponse]:
    query = urllib.parse.urlencode({"q": keyword, "vrm": car_plate.strip().upper()})
    url = f"{config.GSF_CAR_PARTS_URL}/catalogsearch/result/?{query}"

    response = await _fetch_with_retry(url)

    return _parse_search_results(response.text)
