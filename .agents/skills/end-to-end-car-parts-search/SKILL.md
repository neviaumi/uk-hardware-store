---
name: end-to-end-car-parts-search
description: >-
  Executes an end-to-end verification workflow across supported car part providers using native MCP server tools defined in app/mcp_server.py.
---

# Skill: end-to-end-car-parts-search

Use this skill to perform an end-to-end verification workflow for registration-matched car parts search and product details retrieval across all supported car part providers.

> **CRITICAL DIRECTIVE**: You MUST execute tool calls using Antigravity's built-in `call_mcp_tool` to interact with the `uk-hardware-store` MCP server. Do NOT write or run any scripts (Python, bash, or scratch files) to call the MCP server. If `call_mcp_tool` fails, analyze the error and fix your arguments; NEVER fallback to writing a script.

## Built-in MCP Invocation Schema (`call_mcp_tool`)
Always call the built-in `call_mcp_tool` to execute these tools. Check your available tool definitions to confirm the exact parameter casing (e.g., `server_name` vs `ServerName`), but it requires:
- The server name: `"uk-hardware-store"`
- The tool name: The target FastMCP tool (e.g., `"get_car_part_providers"`, `"search_car_parts"`, `"get_product_detail"`)
- The arguments: The JSON object arguments matching the tool schema

### Valid Car Part Provider Identifiers (`provider`)
Enum strings recognized by the server: `"Euro Car Parts"`, `"Halfords"`.

## Search Parameters & Constants
- `car_plate`: Use `TEST_CAR_PLATE` (`"NX60OLA"` from `tests/crawler.py`).
- `keyword`: Use `TEST_SEARCH_CAR_PART` (`"Oil filter"` from `tests/crawler.py`).

## Logic & Execution Workflow

1. **Retrieve Car Part Providers**:
   - Call `call_mcp_tool` targeting the `"uk-hardware-store"` server and the `"get_car_part_providers"` tool, with empty arguments `{}`.
   - Cache response payload to `.debug/e2e_get_car_part_providers.json`.

2. **Search Car Parts Across Car Part Providers**:
   - For each car part provider (or filtered provider if requested):
     - Call `call_mcp_tool` targeting the `"uk-hardware-store"` server and the `"search_car_parts"` tool, with arguments `{"provider": "<Provider_Name>", "request": {"car_plate": "NX60OLA", "keyword": "Oil filter"}}`.
     - Cache raw response to `.debug/e2e_car_parts_search_<provider_slug>.json`.

3. **Fetch Product Details**:
   - For each car part provider that returned search results:
     - Extract the `url` from the first returned product item.
     - Call `call_mcp_tool` targeting the `"uk-hardware-store"` server and the `"get_product_detail"` tool, with arguments `{"provider": "<Provider_Name>", "request": {"product_url": "<extracted_url>"}}`.
     - Cache raw response to `.debug/e2e_car_parts_detail_<provider_slug>.json`.

4. **Summary Reporting**:
   - Output a Markdown summary table displaying all tool calls, target providers, status, and cached file paths:

| Tool Name | Provider | Status | Cache File Path |
| :--- | :--- | :--- | :--- |
| `get_car_part_providers` | - | Success | `.debug/e2e_get_car_part_providers.json` |
| `search_car_parts` | `Euro Car Parts` | Success | `.debug/e2e_car_parts_search_euro_car_parts.json` |
| `get_product_detail` | `Euro Car Parts` | Success | `.debug/e2e_car_parts_detail_euro_car_parts.json` |
