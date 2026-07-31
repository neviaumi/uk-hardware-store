#!/usr/bin/env bash

set -ex

export BROWSER_PROVIDER="${BROWSER_PROVIDER:-unknown}"

uv run pytest -m "not integration_test" "$@"
