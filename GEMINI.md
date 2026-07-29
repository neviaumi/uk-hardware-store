# Project Documentation

## Spec Driven Development (SDD) Workflow
This project STRICTLY adheres to the Spec Driven Development workflow. The Agent **MUST** follow these steps before modifying any runtime logic or configuration:
1. **Discovery & Investigation**: Understand the goal, read relevant files, and check current system statuses.
2. **Drafting the Plan**: Produce a clear `implementation_plan.md` and `task.md` detailing all architectural adjustments.
3. **Safety Hook (Approval)**: Use the `notify_user` tool with `BlockedOnUser: true` to pause and receive explicit user authorization. **No file modifications are allowed before this step.**
4. **Execution**: Apply the approved changes strictly.
5. **Testing & Verification**: Validate code utilizing `scripts/test.sh` (lint/format) and `uv run pytest` (behavioral).
6. **Documentation Walkthrough**: Produce a final `walkthrough.md` capturing what was executed and proven through testing.

## Agent Behavioral Primitives
- **Mandatory Plan Approval**: The agent cannot execute destructive or constructive changes on the primary codebase without an approved implementation plan.
- **Architectural Boundary Adherence**: Follow the exact folder conventions established for `app/`, `tests/`, and `scripts/`. Do not produce files in arbitrary locations.
- **Verification-First**: Always verify application behavior immediately after execution via `pytest` and Ruff linting checks.
- **Environment Execution**: When running shell scripts (like `scripts/test.sh`), you must ensure `~/.local/bin` is in the `PATH` by explicitly executing `source ~/.zshrc` in conjunction with the script (e.g., `source ~/.zshrc && bash ./scripts/test.sh`).
- **Exact Dependency Pinning**: Always use exact version pinning (`==`) for all dependencies in `pyproject.toml`. Do not use range operators (like `>=` or `~=`).

## Project Architecture
This repository uses the following directory structure:
- `app/`: Contains the main application source code, FastAPI entry points, MCP server definitions, and web crawlers.
- `tests/`: Contains the automated test suite for the application.
- `scripts/`: Contains utility scripts for starting the application (`start.sh`), testing (`test.sh`), deploying (`deploy.sh`), and environment setup.
- `Dockerfile` / `docker-compose.yml`: Configurations for containerized deployment and local service setup.
- `pyproject.toml` / `uv.lock`: Dependency management and project definitions managed directly by `uv`.
- `mcp.json`: Model Context Protocol configuration.

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
