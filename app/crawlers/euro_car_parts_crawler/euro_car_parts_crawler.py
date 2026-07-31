import base64
import html
import json
import re
import urllib.parse
from typing import Final, Literal

from parsel import Selector
from pydantic import BaseModel, Field

import app.config as config
import app.crawlers.http_client as http_client
from app.crawlers.utils import clean_html, clean_text

SOURCE_IDENTIFIER: Final = "Euro Car Parts"
SOURCE_DESCRIPTION = (
    "Euro Car Parts offers car parts, tools, accessories, lubricants, and hardware."
)
_FIND_BY_PLATE_QUERY: Final = """query findByPlateNumber($plateNumber: String!) {
  findByPlateNumber(plateNumber: $plateNumber) {
    ... on VehicleInformation {
      manufacturer {
        id
        name
      }
      model {
        id
        name
      }
      vehicleAttributes {
        displayValue
        value
        key
        source
        displayName
        displayType
      }
    }
  }
}"""


class ProductDetailResponse(BaseModel):
    source: Literal["Euro Car Parts"] = Field(
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


async def product_detail(url: str) -> ProductDetailResponse:
    async with http_client.create_client() as client:
        response = await client.get(url)

    text = response.text
    selector = Selector(text=text)

    # 1. Title
    raw_h1 = selector.css("h1::text").get()
    title = raw_h1.strip() if raw_h1 else ""
    if not title:
        raw_og_title = selector.css("meta[property='og:title']::attr(content)").get()
        if raw_og_title:
            title = raw_og_title.split("|")[0].strip()
    if not title:
        raw_title = selector.css("title::text").get()
        title = raw_title.split("|")[0].strip() if raw_title else ""

    # 2. Price
    price = ""
    price_match = re.search(r"\"price\":\{\"price\":([\d.]+)", text) or re.search(
        r"\"amount\":([\d.]+)", text
    )
    if price_match:
        price = f"£{price_match.group(1)}"
    else:
        raw_price = selector.css("[class*='Price']::text, [class*='price']::text").get()
        if raw_price:
            price = raw_price.strip()

    # 3. Description
    raw_desc = selector.css("meta[name='description']::attr(content)").get()
    desc_paras = selector.css(
        "[class*='ProductSubInfo'] p::text, [class*='ProductSubInfo'] span::text"
    ).getall()
    desc_text = clean_text([p.strip() for p in desc_paras if p.strip()])
    description = desc_text if desc_text else (raw_desc.strip() if raw_desc else "")

    # 4. Detail
    detail_raw = selector.css("[class*='ProductSpecification']").get()
    detail = clean_html(detail_raw) if detail_raw else ""

    # 5. Promo
    promo = None
    promo_code_match = re.search(r"USE CODE:\s*([A-Za-z0-9]+)", text)
    promo_discount_match = re.search(
        r"SAVE\s+\d+%\s+ON\s+[A-Za-z0-9\s]+", text, re.IGNORECASE
    )
    if promo_discount_match and promo_code_match:
        promo = f"{promo_discount_match.group(0).strip()} | USE CODE: {promo_code_match.group(1)}"
    elif promo_code_match:
        promo = f"USE CODE: {promo_code_match.group(1)}"
    elif promo_discount_match:
        promo = promo_discount_match.group(0).strip()
    else:
        finance_match = re.search(r"\"copy\":\"([^\"]+)\"", text)
        if finance_match:
            promo = finance_match.group(1)

    return ProductDetailResponse(
        title=title,
        price=price,
        detail=detail,
        description=description,
        promo=promo,
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


def _parse_search_results(text: str) -> list[ProductSearchResponse]:
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


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"{config.EURO_CAR_PARTS_URL}/search/{encoded_keyword}"

    async with http_client.create_client() as client:
        response = await client.get(url)

    return _parse_search_results(response.text)


async def car_parts_product_search(
    car_plate: str, keyword: str
) -> list[ProductSearchResponse]:
    async with http_client.create_client() as client:
        gql_url = f"{config.EURO_CAR_PARTS_URL}/api/graphql"
        gql_payload = {
            "query": _FIND_BY_PLATE_QUERY,
            "variables": {"plateNumber": car_plate.strip().upper()},
        }
        try:
            gql_res = await client.post(
                gql_url,
                json=gql_payload,
                headers={"Content-Type": "application/json"},
            )
            if gql_res.status_code == 200:
                data = gql_res.json()
                v_info = data.get("data", {}).get("findByPlateNumber", {})
                mfr = v_info.get("manufacturer", {}).get("name", "")
                model = v_info.get("model", {}).get("name", "")
                attrs = {}
                for item in v_info.get("vehicleAttributes", []):
                    attrs[item.get("key")] = item.get("value")

                engine = (
                    attrs.get("EngineSizeDescription")
                    or attrs.get("EngineSize")
                    or attrs.get("Capacity")
                    or ""
                )
                fuel = attrs.get("Fuel") or attrs.get("FuelType") or ""
                year = attrs.get("VehicleYear") or attrs.get("Year") or ""
                plate = attrs.get("VRM") or car_plate.strip().upper()

                vsr_str = f"MA:{mfr},M:{model},E:{engine},F:{fuel},Y:{year},P:{plate}"
                encoded_vsr = urllib.parse.quote(vsr_str)
                b64_vsr = base64.b64encode(f"vsr={vsr_str}".encode()).decode()

                parsed_url = urllib.parse.urlparse(config.EURO_CAR_PARTS_URL)
                domain = parsed_url.netloc or "www.eurocarparts.com"

                client.cookies.set(
                    "vehicle_search_result_en_gb", encoded_vsr, domain=domain
                )
                client.cookies.set(
                    "cache_key_cookie_en_gb",
                    urllib.parse.quote(b64_vsr),
                    domain=domain,
                )
        except Exception:
            pass

        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{config.EURO_CAR_PARTS_URL}/search/{encoded_keyword}"
        response = await client.get(search_url)

    return _parse_search_results(response.text)
