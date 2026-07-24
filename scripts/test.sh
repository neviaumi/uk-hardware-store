#!/bin/bash

set -ex

if [ -z "${CI}" ]; then
  export BROWSERLESS_API_KEY=$(gcloud secrets versions access latest --secret="browserless-token")
  export BROWSER_PROVIDER=browserless
fi

uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest