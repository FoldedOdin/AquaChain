"""
Cache Manager for ElastiCache integration
Provides caching layer for frequently accessed data
"""
import json
import logging
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CacheManager:
    """Redis-based cache manager for AquaChain API"""
    
    def __init__(self, redis_endpoint: str = None):
        self.redis_client = None
        self.cache_enabled = False
        
        try:
            import redis
            if redis_endpoint:
                host, port = redis_endpoint.split(':')
                self.redis_client = redis.Redis(
                    host=host,
                    port=int(port),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                self.cache_enabled = True
                logger.info("Cache manager initialized successfully")
            else:
                logger.warning("No Redis endpoint provided, caching disabled")
        except ImportError:
            logger.warning("Redis library not available, caching disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.cache_enabled:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.cache_enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.cache_enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache pattern delete error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.cache_enabled:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        if not self.cache_enabled:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {e}")
            return None
    
    def set_hash(self, key: str, field: str, value: Any) -> bool:
        """Set hash field in cache"""
        if not self.cache_enabled:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return bool(self.redis_client.hset(key, field, serialized_value))
        except Exception as e:
            logger.warning(f"Cache hash set error for key {key}, field {field}: {e}")
            return False
    
    def get_hash(self, key: str, field: str) -> Optional[Any]:
        """Get hash field from cache"""
        if not self.cache_enabled:
            return None
        
        try:
            value = self.redis_client.hget(key, field)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache hash get error for key {key}, field {field}: {e}")
            return None
    
    def get_all_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get all hash fields from cache"""
        if not self.cache_enabled:
            return None
        
        try:
            hash_data = self.redis_client.hgetall(key)
            if hash_data:
                return {field: json.loads(value) for field, value in hash_data.items()}
            return None
        except Exception as e:
            logger.warning(f"Cache hash getall error for key {key}: {e}")
            return None
    
    def add_to_set(self, key: str, *values: Any) -> int:
        """Add values to set in cache"""
        if not self.cache_enabled:
            return 0
        
        try:
            serialized_values = [json.dumps(value, default=str) for value in values]
            return self.redis_client.sadd(key, *serialized_values)
        except Exception as e:
            logger.warning(f"Cache set add error for key {key}: {e}")
            return 0
    
    def get_set_members(self, key: str) -> Optional[List[Any]]:
        """Get all members of set from cache"""
        if not self.cache_enabled:
            return None
        
        try:
            members = self.redis_client.smembers(key)
            if members:
                return [json.loads(member) for member in members]
            return []
        except Exception as e:
            logger.warning(f"Cache set members error for key {key}: {e}")
            return None
    
    def is_set_member(self, key: str, value: Any) -> bool:
        """Check if value is member of set"""
        if not self.cache_enabled:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return bool(self.redis_client.sismember(key, serialized_value))
        except Exception as e:
            logger.warning(f"Cache set member check error for key {key}: {e}")
            return False
    
    def push_to_list(self, key: str, *values: Any) -> int:
        """Push values to list in cache"""
        if not self.cache_enabled:
            return 0
        
        try:
            serialized_values = [json.dumps(value, default=str) for value in values]
            return self.redis_client.lpush(key, *serialized_values)
        except Exception as e:
            logger.warning(f"Cache list push error for key {key}: {e}")
            return 0
    
    def get_list_range(self, key: str, start: int = 0, end: int = -1) -> Optional[List[Any]]:
        """Get range of values from list"""
        if not self.cache_enabled:
            return None
        
        try:
            values = self.redis_client.lrange(key, start, end)
            if values:
                return [json.loads(value) for value in values]
            return []
        except Exception as e:
            logger.warning(f"Cache list range error for key {key}: {e}")
            return None
    
    def trim_list(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range"""
        if not self.cache_enabled:
            return False
        
        try:
            return bool(self.redis_client.ltrim(key, start, end))
        except Exception as e:
            logger.warning(f"Cache list trim error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        if not self.cache_enabled:
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.warning(f"Cache expire error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for key"""
        if not self.cache_enabled:
            return None
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.warning(f"Cache TTL error for key {key}: {e}")
            return None
    
    def generate_cache_key(self, prefix: str, *args: Any) -> str:
        """Generate consistent cache key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ':'.join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string
    
    def cache_device_readings(self, device_id: str, readings: List[Dict[str, Any]], 
                             start_date: datetime, end_date: datetime, ttl: int = 300) -> bool:
        """Cache device readings with metadata"""
        cache_key = self.generate_cache_key(
            'readings', device_id, start_date.isoformat(), end_date.isoformat()
        )
        
        cache_data = {
            'readings': readings,
            'metadata': {
                'deviceId': device_id,
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat(),
                'count': len(readings),
                'cachedAt': datetime.utcnow().isoformat()
            }
        }
        
        return self.set(cache_key, cache_data, ttl)
    
    def get_cached_device_readings(self, device_id: str, start_date: datetime, 
                                  end_date: datetime) -> Optional[List[Dict[str, Any]]]:
        """Get cached device readings"""
        cache_key = self.generate_cache_key(
            'readings', device_id, start_date.isoformat(), end_date.isoformat()
        )
        
        cached_data = self.get(cache_key)
        if cached_data and 'readings' in cached_data:
            return cached_data['readings']
        
        return None
    
    def cache_analytics_result(self, query_type: str, parameters: Dict[str, Any], 
                              result: Dict[str, Any], ttl: int = 600) -> bool:
        """Cache analytics query result"""
        param_hash = hashlib.md5(json.dumps(parameters, sort_keys=True).encode()).hexdigest()
        cache_key = self.generate_cache_key('analytics', query_type, param_hash)
        
        cache_data = {
            'result': result,
            'metadata': {
                'queryType': query_type,
                'parameters': parameters,
                'cachedAt': datetime.utcnow().isoformat()
            }
        }
        
        return self.set(cache_key, cache_data, ttl)
    
    def get_cached_analytics_result(self, query_type: str, 
                                   parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached analytics result"""
        param_hash = hashlib.md5(json.dumps(parameters, sort_keys=True).encode()).hexdigest()
        cache_key = self.generate_cache_key('analytics', query_type, param_hash)
        
        cached_data = self.get(cache_key)
        if cached_data and 'result' in cached_data:
            return cached_data['result']
        
        return None
    
    def invalidate_device_cache(self, device_id: str):
        """Invalidate all cache entries for a device"""
        pattern = f"readings:{device_id}:*"
        deleted_count = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} cache entries for device {device_id}")
        return deleted_count
    
    def invalidate_analytics_cache(self, query_type: str = None):
        """Invalidate analytics cache entries"""
        if query_type:
            pattern = f"analytics:{query_type}:*"
        else:
            pattern = "analytics:*"
        
        deleted_count = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} analytics cache entries")
        return deleted_count
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        if not self.cache_enabled:
            return None
        
        try:
            info = self.redis_client.info()
            return {
                'connected': True,
                'usedMemory': info.get('used_memory_human'),
                'connectedClients': info.get('connected_clients'),
                'totalCommandsProcessed': info.get('total_commands_processed'),
                'keyspaceHits': info.get('keyspace_hits'),
                'keyspaceMisses': info.get('keyspace_misses'),
                'hitRate': round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2
                )
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {'connected': False, 'error': str(e)}


# Global cache manager instance
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    return cache_manager


def initialize_cache(redis_endpoint: str) -> CacheManager:
    """Initialize cache manager with Redis endpoint"""
    global cache_manager
    cache_manager = CacheManager(redis_endpoint)
    return cache_manager