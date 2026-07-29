# https://www.halfords.com/search?q=M6+Hex+Bolt
import json
import urllib.parse
from enum import Enum
from typing import Final, Literal

from parsel import Selector
from playwright.async_api import Page
from pydantic import BaseModel, Field

import app.config as config
from app.crawlers.browser import create_browser
from app.logger import get_logger_for_crawler

SOURCE_IDENTIFIER: Final = "Halfords"
SOURCE_DESCRIPTION = (
    "Halfords is a retailer of car parts, car accessories, and bicycles."
)
# High Wycombe Halfords is superstore with MOT and car services
_DEFAULT_POSTCODE = "HP11 1EZ"
_DEFAULT_TIMEOUT = 300 * 1000
logger = get_logger_for_crawler(SOURCE_IDENTIFIER)


class SearchBy(str, Enum):
    KEYWORD = "keyword"
    CAR_PLATE = "car_plate"


class ProductSearchResponse(BaseModel):
    source: Literal["Halfords"] = Field(
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
        description="A brief summary of any active promotion shown in the search snippet.",
        default=None,
    )


class ProductDetailResponse(BaseModel):
    source: Literal["Halfords"] = Field(
        description="The source of the product.", default=SOURCE_IDENTIFIER
    )
    title: str = Field(description="The full commercial name of the product.")
    price: str = Field(
        description="The current retail price, including the currency symbol (e.g., £17.20)."
    )
    detail: str = Field(
        description="Comprehensive technical specifications or item details in HTML or JSON format."
    )
    description: str = Field(
        description="A brief text summary of the product's key details and features."
    )
    promo: str | None = Field(
        description="Any active promotional offers or discounts associated with the product.",
        default=None,
    )


async def car_parts_product_search(
    car_plate: str, keyword: str
) -> list[ProductSearchResponse]:
    async with create_browser() as browser:
        page = await browser.new_page()
        await _setup_car_registration(page, car_plate)
        return await _product_search(page, keyword)


async def product_search(keyword: str) -> list[ProductSearchResponse]:
    async with create_browser() as browser:
        page = await browser.new_page()
        return await _product_search(page, keyword)


async def product_detail(url: str) -> ProductDetailResponse:
    async with create_browser() as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=_DEFAULT_TIMEOUT)
        cookie_accept = page.get_by_role("button", name="Accept all", exact=False)
        if await cookie_accept.count() > 0:
            await cookie_accept.click()

        html = await page.content()
        sel = Selector(text=html)

        jdata = {}
        jtext = sel.css('script[type="application/ld+json"]::text').get()
        if jtext:
            try:
                jdata = json.loads(jtext)
            except Exception:
                pass

        title = (
            jdata.get("name")
            or sel.css('meta[property="og:title"]::attr(content)').get()
            or await page.locator("h1").first.inner_text()
        )
        if title and " | Halfords UK" in title:
            title = title.replace(" | Halfords UK", "").strip()

        price = None
        if isinstance(jdata.get("offers"), dict) and "price" in jdata["offers"]:
            p_val = jdata["offers"]["price"]
            currency = "£" if jdata["offers"].get("priceCurrency") == "GBP" else ""
            price = (
                f"{currency}{p_val:.2f}"
                if isinstance(p_val, (int, float))
                else f"{currency}{p_val}"
            )
        if not price:
            if await page.locator("[data-testid='price']").count() > 0:
                price = await page.locator("[data-testid='price']").first.inner_text()
            elif await page.locator(".halfords-basket-price").count() > 0:
                price = await page.locator(".halfords-basket-price").first.inner_text()
            else:
                price = "N/A"

        description = jdata.get("description") or ""
        acc0_loc = page.locator("[data-testid='accordion-content']").first
        if await acc0_loc.count() > 0:
            acc0_text = await acc0_loc.inner_text()
            if len(acc0_text.strip()) > len(description):
                description = acc0_text.strip()

        specs_dict = {}
        spec_rows = sel.xpath('//table[@aria-label="Specifications"]//tr')
        for tr in spec_rows:
            label = " ".join(
                [t.strip() for t in tr.xpath("./th//text()").getall() if t.strip()]
            )
            value = " ".join(
                [t.strip() for t in tr.xpath("./td//text()").getall() if t.strip()]
            )
            if label and value:
                specs_dict[label] = value

        detail = json.dumps(specs_dict, indent=2) if specs_dict else ""

        promo_loc = page.locator(
            "[data-testid='promotion'], [data-testid='promo-banner']"
        )
        promo = (
            await promo_loc.first.inner_text() if await promo_loc.count() > 0 else None
        )

        return ProductDetailResponse(
            title=title or "",
            price=price,
            detail=detail,
            description=description,
            promo=promo,
        )


async def _setup_car_registration(page: Page, car_plate: str):
    await page.goto(
        f"{config.HALFORDS_URL}/motoring/car-parts",
        wait_until="networkidle",
        timeout=_DEFAULT_TIMEOUT,
    )
    cookie_accept = page.get_by_role("button", name="Accept all", exact=False)
    if await cookie_accept.count() > 0:
        await cookie_accept.click()
    await page.locator("input[data-testid='vrn_search_form-vrn-inputField']").fill(
        car_plate
    )
    await page.locator(
        "input[data-testid='vrn_search_form-postcode-autocomplete-inputField']"
    ).press_sequentially(_DEFAULT_POSTCODE, delay=100)
    suggestion = (
        page.locator("[data-testid='vrn_search_form-postcode-suggestionBlock']")
        .get_by_role("option")
        .filter(has_text=_DEFAULT_POSTCODE)
    )
    if await suggestion.count() > 0:
        await suggestion.first.evaluate("el => el.click()")
    else:
        await (
            page.locator("[data-testid='vrn_search_form-postcode-suggestionBlock']")
            .get_by_role("option")
            .first.evaluate("el => el.click()")
        )
    search_btn = page.locator("button[data-testid='vrn_search_form-search-button']")
    await search_btn.evaluate("el => el.click()")
    await page.wait_for_selector("[data-testid='alert-success']")


async def _product_search(page: Page, keyword: str):
    query = urllib.parse.urlencode({"q": keyword})
    url = f"{config.HALFORDS_URL}/search?{query}"
    await page.goto(url, wait_until="networkidle", timeout=_DEFAULT_TIMEOUT)
    carparts_product_locator = page.locator("[data-cmp-id='productTileContainer']")
    product_locator = page.locator("[data-testid='product-tile']")
    try:
        await carparts_product_locator.or_(product_locator).first.wait_for(
            state="attached"
        )
    except Exception as e:
        logger.error(f"No products found for {keyword}, {e}")
        return []
    if await carparts_product_locator.count() > 0:
        logger.info(f"Car parts products found for {keyword}")
        return await _parse_car_parts_products(page)
    else:
        logger.info(f"Products found for {keyword}")
        return await _parse_products(page)


async def _parse_car_parts_products(page: Page) -> list[ProductSearchResponse]:
    results = []
    await page.wait_for_load_state("networkidle")
    products = await page.locator("[data-cmp-id='productTileContainer']").all()
    for product in products:
        json_text = await product.locator("script.js-tile-model").inner_text()
        product_data = json.loads(json_text).get("product", {})
        title = product_data.get("productName")
        price = product_data.get("price", {}).get("sales", {}).get("formatted")
        url = product_data.get("cleanProductUrl")
        promo = product_data.get("promotions", [{}])[0].get("name", None)
        results.append(
            ProductSearchResponse(
                title=title,
                price=price,
                url=url if url.startswith("https") else f"{config.HALFORDS_URL}{url}",
                promo=promo,
            )
        )
    return results


async def _parse_products(page: Page) -> list[ProductSearchResponse]:
    results = []
    products = await page.locator("[data-testid='product-tile']").all()
    for product in products:
        title = await product.locator("[data-testid='product-title']").inner_text()
        price = await product.locator("[data-testid='product-tile-price']").inner_text()
        url = await product.locator(
            "[data-testid='halfords-link']"
        ).first.get_attribute("href")
        promotion_locator = product.locator("[data-testid='promotion']")
        promo = (
            await promotion_locator.inner_text()
            if await promotion_locator.count() > 0
            else None
        )
        results.append(
            ProductSearchResponse(
                title=title,
                price=price,
                url=url
                if (url and url.startswith("https"))
                else f"{config.HALFORDS_URL}{url}"
                if url
                else "",
                promo=promo,
            )
        )
    return results
