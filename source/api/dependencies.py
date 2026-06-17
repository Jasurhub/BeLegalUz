"""
FastAPI dependencies
"""

from functools import lru_cache
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from source.utils.config import get_settings, Settings
from source.services.rag_service import RAGService


@lru_cache()
def get_settings_dep() -> Settings:
    """Get cached settings"""
    return get_settings()


async def get_rag_service() -> RAGService:
    """
    Get RAG service instance.
    
    Returns:
        RAGService instance
    """
    # This should be managed by a proper dependency injection container
    # For now, we create a singleton
    if not hasattr(get_rag_service, "service"):
        get_rag_service.service = RAGService()
        await get_rag_service.service.initialize()
    return get_rag_service.service


async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> None:
    """
    Verify API key if required.
    
    Args:
        x_api_key: API key from header
    """
    settings = get_settings_dep()
    
    if settings.environment == "production":
        # Implement API key validation
        if not x_api_key or x_api_key != settings.secret_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )