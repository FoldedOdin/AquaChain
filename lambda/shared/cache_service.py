"""
Dashboard Caching Service
Provides Redis-based caching with fallback mechanisms for dashboard services
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service with fallback mechanisms and monitoring
    """
    
    def __init__(self, redis_endpoint: Optional[str] = None, redis_port: int = 6379):
        """
        Initialize cache service
        
        Args:
            redis_endpoint: Redis cluster endpoint (from environment if not provided)
            redis_port: Redis port (default 6379)
        """
        self.redis_endpoint = redis_endpoint or os.environ.get('REDIS_ENDPOINT')
        self.redis_port = redis_port
        self.redis_client = None
        self.fallback_cache = {}  # In-memory fallback cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'fallback_hits': 0
        }
        
        # Initialize Redis connection
        self._initialize_redis()
    
    def _initialize_redis(self) -> None:
        """
        Initialize Redis connection with error handling
        """
        if not self.redis_endpoint:
            logger.warning("Redis endpoint not configured, using fallback cache only")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_endpoint,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                ssl=True,  # ElastiCache with encryption in transit
                ssl_cert_reqs=None
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connection established to {self.redis_endpoint}:{self.redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            self.redis_client = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with fallback mechanisms
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value is not None:
                        self.cache_stats['hits'] += 1
                        return json.loads(value)
                except (RedisError, ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis get error for key {key}: {str(e)}")
                    self.cache_stats['errors'] += 1
                    # Fall through to fallback cache
            
            # Try fallback cache
            if key in self.fallback_cache:
                cache_entry = self.fallback_cache[key]
                if cache_entry['expires_at'] > time.time():
                    self.cache_stats['fallback_hits'] += 1
                    return cache_entry['value']
                else:
                    # Expired entry
                    del self.fallback_cache[key]
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            self.cache_stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value, default=str)
            
            # Try Redis first
            if self.redis_client:
                try:
                    result = self.redis_client.setex(key, ttl, serialized_value)
                    if result:
                        # Also store in fallback cache for redundancy
                        self.fallback_cache[key] = {
                            'value': value,
                            'expires_at': time.time() + ttl
                        }
                        return True
                except (RedisError, ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis set error for key {key}: {str(e)}")
                    # Fall through to fallback cache
            
            # Use fallback cache
            self.fallback_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            
            # Clean up expired entries periodically
            self._cleanup_fallback_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = False
            
            # Delete from Redis
            if self.redis_client:
                try:
                    result = self.redis_client.delete(key)
                    success = result > 0
                except (RedisError, ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis delete error for key {key}: {str(e)}")
            
            # Delete from fallback cache
            if key in self.fallback_cache:
                del self.fallback_cache[key]
                success = True
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*", "inventory:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0
            
            # Redis pattern deletion
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        deleted_count = self.redis_client.delete(*keys)
                except (RedisError, ConnectionError, TimeoutError) as e:
                    logger.warning(f"Redis pattern delete error for pattern {pattern}: {str(e)}")
            
            # Fallback cache pattern deletion
            import fnmatch
            keys_to_delete = [
                key for key in self.fallback_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                del self.fallback_cache[key]
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for pattern {pattern}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache_stats.copy()
        
        # Calculate hit ratio
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_ratio'] = stats['hits'] / total_requests
            stats['fallback_ratio'] = stats['fallback_hits'] / total_requests
        else:
            stats['hit_ratio'] = 0.0
            stats['fallback_ratio'] = 0.0
        
        # Redis connection status
        stats['redis_connected'] = self._is_redis_connected()
        stats['fallback_cache_size'] = len(self.fallback_cache)
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache service
        
        Returns:
            Health check results
        """
        health = {
            'status': 'healthy',
            'redis_status': 'disconnected',
            'fallback_cache_status': 'available',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check Redis connection
        if self._is_redis_connected():
            health['redis_status'] = 'connected'
            try:
                # Test Redis operations
                test_key = f"health_check_{int(time.time())}"
                self.redis_client.setex(test_key, 10, "test")
                value = self.redis_client.get(test_key)
                self.redis_client.delete(test_key)
                
                if value == "test":
                    health['redis_status'] = 'healthy'
                else:
                    health['redis_status'] = 'degraded'
                    
            except Exception as e:
                health['redis_status'] = 'error'
                health['redis_error'] = str(e)
        
        # Overall status
        if health['redis_status'] in ['disconnected', 'error']:
            health['status'] = 'degraded'  # Still functional with fallback
        
        # Add statistics
        health['stats'] = self.get_stats()
        
        return health
    
    def _is_redis_connected(self) -> bool:
        """
        Check if Redis is connected and responsive
        
        Returns:
            True if Redis is connected, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def _cleanup_fallback_cache(self) -> None:
        """
        Clean up expired entries from fallback cache
        """
        try:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.fallback_cache.items()
                if entry['expires_at'] <= current_time
            ]
            
            for key in expired_keys:
                del self.fallback_cache[key]
                
            # Limit fallback cache size to prevent memory issues
            if len(self.fallback_cache) > 1000:
                # Remove oldest entries
                sorted_entries = sorted(
                    self.fallback_cache.items(),
                    key=lambda x: x[1]['expires_at']
                )
                
                # Keep only the 800 most recent entries
                keys_to_remove = [entry[0] for entry in sorted_entries[:-800]]
                for key in keys_to_remove:
                    del self.fallback_cache[key]
                    
        except Exception as e:
            logger.error(f"Fallback cache cleanup error: {str(e)}")

# Cache key generators for consistent naming
class CacheKeys:
    """
    Standardized cache key generators for dashboard services
    """
    
    @staticmethod
    def user_permissions(user_id: str) -> str:
        """Generate cache key for user permissions"""
        return f"user:permissions:{user_id}"
    
    @staticmethod
    def user_roles(user_id: str) -> str:
        """Generate cache key for user roles"""
        return f"user:roles:{user_id}"
    
    @staticmethod
    def inventory_item(item_id: str) -> str:
        """Generate cache key for inventory item"""
        return f"inventory:item:{item_id}"
    
    @staticmethod
    def inventory_alerts(user_id: str) -> str:
        """Generate cache key for inventory alerts"""
        return f"inventory:alerts:{user_id}"
    
    @staticmethod
    def budget_utilization(category: str, period: str) -> str:
        """Generate cache key for budget utilization"""
        return f"budget:utilization:{category}:{period}"
    
    @staticmethod
    def purchase_order_queue(user_id: str) -> str:
        """Generate cache key for purchase order approval queue"""
        return f"procurement:queue:{user_id}"
    
    @staticmethod
    def supplier_performance(supplier_id: str) -> str:
        """Generate cache key for supplier performance data"""
        return f"supplier:performance:{supplier_id}"
    
    @staticmethod
    def workflow_status(workflow_id: str) -> str:
        """Generate cache key for workflow status"""
        return f"workflow:status:{workflow_id}"
    
    @staticmethod
    def dashboard_data(role: str, user_id: str) -> str:
        """Generate cache key for dashboard data"""
        return f"dashboard:{role}:{user_id}"

# Global cache service instance
cache_service = None

def get_cache_service() -> CacheService:
    """
    Get global cache service instance (singleton pattern)
    
    Returns:
        CacheService instance
    """
    global cache_service
    
    if cache_service is None:
        cache_service = CacheService()
    
    return cache_service

# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cache = get_cache_service()
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator