import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint should return a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Trading Chatbot API" in response.json()["message"]


def test_health_endpoint():
    """Health check should return status and timestamp."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "connections" in data


def test_screen_endpoint_returns_list():
    """Screen endpoint should return a list (possibly empty if no tickers)."""
    response = client.get("/api/screen", params={"limit": 2})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_endpoint_with_missing_data():
    """Chat endpoint should handle unknown tickers gracefully."""
    response = client.post("/api/chat", json={
        "ticker": "NONEXISTENT_TICKER_XYZ",
        "question": "What is the price?",
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_chat_endpoint_valid_request():
    """Chat endpoint should return a response for a valid ticker."""
    response = client.post("/api/chat", json={
        "ticker": "RELIANCE",
        "question": "hello",
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
