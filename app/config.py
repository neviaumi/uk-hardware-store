import os

HOMEBASE_URL = "https://www.homebase.co.uk/en-uk"
DIY_DOT_COM_URL = "https://www.diy.com"
WICKES_URL = "https://www.wickes.co.uk"
SCREWFIX_URL = "https://www.screwfix.com"
TOOLSTATION_URL = "https://www.toolstation.com"
THE_RANGE_URL = "https://www.therange.co.uk"
HALFORDS_URL = "https://www.halfords.com"
ROBERT_DYAS_URL = "https://www.robertdyas.co.uk"
BROWSERLESS_ENDPOINT = "wss://browserless.handy-david.dev"
BROWSER_PROVIDER = os.getenv("BROWSER_PROVIDER", "browserless")
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
if BROWSER_PROVIDER == "browserless" and not BROWSERLESS_API_KEY:
    raise ValueError("BROWSERLESS_API_KEY is not set")
LIGHTPANDA_ENDPOINT = "ws://localhost:9222"
