"""
Caching service for embeddings
"""

import json
import hashlib
from typing import List, Optional
import redis.asyncio as redis
from source.utils.logger import get_logger
from source.utils.config import get_config

logger = get_logger(__name__)


class EmbeddingCache:
    """
    Redis-based cache for embeddings to avoid recomputation.
    """
    
    def __init__(self):
        """Initialize embedding cache"""
        self.config = get_config()
        self.logger = logger
        self.redis: Optional[redis.Redis] = None
        self.prefix = "embedding:"
        self.ttl = 86400 * 30  # 30 days
    
    async def connect(self) -> None:
        """Connect to Redis"""
        redis_url = self.config.get("cache", {}).get(
            "redis_url", "redis://localhost:6379/0"
        )
        self.redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        self.logger.info("Embedding cache connected to Redis")
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.logger.info("Embedding cache disconnected from Redis")
    
    def _generate_key(self, text: str) -> str:
        """
        Generate cache key from text.
        
        Args:
            text: Input text
        
        Returns:
            Cache key
        """
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{self.prefix}{text_hash}"
    
    async def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Args:
            text: Input text
        
        Returns:
            Cached embedding or None
        """
        if not self.redis:
            return None
        
        try:
            key = self._generate_key(text)
            cached = await self.redis.get(key)
            
            if cached:
                embedding = json.loads(cached.decode("utf-8"))
                self.logger.debug(f"Cache hit for embedding")
                return embedding
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(self, text: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.
        
        Args:
            text: Input text
            embedding: Embedding vector
        """
        if not self.redis:
            return
        
        try:
            key = self._generate_key(text)
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(embedding).encode("utf-8")
            )
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
    
    async def clear(self) -> None:
        """Clear all cached embeddings"""
        if not self.redis:
            return
        
        try:
            pattern = f"{self.prefix}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            self.logger.info("Embedding cache cleared")
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")