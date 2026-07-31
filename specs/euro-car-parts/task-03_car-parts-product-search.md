SPEC: [spec.md](file:///Users/david/my-apps/uk-hardware-store/specs/euro-car-parts/spec.md)

# Task: Euro Car Parts Car Parts Product Search & MCP Server Integration

## Goal
Implement `car_parts_product_search(car_plate, keyword)` in `euro_car_parts_crawler`, register `EURO_CAR_PARTS` in `Provider` enum in `app/mcp_server.py`, and expose Euro Car Parts across all MCP tools (`search_products`, `get_product_detail`, and `search_car_parts`).

## Acceptance Criteria
- [x] `euro_car_parts_crawler` exports `async def car_parts_product_search(car_plate: str, keyword: str) -> list[ProductSearchResponse]`.
- [x] VRM vehicle resolution is performed via `curl_cffi` HTTP client using Euro Car Parts GraphQL `findByPlateNumber` query (`https://www.eurocarparts.com/api/graphql`).
- [x] Vehicle session cookies (`vehicle_search_result_en_gb` and `cache_key_cookie_en_gb`) are set on the HTTP client session to filter search results without requiring a headless Playwright browser.
- [x] `EURO_CAR_PARTS = "Euro Car Parts"` is added to the `Provider` enum and `get_providers` metadata in [app/mcp_server.py](file:///Users/david/my-apps/uk-hardware-store/app/mcp_server.py).
- [x] MCP tools `search_products`, `get_product_detail`, and `search_car_parts` in [app/mcp_server.py](file:///Users/david/my-apps/uk-hardware-store/app/mcp_server.py) dispatch Euro Car Parts crawler functions.
- [x] Mock HTML and GraphQL response fixtures are added to [tests/mock_server/](file:///Users/david/my-apps/uk-hardware-store/tests/mock_server/) and registered in [tests/mock_server/__init__.py](file:///Users/david/my-apps/uk-hardware-store/tests/mock_server/__init__.py).
- [x] Unit tests for `car_parts_product_search` and MCP tool dispatching pass in [tests/test_euro_car_parts_crawler.py](file:///Users/david/my-apps/uk-hardware-store/tests/test_euro_car_parts_crawler.py) and [tests/test_mcp_server.py](file:///Users/david/my-apps/uk-hardware-store/tests/test_mcp_server.py).
- [x] All linting (`scripts/lint.sh`) and pytest suites pass cleanly.

## Implementation Plan

1. Implement `car_parts_product_search` in `euro_car_parts_crawler.py`.
   - Define `findByPlateNumber` GraphQL query and helper functions to fetch vehicle specifications (`Make`, `Model`, `EngineSize`, `FuelType`, `Year`) using `http_client.create_client()`.
   - Encode vehicle details into `vehicle_search_result_en_gb` and `cache_key_cookie_en_gb` session cookies.
   - Execute `product_search(keyword)` with vehicle session cookies set to retrieve vehicle-compatible products.
   - Export `car_parts_product_search` in [app/crawlers/euro_car_parts_crawler/__init__.py](file:///Users/david/my-apps/uk-hardware-store/app/crawlers/euro_car_parts_crawler/__init__.py) and [app/crawlers/__init__.py](file:///Users/david/my-apps/uk-hardware-store/app/crawlers/__init__.py).

2. Register Euro Car Parts in `app/mcp_server.py`.
   - Add `EURO_CAR_PARTS = "Euro Car Parts"` to the `Provider` enum in [app/mcp_server.py](file:///Users/david/my-apps/uk-hardware-store/app/mcp_server.py).
   - Include Euro Car Parts metadata entry in `get_providers`.
   - Update `search_products`, `get_product_detail`, and `search_car_parts` MCP tool endpoints to support `Provider.EURO_CAR_PARTS`.

3. Update mock server and test suite.
   - Add GraphQL mock response and vehicle search result HTML fixture in [tests/mock_server/](file:///Users/david/my-apps/uk-hardware-store/tests/mock_server/).
   - Add unit tests for `car_parts_product_search` in [tests/test_euro_car_parts_crawler.py](file:///Users/david/my-apps/uk-hardware-store/tests/test_euro_car_parts_crawler.py).
   - Add MCP server unit tests for Euro Car Parts provider integration in [tests/test_mcp_server.py](file:///Users/david/my-apps/uk-hardware-store/tests/test_mcp_server.py).

## Test Plan
- [x] Run `bash ./scripts/lint.sh` to verify syntax formatting, linting, and static typing pass without errors.
- [x] Run `pytest tests/test_euro_car_parts_crawler.py` to verify Euro Car Parts unit tests.
- [x] Run `pytest tests/test_mcp_server.py` to verify MCP server provider dispatching for Euro Car Parts.
- [x] Run `bash ./scripts/tests/unit.sh` to verify all unit tests pass cleanly without regressions.

## Explore
- Empirically probed Euro Car Parts VRM lookup flow and verified that **No Headless Browser / Playwright is required**.
- VRM resolution is accomplished via a POST request to Euro Car Parts GraphQL endpoint `https://www.eurocarparts.com/api/graphql` using `query findByPlateNumber($plateNumber: String!)`.
- Passing the plate (e.g. `NX60OLA`) returns vehicle details (`TOYOTA`, `Yaris`, `1.3`, `Petrol`, `2010`).
- Setting vehicle cookies `vehicle_search_result_en_gb` (URL-encoded `MA:{Make},M:{Model},E:{EngineSize},F:{Fuel},Y:{Year},P:{VRM}`) and `cache_key_cookie_en_gb` (URL-encoded base64 string `vsr=...`) on the `http_client.create_client()` session causes search queries to filter products for the targeted vehicle directly via lightweight HTTP requests.
- `app/mcp_server.py` requires registering `EURO_CAR_PARTS` in `Provider` enum, `get_providers`, `search_products`, `get_product_detail`, and `search_car_parts`.

## Changelog
- 2026-07-31: Implemented `car_parts_product_search`, registered `EURO_CAR_PARTS` in `Provider` enum and MCP server tools, added mock JSON fixtures, unit tests, and live integration tests. All linting and tests passed.

