"""
Integration tests for BeLagel API
"""

import pytest
from fastapi.testclient import TestClient
from source.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "BeLagel"


def test_list_legal_codes(client):
    """Test listing legal codes"""
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    """Test chat endpoint"""
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Mehnat ta'tili necha kun?",
            "code_filter": "MK"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["answer"]) > 0