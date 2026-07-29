# Project Documentation

## Agent Behavioral Primitives
- **Mandatory Plan Approval**: The agent cannot execute destructive or constructive changes on the primary codebase without an approved implementation plan.
- **Architectural Boundary Adherence**: Follow the exact folder conventions established for `app/`, `tests/`, and `scripts/`. Do not produce files in arbitrary locations.
- **Verification-First**: Always verify application behavior immediately after execution via `pytest` and Ruff linting checks.
- **Environment Execution**: When running shell scripts (like `scripts/test.sh`), you must ensure `~/.local/bin` is in the `PATH` by explicitly executing `source ~/.zshrc` in conjunction with the script (e.g., `source ~/.zshrc && bash ./scripts/test.sh`).
- **Exact Dependency Pinning**: Always use exact version pinning (`==`) for all dependencies in `pyproject.toml`. Do not use range operators (like `>=` or `~=`).

## Project Architecture
This repository uses the following directory structure:
- `app/`: Contains the main application source code, FastAPI entry points, MCP server definitions, and web crawlers.
  - `config.py`: Centralized environment and browser provider configuration.
  - `mcp_server.py`: FastMCP server implementation exposing e-commerce search tools and crawler integrations.
  - `crawlers/`: Retailer crawler modules (DIY.com/B&Q, Halfords, Homebase, Robert Dyas, Screwfix, Toolstation, Wickes) along with HTTP client (`http_client.py`) and Playwright browser (`browser.py`) utilities.
  - `main.py` / `stdio.py`: Application entry points for web server and stdio MCP transport.
- `specs/`: Feature specifications and task definitions created for Spec Driven Development (SDD).
- `tests/`: Automated unit and integration test suite (`pytest`), including `mock_server/` HTML snapshots and crawler behavioral tests.
- `scripts/`: Utility bash scripts for application startup (`start.sh`), linting (`lint.sh`), testing (`test.sh`), deployment (`deploy.sh`), and environment setup (`setup.sh`).
- `.agents/`: Repository-specific agent rules and coding guidelines (`rules/crawler.md`, `rules/testing.md`).
- `Dockerfile` / `docker-compose.yml`: Configurations for containerized deployment and local service execution.
- `pyproject.toml` / `uv.lock`: Dependency definitions and exact version locks managed by `uv`.

## Starting the Application
The application can be started using the provided bash scripts, which run the FastAPI server via `uv`.

To start the application in development mode (runs on port 8080):
```bash
bash ./scripts/start.sh --dev
```

To start the application in production mode (runs on port 8081):
```bash
bash ./scripts/start.sh --prod
```

### Comprehensive Testing Protocols
For all instructions on quality standards, linting, mock data capture, and pytest implementation, consult the consolidated testing rules:
- **[Testing Rules](file:///Users/david/apps/uk-hardware-store-mcp/.agents/rules/testing.md)**: Standardized procedures for all testing activities and mock server integration.
