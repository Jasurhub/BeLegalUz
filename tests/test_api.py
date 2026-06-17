"""
Tests for FastAPI API endpoints
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from source.api.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_rag_service():
    with patch('src.api.dependencies.get_rag_service') as mock:
        service = AsyncMock()
        service.process_query.return_value = {
            "answer": "Mehnat ta'tili 15 kun.",
            "citations": [{"code_name": "MK", "article_number": "139"}],
            "sources": [{"code_name": "MK", "article_number": "139", "score": 0.95}],
            "chat_id": "test-123"
        }
        service.get_stats.return_value = {
            "total_documents": 100,
            "total_chunks": 500,
            "legal_codes": ["MK", "JK"],
            "last_updated": "2023-10-01"
        }
        mock.return_value = service
        yield service


def test_health_check(client):
    """Test /health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_legal_codes(client):
    """Test /codes endpoint"""
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_chat_endpoint(client, mock_rag_service):
    """Test /chat endpoint with mocked RAG service"""
    payload = {
        "query": "Mehnat ta'tili necha kun?",
        "code_filter": "MK"
    }
    
    response = client.post("/api/v1/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["answer"] == "Mehnat ta'tili 15 kun."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["article_number"] == "139"
    assert data["processing_time_ms"] > 0


def test_chat_endpoint_invalid_payload(client):
    """Test /chat endpoint with invalid payload"""
    payload = {"query": ""}  # Empty query should fail validation
    
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 422  # Unprocessable Entity