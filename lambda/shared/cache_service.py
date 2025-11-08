"""
Cache Service for AquaChain
Provides Redis caching functionality for Lambda functions
"""

import os
import json
import redis
from typing import Optional, Any, List
from datetime import timedelta
from .structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class CacheService:
    """
    Service for interacting with ElastiCache Redis cluster
    """
    
    def __init__(self, redis_endpoint: Optional[str] = None, redis_port: int = 6379):
        """
        Initialize cache service
        
        Args:
            redis_endpoint: Redis cluster endpoint (defaults to env var)
            redis_port: Redis port (default 6379)
        """
        self.redis_endpoint = redis_endpoint or os.environ.get('REDIS_ENDPOINT')
        self.redis_port = redis_port
        
        if not self.redis_endpoint:
            logger.log('warning', 'Redis endpoint not configured, caching disabled')
            self.client = None
        else:
            try:
                self.client = redis.Redis(
                    host=self.redis_endpoint,
                    port=self.redis_port,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self.client.ping()
                logger.log('info', 'Redis connection established', 
                          endpoint=self.redis_endpoint)
            except Exception as e:
                logger.log('error', f'Failed to connect to Redis: {str(e)}',
                          endpoint=self.redis_endpoint)
                self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or cache unavailable
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                logger.log('debug', 'Cache hit', key=key)
                return json.loads(value)
            else:
                logger.log('debug', 'Cache miss', key=key)
                return None
        except json.JSONDecodeError as e:
            logger.log('error', f'Failed to decode cached value: {str(e)}', key=key)
            # Delete corrupted cache entry
            self.delete(key)
            return None
        except Exception as e:
            logger.log('error', f'Cache get error: {str(e)}', key=key)
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 300 = 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            serialized_value = json.dumps(value)
            self.client.setex(
                key,
                timedelta(seconds=ttl),
                serialized_value
            )
            logger.log('debug', 'Cache set', key=key, ttl=ttl)
            return True
        except (TypeError, ValueError) as e:
            logger.log('error', f'Failed to serialize value: {str(e)}', key=key)
            return False
        except Exception as e:
            logger.log('error', f'Cache set error: {str(e)}', key=key)
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            logger.log('debug', 'Cache delete', key=key)
            return True
        except Exception as e:
            logger.log('error', f'Cache delete error: {str(e)}', key=key)
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., 'device:*', 'user:123:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            deleted_count = 0
            # Use SCAN to avoid blocking Redis
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    self.client.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break
            
            logger.log('info', 'Cache pattern invalidated', 
                      pattern=pattern, deleted_count=deleted_count)
            return deleted_count
        except Exception as e:
            logger.log('error', f'Cache invalidate pattern error: {str(e)}', 
                      pattern=pattern)
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.log('error', f'Cache exists error: {str(e)}', key=key)
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, None if key doesn't exist or cache unavailable
        """
        if not self.client:
            return None
        
        try:
            ttl = self.client.ttl(key)
            if ttl == -2:  # Key doesn't exist
                return None
            elif ttl == -1:  # Key exists but has no expiration
                return -1
            else:
                return ttl
        except Exception as e:
            logger.log('error', f'Cache get TTL error: {str(e)}', key=key)
            return None
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter in cache
        
        Args:
            key: Cache key
            amount: Amount to increment by (default 1)
            
        Returns:
            New value after increment, None if error
        """
        if not self.client:
            return None
        
        try:
            new_value = self.client.incrby(key, amount)
            logger.log('debug', 'Cache increment', key=key, amount=amount, new_value=new_value)
            return new_value
        except Exception as e:
            logger.log('error', f'Cache increment error: {str(e)}', key=key)
            return None
    
    def get_many(self, keys: List[str]) -> dict:
        """
        Get multiple values from cache
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values (only includes found keys)
        """
        if not self.client or not keys:
            return {}
        
        try:
            values = self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.log('warning', 'Failed to decode cached value', key=key)
            
            logger.log('debug', 'Cache get many', 
                      requested=len(keys), found=len(result))
            return result
        except Exception as e:
            logger.log('error', f'Cache get many error: {str(e)}')
            return {}
    
    def set_many(self, mapping: dict, ttl: int = 300) -> bool:
        """
        Set multiple values in cache
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds (default 300 = 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not mapping:
            return False
        
        try:
            # Use pipeline for atomic operation
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                serialized_value = json.dumps(value)
                pipe.setex(key, timedelta(seconds=ttl), serialized_value)
            pipe.execute()
            
            logger.log('debug', 'Cache set many', count=len(mapping), ttl=ttl)
            return True
        except Exception as e:
            logger.log('error', f'Cache set many error: {str(e)}')
            return False
    
    def flush_all(self) -> bool:
        """
        Flush all keys from cache (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.log('warning', 'Cache flushed - all keys deleted')
            return True
        except Exception as e:
            logger.log('error', f'Cache flush error: {str(e)}')
            return False
    
    def get_stats(self) -> Optional[dict]:
        """
        Get Redis server statistics
        
        Returns:
            Dictionary of Redis stats or None if unavailable
        """
        if not self.client:
            return None
        
        try:
            info = self.client.info()
            return {
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.log('error', f'Failed to get cache stats: {str(e)}')
            return None
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                logger.log('info', 'Redis connection closed')
            except Exception as e:
                logger.log('error', f'Error closing Redis connection: {str(e)}')


# Singleton instance for reuse across Lambda invocations
_cache_service_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get singleton CacheService instance
    
    Returns:
        CacheService instance
    """
    global _cache_service_instance
    
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    
    return _cache_service_instance
