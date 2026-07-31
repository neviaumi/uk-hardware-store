# Specification: Euro Car Parts Crawler & MCP Integration

## Goals
Integrate Euro Car Parts (https://www.eurocarparts.com/) into the UK Hardware Store application and MCP server. This includes supporting non-car-specific product searches, detailed product information retrieval, car registration plate-specific parts search, and registering Euro Car Parts as a supported provider across all relevant MCP tools.

## Acceptance Criteria (AC)
- [x] `euro_car_parts_crawler` supports `product_search(keyword)` for standard non-car-specific items returning standard `ProductSearchResponse` models.
- [x] `euro_car_parts_crawler` supports `product_detail(url)` for retrieving full product specifications, title, price, and description returning a standard `ProductDetailResponse` model.
- [x] `euro_car_parts_crawler` supports `car_parts_product_search(car_plate, keyword)` for querying vehicle-compatible products using a vehicle registration plate.
- [x] `EURO_CAR_PARTS` is added to the `Provider` enum and provider metadata list (`get_providers`) in `app/mcp_server.py`.
- [x] MCP tools `search_products`, `get_product_detail`, and `search_car_parts` support Euro Car Parts as a provider.
- [x] Mock HTML fixtures for Euro Car Parts are added to `tests/mock_server/` and tested via unit and integration tests.
- [x] All linting checks (`scripts/lint.sh`) and pytest suites pass cleanly.

## Out of Scope
- [ ] E-commerce checkout, basket addition, or user account management on Euro Car Parts.
- [ ] Real-time local store stock/inventory lookup per physical Euro Car Parts branch.
- [ ] Scraped data persistence to a database (data is parsed and returned dynamically on request).

## Development Plan
- [x] Support crawler search_product, it search for normal , non-car specific product
- [x] Support crawler get_prodct_details, search by product url
- [x] Support crawler search_car_parts, it search for car specific product
- [x] Support MCP integration
- [x] Final e2e check

## Explore
Currently, the application includes crawlers for 8 UK retailers (B&Q/DIY.com, Euro Car Parts, Halfords, Homebase, Robert Dyas, Screwfix, Toolstation, and Wickes) located in `app/crawlers/`.
- `app/config.py` defines the base URLs for retailers (`EURO_CAR_PARTS_URL = "https://www.eurocarparts.com"`).
- Empirically verified via `http_client.create_client()` (`curl-cffi` + `browserforge`) that Euro Car Parts returns `200 OK` without Cloudflare bot walls. Headless Playwright browser is **not** required.
- Euro Car Parts search and product pages use Next.js SSR, delivering HTML elements and JSON payload chunks containing product metadata (`title`, `price`, `sku`, `slug`).
- `app/crawlers/` contains individual modules returning standardized Pydantic models (`ProductSearchResponse`, `ProductDetailResponse`).
- `app/mcp_server.py` exposes `FastMCP` tools (`get_providers`, `get_product_detail`, `search_products`, `search_car_parts`) dispatched via the `Provider` enum. Euro Car Parts is registered as a supported provider across all tools.
- `tests/` contains crawler unit tests utilizing `pytest-httpserver` with static HTML fixtures stored in `tests/mock_server/`.

## Changelog
- 2026-07-31: Marked `product_search` as completed in Acceptance Criteria and Development Plan after task-01 execution. Updated Explore section with empirical findings confirming Euro Car Parts works via `curl_cffi`.
- 2026-07-31: Implemented `product_detail(url)` in `app/crawlers/euro_car_parts_crawler/euro_car_parts_crawler.py` and exported `ProductDetailResponse` after task-02 execution.
- 2026-07-31: Implemented `car_parts_product_search(car_plate, keyword)` using GraphQL VRM lookup and HTTP cookie session filtering. Registered `EURO_CAR_PARTS` in `Provider` enum and all MCP server tools in `app/mcp_server.py`. Added mock server fixtures, unit tests, and live integration tests after task-03 execution.


