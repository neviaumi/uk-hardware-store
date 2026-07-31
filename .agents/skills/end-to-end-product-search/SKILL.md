---
name: end-to-end-product-search
description: >-
  Executes an end-to-end verification workflow across all hardware store providers using native MCP server tools defined in app/mcp_server.py.
---

# Skill: end-to-end-product-search

Use this skill to perform an end-to-end verification workflow for general product search and product details retrieval across all supported UK hardware store providers.

> **CRITICAL DIRECTIVE**: You MUST execute tool calls using the native MCP server connection configured in `.agents/mcp_config.json`. Do NOT create, write, or run custom Python or bash verification scripts to call the tools.

## Search Parameters & Constants
- `keyword`: Use `TEST_SEARCH_KEYWORD` (`"M6 Hex Bolt"` from `tests/crawler.py`).

## Logic & Execution Workflow

1. **Retrieve Available Providers**:
   - Call the `get_providers` MCP tool directly to list all supported hardware store providers (`diy_dot_com`, `euro_car_parts`, `halfords`, `homebase`, `robert_dyas`, `screwfix`, `toolstation`, `wickes`).
   - Cache response payload to `.debug/e2e_get_providers.json`.

2. **Search Products Across All Providers**:
   - For each provider returned by `get_providers`:
     - Call the `search_products` MCP tool with parameters: `provider=<provider_name>` and `request={"keyword": "M6 Hex Bolt"}`.
     - Cache raw response to `.debug/e2e_product_search_<provider_name>.json`.

3. **Fetch Product Details**:
   - For each provider that returned search results:
     - Extract the `url` from the first returned product item.
     - Call the `get_product_detail` MCP tool with parameters: `provider=<provider_name>` and `request={"product_url": <extracted_url>}`.
     - Cache raw response to `.debug/e2e_product_detail_<provider_name>.json`.

4. **Summary Reporting**:
   - After completing all tool executions, output a Markdown summary table displaying all tool calls, target providers, status, and cached file paths:

| Tool Name | Provider | Status | Cache File Path |
| :--- | :--- | :--- | :--- |
| `get_providers` | - | Success | `.debug/e2e_get_providers.json` |
| `search_products` | `diy_dot_com` | Success | `.debug/e2e_product_search_diy_dot_com.json` |
| `get_product_detail` | `diy_dot_com` | Success | `.debug/e2e_product_detail_diy_dot_com.json` |
