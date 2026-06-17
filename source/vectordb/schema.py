"""
Pydantic schemas for vector database payloads
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChunkPayload(BaseModel):
    """
    Schema for chunk payload stored in vector database.
    """
    
    # Core fields
    code_name: str = Field(..., description="Full name of legal code")
    code_short: str = Field(..., description="Short code identifier")
    article_number: str = Field(..., description="Article number")
    content: str = Field(..., description="Article text content")
    
    # Optional fields
    chapter: Optional[str] = Field(None, description="Chapter name")
    part_number: Optional[str] = Field(None, description="Part number within article")
    chunk_type: str = Field(default="article", description="Type of chunk")
    chunk_number: Optional[int] = Field(None, description="Chunk number if split")
    
    # Metadata
    is_active: bool = Field(default=True, description="Whether article is active")
    effective_date: Optional[str] = Field(None, description="Effective date")
    indexed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content_length: Optional[int] = Field(None, description="Content length in chars")
    word_count: Optional[int] = Field(None, description="Word count")
    version: str = Field(default="1.0", description="Version")
    source_type: str = Field(default="legal_code", description="Source type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code_name": "O'zbekiston Respublikasi Mehnat kodeksi",
                "code_short": "MK",
                "article_number": "100",
                "content": "Ish beruvchi quyidagi asoslarga ko'ra...",
                "chapter": "Ish beruvchi tashabbusi bilan...",
                "is_active": True,
                "chunk_type": "article"
            }
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Qdrant"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChunkPayload":
        """Create from dictionary"""
        return cls(**data)