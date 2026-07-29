import urllib.parse
from contextlib import asynccontextmanager

from playwright.async_api import Playwright, async_playwright

from app.config import (
    BROWSER_PROVIDER,
    BROWSERLESS_API_KEY,
    BROWSERLESS_ENDPOINT,
)


def connect_browserless(playwright: Playwright):
    params = {
        "token": BROWSERLESS_API_KEY,
        "--stealth": "",
        "--disable-blink-features": "AutomationControlled",
    }
    endpoint = f"{BROWSERLESS_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return playwright.chromium.connect_over_cdp(endpoint_url=endpoint, timeout=120000)


@asynccontextmanager
async def create_browser():
    async with async_playwright() as playwright:
        if BROWSER_PROVIDER == "browserless":
            browser = await connect_browserless(playwright)
        else:
            raise ValueError(f"Unknown browser provider: {BROWSER_PROVIDER}")
        context = await browser.new_context()
        try:
            yield context
        finally:
            await context.close()
            await browser.close()
