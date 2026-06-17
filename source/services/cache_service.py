"""
Redis caching service
"""

import json
from typing import Optional, Any, Dict
import redis.asyncio as redis
from source.utils.logger import get_logger
from source.utils.config import get_settings

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service for query results.
    """
    
    def __init__(self):
        """Initialize cache service"""
        self.settings = get_settings()
        self.logger = logger
        self.redis: Optional[redis.Redis] = None
        self.prefix = "belagel:"
        self.default_ttl = self.settings.cache_ttl
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            self.logger.info("Cache service connected to Redis")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.logger.info("Cache service disconnected")
    
    def _get_key(self, key_type: str, identifier: str) -> str:
        """
        Generate cache key.
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier
        
        Returns:
            Full cache key
        """
        return f"{self.prefix}{key_type}:{identifier}"
    
    async def get(self, key_type: str, identifier: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier
        
        Returns:
            Cached value or None
        """
        if not self.redis:
            return None
        
        try:
            key = self._get_key(key_type, identifier)
            value = await self.redis.get(key)
            
            if value:
                self.logger.debug(f"Cache hit: {key}")
                return json.loads(value)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(
        self,
        key_type: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier
            value: Value to cache
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        if not self.redis:
            return False
        
        try:
            key = self._get_key(key_type, identifier)
            ttl = ttl or self.default_ttl
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key_type: str, identifier: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier
        
        Returns:
            True if deleted
        """
        if not self.redis:
            return False
        
        try:
            key = self._get_key(key_type, identifier)
            await self.redis.delete(key)
            self.logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            self.logger.warning(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern
        
        Returns:
            Number of deleted keys
        """
        if not self.redis:
            return 0
        
        try:
            full_pattern = f"{self.prefix}{pattern}*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=full_pattern,
                    count=100
                )
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                if cursor == 0:
                    break
            
            self.logger.info(f"Cleared {deleted_count} keys matching {pattern}")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return 0