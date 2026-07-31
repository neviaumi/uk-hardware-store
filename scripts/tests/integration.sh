#!/usr/bin/env bash

set -ex

export BROWSER_PROVIDER="${BROWSER_PROVIDER:-browserless}"

if [ -z "${BROWSERLESS_API_KEY}" ]; then
  export BROWSERLESS_API_KEY=$(gcloud secrets versions access latest --secret="browserless-token")
fi

uv run pytest -m "integration_test" "$@"
