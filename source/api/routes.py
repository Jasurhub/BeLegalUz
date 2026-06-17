"""
API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from source.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    StatsResponse,
    Citation
)
from source.api.dependencies import get_rag_service, get_settings_dep
from source.services.rag_service import RAGService
from source.utils.config import get_settings
import time
import uuid

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    settings = get_settings_dep()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        services={
            "api": True,
            "database": True,  # Should check actual connection
            "llm": True  # Should check actual connection
        }
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> ChatResponse:
    """
    Chat with legal AI assistant.
    
    Args:
        request: Chat request
        rag_service: RAG service
    
    Returns:
        Chat response
    """
    start_time = time.time()
    
    try:
        # Process query
        result = await rag_service.process_query(
            query=request.query,
            code_filter=request.code_filter,
            chat_id=request.chat_id or str(uuid.uuid4())
        )
        
        # Format citations
        citations = [
            Citation(
                code_name=c["code_name"],
                code_short=c.get("code_short"),
                article_number=c["article_number"],
                chapter=c.get("chapter")
            )
            for c in result.get("citations", [])
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            answer=result["answer"],
            citations=citations,
            sources=result.get("sources", []),
            query=request.query,
            chat_id=result["chat_id"],
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    rag_service: RAGService = Depends(get_rag_service)
) -> StatsResponse:
    """
    Get system statistics.
    
    Args:
        rag_service: RAG service
    
    Returns:
        Statistics
    """
    stats = await rag_service.get_stats()
    
    return StatsResponse(
        total_documents=stats.get("total_documents", 0),
        total_chunks=stats.get("total_chunks", 0),
        legal_codes=stats.get("legal_codes", []),
        last_updated=stats.get("last_updated")
    )


@router.get("/codes")
async def list_legal_codes() -> list:
    """
    List all available legal codes.
    
    Returns:
        List of legal codes
    """
    from source.utils.config import get_config
    config = get_config()
    return config.legal_codes