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
from app.crawlers.utils import clean_html
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
        await page.goto(url, wait_until="domcontentloaded", timeout=_DEFAULT_TIMEOUT)
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

        desc_parts = []
        acc_locs = page.locator(
            "[data-testid='accordion-content'], [data-testid='product-description'], .b-product-description"
        )
        acc_count = await acc_locs.count()
        if acc_count > 0:
            for i in range(acc_count):
                acc_el = acc_locs.nth(i)
                text = (await acc_el.inner_text()).strip()
                if text and text not in desc_parts:
                    desc_parts.append(text)

        features_loc = page.locator(
            "[data-testid='features-and-benefits'] li, .b-features-list li"
        )
        feat_count = await features_loc.count()
        if feat_count > 0:
            bullet_items = []
            for i in range(feat_count):
                bullet = (await features_loc.nth(i).inner_text()).strip()
                if bullet and bullet not in bullet_items:
                    bullet_items.append(f"• {bullet}")
            if bullet_items:
                feat_text = "Features & Benefits:\n" + "\n".join(bullet_items)
                if feat_text not in desc_parts:
                    desc_parts.append(feat_text)

        desc_text = "\n\n".join(desc_parts).strip()
        ld_desc = str(jdata.get("description") or "").strip()

        if desc_text:
            if ld_desc and ld_desc not in desc_text and len(ld_desc) > len(desc_text):
                description = f"{ld_desc}\n\n{desc_text}"
            else:
                description = desc_text
        else:
            description = ld_desc

        detail_raw = None
        table_loc = page.locator(
            "[data-testid='specification-table'], "
            "table[data-testid='specification-table'], "
            "[data-testid='specification-table-wrapper']"
        )
        if await table_loc.count() > 0:
            try:
                detail_raw = await table_loc.first.evaluate("el => el.outerHTML")
            except Exception:
                pass

        if not detail_raw:
            detail_raw = (
                sel.css("[data-testid='specification-table-wrapper']").get()
                or sel.css("[data-testid='specification-table']").get()
                or sel.xpath(
                    "//table[@aria-label='Specifications' or contains(@class, 'spec')] "
                    "| //div[@data-testid='specifications']"
                ).get()
            )

        if detail_raw:
            detail = clean_html(detail_raw) or ""
        else:
            specs_dict = {}
            cell_0s = page.locator(
                "[data-testid^='specification-cell-'][data-testid$='-0']"
            )
            c_count = await cell_0s.count()
            if c_count > 0:
                for i in range(c_count):
                    cell_lbl = cell_0s.nth(i)
                    testid = await cell_lbl.get_attribute("data-testid")
                    if testid and testid.startswith("specification-cell-"):
                        cell_val_id = testid[:-1] + "1"
                        cell_val = page.locator(f"[data-testid='{cell_val_id}']")
                        if await cell_val.count() > 0:
                            lbl = (await cell_lbl.text_content() or "").strip()
                            val = (await cell_val.text_content() or "").strip()
                            if lbl and val:
                                specs_dict[lbl] = val

            sku_val = (
                jdata.get("sku")
                or sel.css('[itemprop="sku"]::text, [data-testid="sku"]::text').get()
            )
            if sku_val and "SKU" not in specs_dict:
                specs_dict["SKU"] = str(sku_val).strip()

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
        wait_until="domcontentloaded",
        timeout=_DEFAULT_TIMEOUT,
    )
    cookie_accept = page.get_by_role("button", name="Accept all", exact=False)
    if await cookie_accept.count() > 0:
        await cookie_accept.click()

    vrn_input = page.locator("input[data-testid='vrn_search_form-vrn-inputField']")
    await vrn_input.wait_for(state="visible", timeout=15000)
    await vrn_input.fill(car_plate)

    postcode_input = page.locator(
        "input[data-testid='vrn_search_form-postcode-autocomplete-inputField']"
    )
    await postcode_input.press_sequentially(_DEFAULT_POSTCODE, delay=100)
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
    try:
        await page.wait_for_selector("[data-testid='alert-success']", timeout=10000)
    except Exception:
        pass


async def _product_search(page: Page, keyword: str):
    query = urllib.parse.urlencode({"q": keyword})
    url = f"{config.HALFORDS_URL}/search?{query}"
    await page.goto(url, wait_until="domcontentloaded", timeout=_DEFAULT_TIMEOUT)
    carparts_product_locator = page.locator("[data-cmp-id='productTileContainer']")
    product_locator = page.locator("[data-testid='product-tile']")
    try:
        await carparts_product_locator.or_(product_locator).first.wait_for(
            state="visible", timeout=15000
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
        title_loc = product.locator("[data-testid='product-title']")
        title = await title_loc.inner_text() if await title_loc.count() > 0 else ""
        price_loc = product.locator("[data-testid='product-tile-price']")
        price = await price_loc.inner_text() if await price_loc.count() > 0 else ""
        link_loc = product.locator(
            "a[href*='/product/'], a[href*='.html'], [data-testid='halfords-link']"
        ).first
        url = await link_loc.get_attribute("href") if await link_loc.count() > 0 else ""
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
