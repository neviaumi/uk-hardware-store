---
trigger: always_on
description: This rule governs code quality, linting (Ruff), the pytest framework, and the specialized mock data capture protocols.
---

# Testing Protocols

This document defines the requirements and procedures for all testing activities within the repository, ensuring code quality and environment parity.

## 1. General Testing Standards

### Linting and Formatting
To maintain code consistency and catch logical errors, use **Ruff** and **ty**.
```bash
# Run formatting checks, linting rules, and type checking
bash ./scripts/lint.sh
```

### Behavioral Testing Tiers

Testing is split into three distinct execution tiers:

1. **Unit Testing (`bash ./scripts/tests/unit.sh`)**:
   - Runs all fast unit tests (excluding tests marked with `@integration_test`).
   - **Requirement**: Must be executed automatically whenever an agent completes code changes or refactoring.

2. **Integration Testing (`bash ./scripts/tests/integration.sh`)**:
   - Runs live crawler and browser tests marked with `@integration_test`.
   - Automatically manages `BROWSERLESS_API_KEY` authentication locally.
   - **Requirement**: During development, agents should run only specific, targeted integration test cases (e.g., `bash ./scripts/tests/integration.sh tests/test_halfords_crawler.py`). Running all integration tests is time-consuming and must not be triggered automatically unless explicitly requested by the user.
   - **Targeting Specific Providers**: Pass the `-k` filter to target specific providers in parameterized integration tests (e.g., `bash ./scripts/tests/integration.sh tests/test_mcp_provider_integration.py -k "GSF"`, `... -k "Halfords"`, or `... -k "Euro"`).

3. **End-to-End (E2E) Testing**:
   - Direct verification of MCP tools using `.agents/mcp_config.json`.
   - **Requirement**: Only run when explicitly requested by the user.

### Browserless Token Requirement
When running integration tests that utilize the browser-based stack, a valid `BROWSERLESS_API_KEY` must be present in the environment.

- **Local Execution**: `scripts/tests/integration.sh` automatically fetches the latest token from Google Cloud Secret Manager if `BROWSERLESS_API_KEY` is not set.
- **Manual Execution**: If running `pytest -m integration_test` directly without the script, ensure you have authenticated with `gcloud` and exported the key manually.
- **CI Execution**: Integration tests marked `@integration_test` are excluded from CI runs.

---

## 2. Mock Data Capture Protocol

> [!NOTE]
> When this rule is active, the agent should automatically suggest using `curl` for fetching new HTML snapshots if the existing mocks are missing or user ask for refresh/reload explicitly.

To ensure parity between the real-world site and the mocked environment, all HTML fixtures **MUST** be captured using a standardized `curl` command to avoid browser-specific DOM manipulations or missing attributes.

### Capture Command
Use the following `curl` flags to capture the raw HTML into the `.debug/` folder:
- `-s`: Silent mode (no progress bar).
- `-L`: Follow redirects (essential for search results that may point to canonical URLs).
- `-H`: Spoof a modern browser `User-Agent` to avoid bot-detect blocks.

```bash
curl -sL "https://www.wickes.co.uk/search?q=M6+Hex+Bolt" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  > .debug/product_search_wickes.html
```

### Post-Processing Logic
Before moving the file to `tests/mock_server/`, perform the following checks:
- **Selector Verification**: Use `grep` or `parsel` in a scratch script to confirm that the crawler's target selectors (e.g., `[data-product-code]`, `.main-price__value`) exist in the raw HTML.
- **Path Correction**: If the crawler relies on absolute URLs prepended by a base, ensure the mock server mimics this directory structure.
- **Cleanup**: Remove large `<script>` or `<style>` blocks only if they cause significant parsing latency. Do not modify the structure of the data-bearing elements.

### Integration Guide
Captured files are served by the local `pytest-httpserver`. 
- **Mapping**: Register the endpoint in `tests/mock_server/__init__.py`.
- **Mocking**: Use `monkeypatch` to redirect the `app.config` URL constants to the `mock_server.url_for()` equivalent.

```python
# tests/mock_server/__init__.py
monkeypatch.setattr(config, "WICKES_URL", httpserver.url_for("/wickes"))
```

---

## 3. Troubleshooting and Refresh
If a crawler test fails due to UI drift or missing data:
1.  Verify the keyword in `tests/crawler.py`.
2.  Re-run the **Capture Command** mentioned above to refresh the local HTML fixture.
3.  Update the expected paths in `tests/test_<crawler>_crawler.py` if the site structure has changed.

---

## 4. End-to-End (E2E) MCP Testing Standard

> [!IMPORTANT]
> **Direct MCP Connection Rule**:
> For verifying end-to-end MCP server behavior and tools, agents **MUST NOT** write or execute custom scratch verification scripts. 
> Agents must leverage the direct MCP connection defined in `.agents/mcp_config.json` via the native MCP interface.

### Verification Protocol
1. **Configuration**: Use `.agents/mcp_config.json` which defines the stdio server entry point.
2. **Execution Rules**:
   - **Direct MCP Connection**: Agents must interact directly with the MCP server using the configured MCP connection in `.agents/mcp_config.json` to call and verify tools.
   - **No Scratch Verification Scripts**: Agents must not generate custom Python test scripts to test MCP tool responses.