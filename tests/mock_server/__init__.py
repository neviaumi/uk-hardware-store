import json
import os

import pytest
import pytest_httpserver.httpserver as httpserver

import app.config as config

CURRENT_DIR = os.path.dirname(__file__)


def mock_response_data(fileName: str):
    path = os.path.join(CURRENT_DIR, fileName)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def mock_response_json(fileName: str):
    path = os.path.join(CURRENT_DIR, fileName)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_server(httpserver: httpserver.HTTPServer, monkeypatch):
    monkeypatch.setattr(
        config,
        "HOMEBASE_URL",
        httpserver.url_for("/homebase/en-uk"),
    )
    monkeypatch.setattr(
        config,
        "DIY_DOT_COM_URL",
        httpserver.url_for("/b&q"),
    )
    monkeypatch.setattr(
        config,
        "WICKES_URL",
        httpserver.url_for("/wickes"),
    )
    monkeypatch.setattr(
        config,
        "SCREWFIX_URL",
        httpserver.url_for("/screwfix"),
    )
    monkeypatch.setattr(
        config,
        "TOOLSTATION_URL",
        httpserver.url_for("/toolstation"),
    )
    monkeypatch.setattr(
        config,
        "THE_RANGE_URL",
        httpserver.url_for("/the-range"),
    )
    monkeypatch.setattr(
        config,
        "ROBERT_DYAS_URL",
        httpserver.url_for("/robertdyas"),
    )
    return httpserver
