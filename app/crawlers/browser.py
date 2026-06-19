import urllib.parse
from contextlib import asynccontextmanager

from playwright.async_api import PlaywrightContextManager, async_playwright

from app.config import (
    BROWSER_PROVIDER,
    BROWSERLESS_API_KEY,
    BROWSERLESS_ENDPOINT,
    LIGHTPANDA_ENDPOINT,
)


def connect_lightpanda(playwright: PlaywrightContextManager):
    return playwright.chromium.connect_over_cdp(
        endpoint_url=LIGHTPANDA_ENDPOINT, timeout=120000
    )


def connect_browserless(playwright: PlaywrightContextManager):
    if BROWSERLESS_API_KEY is None:
        raise ValueError("BROWSERLESS_API_KEY is not set")
    params = {
        "token": BROWSERLESS_API_KEY,
        "--stealth": "",
        "--disable-blink-features": "AutomationControlled",
    }
    endpoint = f"{BROWSERLESS_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return playwright.chromium.connect_over_cdp(endpoint_url=endpoint, timeout=120000)


def connect_local_firefox(playwright: PlaywrightContextManager):
    return playwright.firefox.launch(headless=False)


@asynccontextmanager
async def create_browser():
    async with async_playwright() as playwright:
        if BROWSER_PROVIDER == "lightpanda":
            browser = await connect_lightpanda(playwright)
        elif BROWSER_PROVIDER == "browserless":
            browser = await connect_browserless(playwright)
        elif BROWSER_PROVIDER == "firefox":
            browser = await connect_local_firefox(playwright)
        else:
            raise ValueError(f"Unknown browser provider: {BROWSER_PROVIDER}")
        context = await browser.new_context()
        try:
            yield context
        finally:
            await context.close()
            await browser.close()
