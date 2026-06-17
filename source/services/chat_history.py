"""
Chat history service using PostgreSQL
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from source.utils.logger import get_logger
from source.utils.config import get_settings

logger = get_logger(__name__)
Base = declarative_base()


class ChatMessage(Base):
    """Chat message database model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(100), index=True)
    query = Column(Text)
    answer = Column(Text)
    citations = Column(JSON)
    sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer)


class ChatHistoryService:
    """
    Service for managing chat history.
    """
    
    def __init__(self):
        """Initialize chat history service"""
        self.settings = get_settings()
        self.logger = logger
        self.engine = None
        self.SessionLocal = None
    
    async def initialize(self) -> None:
        """Initialize database connection"""
        try:
            self.engine = create_async_engine(
                self.settings.database_url,
                echo=False
            )
            self.SessionLocal = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.logger.info("Chat history service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize chat history: {e}")
    
    async def close(self) -> None:
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Chat history service closed")
    
    async def save_message(
        self,
        chat_id: str,
        query: str,
        answer: str,
        citations: List[Dict],
        sources: List[Dict],
        processing_time_ms: float
    ) -> None:
        """
        Save chat message to database.
        
        Args:
            chat_id: Chat session ID
            query: User query
            answer: AI answer
            citations: List of citations
            sources: List of sources
            processing_time_ms: Processing time
        """
        if not self.SessionLocal:
            return
        
        try:
            async with self.SessionLocal() as session:
                message = ChatMessage(
                    chat_id=chat_id,
                    query=query,
                    answer=answer,
                    citations=citations,
                    sources=sources,
                    processing_time_ms=int(processing_time_ms)
                )
                session.add(message)
                await session.commit()
                self.logger.debug(f"Saved chat message: {chat_id}")
        except Exception as e:
            self.logger.error(f"Failed to save chat message: {e}")
    
    async def get_chat_history(
        self,
        chat_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            chat_id: Chat session ID
            limit: Maximum number of messages
        
        Returns:
            List of messages
        """
        if not self.SessionLocal:
            return []
        
        try:
            async with self.SessionLocal() as session:
                messages = await session.execute(
                    ChatMessage.__table__.select()
                    .where(ChatMessage.chat_id == chat_id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(limit)
                )
                return [dict(msg._mapping) for msg in messages]
        except Exception as e:
            self.logger.error(f"Failed to get chat history: {e}")
            return []