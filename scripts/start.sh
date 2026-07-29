#!/usr/bin/env bash
set -ex

MODE=${1:---dev}
export BROWSERLESS_API_KEY=$(gcloud secrets versions access latest --secret="browserless-token" 2>/dev/null || echo "")
export BROWSER_PROVIDER=browserless
if [ "$MODE" = "--dev" ]; then
    PYTHONPATH=. uv run mcp dev app/mcp_server.py
elif [ "$MODE" = "--prod" ]; then
    uv run fastapi run --port 8082 app/main.py
elif [ "$MODE" = "--stdio" ]; then
    PYTHONPATH=. uv run -m app.stdio
else
    echo "Invalid argument: $MODE"
    exit 1
fi
