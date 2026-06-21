import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["version"] == "1.0.0"
    assert "checks" in data


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "MarketPulse" in data["name"]
    assert "version" in data
    assert "endpoints" in data


def test_list_markets():
    response = client.get("/api/v1/markets/")
    assert response.status_code == 200
    data = response.json()
    assert "markets" in data


def test_current_score():
    response = client.get("/api/v1/scores/current?market=sp500")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "market_id" in data or "composite_score" in data


def test_composite_score():
    response = client.get("/api/v1/scores/composite?market=sp500")
    assert response.status_code == 200
    data = response.json()
    assert "composite_score" in data
    assert "regime" in data


def test_source_status():
    response = client.get("/api/v1/sources/status")
    assert response.status_code == 200


def test_embed_html():
    response = client.get("/api/v1/embed/marketpulse?market=sp500&size=medium")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_embed_html_small():
    response = client.get("/api/v1/embed/marketpulse?market=nasdaq100&size=small")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_embed_html_dark_theme():
    response = client.get("/api/v1/embed/marketpulse?market=dow&size=medium&theme=dark")
    assert response.status_code == 200
    body = response.text
    assert "#1a1a2e" in body or "dark" in body.lower()


def test_embed_json():
    response = client.get("/api/v1/embed/marketpulse.json?market=sp500")
    assert response.status_code == 200
    data = response.json()
    assert "widget" in data
    assert "embed" in data
    assert "composite_score" in data["widget"]


def test_api_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
