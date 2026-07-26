import html
import json
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
        description="Any active promotional offers or discounts associated with the product.",
        default=None,
    )


class ProductDetailResponse(BaseModel):
    source: Literal["Robert Dyas"] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML or text format.",
        default="",
    )
    description: str = Field(
        description="A brief text summary of the product's key details and features.",
        default="",
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product.",
        default=None,
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


async def product_detail(product_id_or_url: str) -> ProductDetailResponse:
    if product_id_or_url.startswith("http://") or product_id_or_url.startswith(
        "https://"
    ):
        url = product_id_or_url
    elif product_id_or_url.startswith("/"):
        url = f"{config.ROBERT_DYAS_URL}{product_id_or_url}"
    else:
        url = f"{config.ROBERT_DYAS_URL}/{product_id_or_url}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    selector = Selector(text=response.text)

    title = ""
    price = ""
    description = ""
    detail = ""
    promo: str | None = None

    for script_text in selector.css(
        'script[type="application/ld+json"]::text'
    ).getall():
        try:
            data = json.loads(script_text)
            if isinstance(data, dict) and data.get("@type") in [
                "Product",
                "http://schema.org/Product",
            ]:
                if not title and data.get("name"):
                    title = html.unescape(str(data["name"])).strip()
                if not description and data.get("description"):
                    description = html.unescape(str(data["description"])).strip()
                offers = data.get("offers")
                if isinstance(offers, list) and offers:
                    offer = offers[0]
                elif isinstance(offers, dict):
                    offer = offers
                else:
                    offer = {}

                if offer:
                    if not price and offer.get("price"):
                        currency_symbol = (
                            "£" if offer.get("priceCurrency") == "GBP" else ""
                        )
                        price = f"{currency_symbol}{offer['price']}"
        except Exception:
            pass

    if not title:
        raw_title = selector.css(
            "h1.page-title span[itemprop='name']::text, h1.page-title span::text, h1.page-title::text, h1::text"
        ).get()
        title = html.unescape(raw_title).strip() if raw_title else ""

    if not price:
        raw_price = selector.css(
            "[data-price-type='finalPrice'] .price::text, .price-final_price .price::text, .price-box .price::text, span.price::text"
        ).get()
        price = raw_price.strip() if raw_price else ""

    if not description:
        desc_parts = selector.css(
            ".product.attribute.description .value::text, #description .value::text, meta[name='description']::attr(content)"
        ).getall()
        description = html.unescape(
            " ".join(d.strip() for d in desc_parts if d.strip())
        )

    specs_list = []
    for tr in selector.css(
        "#product-attribute-specs-table tr, .additional-attributes tr"
    ):
        th = tr.css("th::text").get()
        td = tr.css("td::text, td *::text").getall()
        if th:
            val = " ".join(t.strip() for t in td if t.strip())
            specs_list.append(f"{th.strip()}: {val}")
    if specs_list:
        detail = "\n".join(specs_list)
    elif description and "Specifications" in description:
        spec_idx = description.find("Specifications")
        detail = description[spec_idx:].strip()

    description = html.unescape(description).strip()
    detail = html.unescape(detail).strip()

    raw_promo = selector.css(
        ".product-info-promo::text, .product-label::text, .ribbon::text, .action-ribbon::text"
    ).get()
    if raw_promo and raw_promo.strip():
        promo = html.unescape(raw_promo).strip()

    return ProductDetailResponse(
        title=title,
        price=price,
        detail=detail,
        description=description,
        promo=promo,
    )
