---
name: end-to-end-car-parts-search
description: >-
  Executes an end-to-end verification workflow across supported car part providers using native MCP server tools defined in app/mcp_server.py.
---

# Skill: end-to-end-car-parts-search

Use this skill to perform an end-to-end verification workflow for registration-matched car parts search and product details retrieval across all supported car part providers.

> **CRITICAL DIRECTIVE**: You MUST execute tool calls using the native MCP server connection configured in `.agents/mcp_config.json`. Do NOT create, write, or run custom Python or bash verification scripts to call the tools.

## Search Parameters & Constants
- `car_plate`: Use `TEST_CAR_PLATE` (`"NX60OLA"` from `tests/crawler.py`).
- `keyword`: Use `TEST_SEARCH_CAR_PART` (`"Oil filter"` from `tests/crawler.py`).

## Logic & Execution Workflow

1. **Retrieve Car Part Providers**:
   - Call the `get_car_part_providers` MCP tool directly to list supported car part providers (`euro_car_parts`, `halfords`).
   - Cache response payload to `.debug/e2e_get_car_part_providers.json`.

2. **Search Car Parts Across Car Part Providers**:
   - For each provider returned by `get_car_part_providers`:
     - Call the `search_car_parts` MCP tool with parameters: `provider=<provider_name>` and `request={"car_plate": "NX60OLA", "keyword": "Oil filter"}`.
     - Cache raw response to `.debug/e2e_car_parts_search_<provider_name>.json`.

3. **Fetch Product Details**:
   - For each car part provider that returned search results:
     - Extract the `url` from the first returned product item.
     - Call the `get_product_detail` MCP tool with parameters: `provider=<provider_name>` and `request={"product_url": <extracted_url>}`.
     - Cache raw response to `.debug/e2e_car_parts_detail_<provider_name>.json`.

4. **Summary Reporting**:
   - After completing all tool executions, output a Markdown summary table displaying all tool calls, target providers, status, and cached file paths:

| Tool Name | Provider | Status | Cache File Path |
| :--- | :--- | :--- | :--- |
| `get_car_part_providers` | - | Success | `.debug/e2e_get_car_part_providers.json` |
| `search_car_parts` | `euro_car_parts` | Success | `.debug/e2e_car_parts_search_euro_car_parts.json` |
| `get_product_detail` | `euro_car_parts` | Success | `.debug/e2e_car_parts_detail_euro_car_parts.json` |
