"""
Tests for retrieval system
"""

import pytest
from source.retrieval.retriever import LegalRetriever
from source.embeddings.embedder import EmbeddingService
from source.vectordb.vector_store import VectorStore


@pytest.fixture
def retriever():
    """Create retriever instance"""
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    return LegalRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store
    )


@pytest.mark.asyncio
async def test_detect_legal_code(retriever):
    """Test legal code detection"""
    query = "Mehnat kodeksiga ko'ra ishdan bo'shatish"
    code = await retriever.detect_legal_code(query)
    assert code == "MK"


@pytest.mark.asyncio
async def test_retrieve(retriever):
    """Test retrieval"""
    results = await retriever.retrieve(
        query="Mehnat ta'tili",
        code_filter="MK",
        top_k=3
    )
    assert len(results) > 0
    for payload, score in results:
        assert payload.code_short == "MK"
        assert score > 0