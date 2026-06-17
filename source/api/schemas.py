"""
Pydantic schemas for API requests and responses
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    query: str = Field(..., min_length=1, max_length=1000)
    code_filter: Optional[str] = Field(None, max_length=10)
    chat_id: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Mehnat ta'tili necha kun?",
                "code_filter": "MK"
            }
        }


class Citation(BaseModel):
    """Citation schema"""
    code_name: str
    code_short: Optional[str] = None
    article_number: str
    chapter: Optional[str] = None


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    answer: str
    citations: List[Citation]
    sources: List[Dict[str, Any]]
    query: str
    chat_id: str
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: Dict[str, bool]


class StatsResponse(BaseModel):
    """Statistics response"""
    total_documents: int
    total_chunks: int
    legal_codes: List[str]
    last_updated: Optional[str]


class ErrorMessage(BaseModel):
    """Error message schema"""
    detail: str
    error_code: Optional[str] = None