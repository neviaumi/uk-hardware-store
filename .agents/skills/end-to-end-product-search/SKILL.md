---
name: end-to-end-product-search
description: >-
  Executes an end-to-end verification workflow across all hardware store providers using native MCP server tools defined in app/mcp_server.py.
---

# Skill: end-to-end-product-search

Use this skill to perform an end-to-end verification workflow for general product search and product details retrieval across all supported UK hardware store providers.

> **CRITICAL DIRECTIVE**: You MUST execute tool calls using Antigravity's built-in `call_mcp_tool` to interact with the `uk-hardware-store` MCP server. Do NOT write or run any scripts (Python, bash, or scratch files) to call the MCP server.

## Built-in MCP Invocation Schema (`call_mcp_tool`)
Always call the built-in `call_mcp_tool` with the following parameter structure:
- `ServerName`: `"uk-hardware-store"`
- `ToolName`: The target FastMCP tool (e.g., `"get_providers"`, `"search_products"`, `"get_product_detail"`)
- `Arguments`: The JSON object arguments matching the tool schema
- `toolSummary`: Short description phrase
- `toolAction`: Short action description phrase

### Valid Provider Identifiers (`provider`)
Enum strings recognized by the server: `"B&Q"`, `"Euro Car Parts"`, `"Halfords"`, `"Homebase"`, `"Robert Dyas"`, `"Screwfix"`, `"Toolstation"`, `"Wickes"`.

## Search Parameters & Constants
- `keyword`: Use `TEST_SEARCH_KEYWORD` (`"M6 Hex Bolt"` from `tests/crawler.py`).

## Logic & Execution Workflow

1. **Retrieve Available Providers**:
   - Call `call_mcp_tool` with `ServerName="uk-hardware-store"`, `ToolName="get_providers"`, `Arguments={}`.
   - Cache response payload to `.debug/e2e_get_providers.json`.

2. **Search Products Across Providers**:
   - For each target provider (or filtered provider if requested):
     - Call `call_mcp_tool` with `ServerName="uk-hardware-store"`, `ToolName="search_products"`, and `Arguments={"provider": "<Provider_Name>", "request": {"keyword": "M6 Hex Bolt"}}`.
     - Cache raw response to `.debug/e2e_product_search_<provider_slug>.json`.

3. **Fetch Product Details**:
   - For each provider that returned search results:
     - Extract the `url` from the first returned product item.
     - Call `call_mcp_tool` with `ServerName="uk-hardware-store"`, `ToolName="get_product_detail"`, and `Arguments={"provider": "<Provider_Name>", "request": {"product_url": "<extracted_url>"}}`.
     - Cache raw response to `.debug/e2e_product_detail_<provider_slug>.json`.

4. **Summary Reporting**:
   - Output a Markdown summary table displaying all tool calls, target providers, status, and cached file paths:

| Tool Name | Provider | Status | Cache File Path |
| :--- | :--- | :--- | :--- |
| `get_providers` | - | Success | `.debug/e2e_get_providers.json` |
| `search_products` | `Halfords` | Success | `.debug/e2e_product_search_halfords.json` |
| `get_product_detail` | `Halfords` | Success | `.debug/e2e_product_detail_halfords.json` |
