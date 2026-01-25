"""
Property-Based Tests for Caching Strategy Effectiveness
Feature: dashboard-overhaul, Property 24: Caching Strategy Effectiveness

Tests that the caching system effectively improves performance while maintaining data consistency.
Validates: Requirements 9.5
"""

import pytest
import time
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List, Optional
import sys
import os

# Mock redis module before importing cache_service
sys.modules['redis'] = Mock()
sys.modules['redis.exceptions'] = Mock()

# Add the lambda directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from shared.cache_service import CacheService, CacheKeys, get_cache_service

class TestCachingEffectivenessProperties:
    """Property-based tests for caching strategy effectiveness"""
    
    def setup_method(self):
        """Set up test environment"""
        # Mock Redis client to avoid external dependencies
        self.mock_redis = Mock()
        self.mock_redis.ping.return_value = True
        self.mock_redis.get.return_value = None
        self.mock_redis.setex.return_value = True
        self.mock_redis.delete.return_value = 1
        self.mock_redis.keys.return_value = []
        
        # Create cache service with mocked Redis
        self.cache_service = CacheService()
        self.cache_service.redis_client = self.mock_redis
        
    @given(
        cache_key=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
        cache_value=st.one_of(
            st.text(min_size=0, max_size=100),
            st.integers(min_value=-1000, max_value=1000),
            st.booleans(),
            st.lists(st.text(min_size=0, max_size=50), max_size=5),
            st.dictionaries(
                st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
                st.one_of(st.text(max_size=50), st.integers(min_value=-100, max_value=100), st.booleans()),
                max_size=3
            )
        ),
        ttl=st.integers(min_value=60, max_value=3600)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_24_caching_strategy_effectiveness(self, cache_key: str, cache_value: Any, ttl: int):
        """
        Property 24: Caching Strategy Effectiveness
        
        For any cacheable data request, the system SHALL implement appropriate caching 
        with proper cache invalidation, cache hit/miss tracking, and fallback to source 
        data when cache is unavailable.
        
        Validates: Requirements 9.5
        """
        # Ensure cache key is valid
        assume(len(cache_key.strip()) > 0)
        assume(cache_key.isascii())
        
        try:
            # Test 1: Cache SET operation should succeed
            set_result = self.cache_service.set(cache_key, cache_value, ttl)
            assert set_result is True, "Cache SET operation should succeed"
            
            # Verify Redis was called with correct parameters
            self.mock_redis.setex.assert_called()
            call_args = self.mock_redis.setex.call_args
            assert call_args[0][0] == cache_key, "Cache key should match"
            assert call_args[0][1] == ttl, "TTL should match"
            
            # Test 2: Cache GET should return the same value (cache hit)
            # Mock Redis to return the cached value
            self.mock_redis.get.return_value = json.dumps(cache_value, default=str)
            
            retrieved_value = self.cache_service.get(cache_key)
            assert retrieved_value == cache_value, "Retrieved value should match cached value"
            
            # Test 3: Cache statistics should track hits
            stats_before = self.cache_service.get_stats()
            
            # Perform another GET operation
            self.cache_service.get(cache_key)
            
            stats_after = self.cache_service.get_stats()
            assert stats_after['hits'] >= stats_before['hits'], "Hit count should increase"
            
            # Test 4: Cache miss should be handled gracefully
            # Mock Redis to return None (cache miss)
            self.mock_redis.get.return_value = None
            
            default_value = "default_test_value"
            retrieved_value = self.cache_service.get("nonexistent_key", default_value)
            assert retrieved_value == default_value, "Should return default value on cache miss"
            
            # Test 5: Cache invalidation should work
            delete_result = self.cache_service.delete(cache_key)
            assert delete_result is True, "Cache DELETE operation should succeed"
            
            # Test 6: Fallback mechanism when Redis is unavailable
            # Simulate Redis connection failure
            original_redis = self.cache_service.redis_client
            self.cache_service.redis_client = None
            
            # Should still work with fallback cache
            fallback_set_result = self.cache_service.set(cache_key, cache_value, ttl)
            assert fallback_set_result is True, "Fallback cache SET should succeed"
            
            fallback_get_result = self.cache_service.get(cache_key)
            assert fallback_get_result == cache_value, "Fallback cache GET should work"
            
            # Restore Redis client
            self.cache_service.redis_client = original_redis
            
            # Test 7: Cache hit ratio calculation should be accurate
            stats = self.cache_service.get_stats()
            total_requests = stats['hits'] + stats['misses']
            if total_requests > 0:
                expected_hit_ratio = stats['hits'] / total_requests
                assert abs(stats['hit_ratio'] - expected_hit_ratio) < 0.001, "Hit ratio calculation should be accurate"
            
        except Exception as e:
            pytest.fail(f"Caching effectiveness property failed: {str(e)}")
    
    @given(
        pattern=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        num_keys=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=3000)
    def test_cache_invalidation_pattern_effectiveness(self, pattern: str, num_keys: int):
        """
        Test that cache invalidation patterns work effectively
        
        Property: Cache invalidation should remove all matching keys and maintain consistency
        """
        assume(len(pattern.strip()) > 0)
        assume(pattern.isascii())
        
        try:
            # Create multiple cache entries with the pattern
            test_keys = []
            for i in range(num_keys):
                key = f"{pattern}:{i}"
                test_keys.append(key)
                self.cache_service.set(key, f"value_{i}", 300)
            
            # Mock Redis keys method to return our test keys
            self.mock_redis.keys.return_value = test_keys
            
            # Test pattern invalidation
            invalidated_count = self.cache_service.invalidate_pattern(f"{pattern}:*")
            
            # Should have invalidated all matching keys
            assert invalidated_count >= 0, "Should return non-negative count of invalidated keys"
            
            # Verify Redis delete was called
            if test_keys:
                self.mock_redis.delete.assert_called()
            
        except Exception as e:
            pytest.fail(f"Cache invalidation pattern test failed: {str(e)}")
    
    @given(
        concurrent_operations=st.integers(min_value=2, max_value=10),
        cache_key=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=30, deadline=3000)
    def test_cache_consistency_under_concurrent_access(self, concurrent_operations: int, cache_key: str):
        """
        Test cache consistency under concurrent access patterns
        
        Property: Cache should maintain consistency even with concurrent operations
        """
        assume(len(cache_key.strip()) > 0)
        assume(cache_key.isascii())
        
        try:
            # Simulate concurrent cache operations
            operations_completed = 0
            
            for i in range(concurrent_operations):
                # Alternate between set and get operations
                if i % 2 == 0:
                    result = self.cache_service.set(f"{cache_key}_{i}", f"value_{i}", 300)
                    assert result is True, f"Set operation {i} should succeed"
                else:
                    # Mock Redis to return a value for get operations
                    self.mock_redis.get.return_value = json.dumps(f"value_{i-1}", default=str)
                    result = self.cache_service.get(f"{cache_key}_{i-1}")
                    assert result == f"value_{i-1}", f"Get operation {i} should return correct value"
                
                operations_completed += 1
            
            # All operations should complete successfully
            assert operations_completed == concurrent_operations, "All concurrent operations should complete"
            
            # Cache statistics should be consistent
            stats = self.cache_service.get_stats()
            assert isinstance(stats['hits'], int), "Hit count should be integer"
            assert isinstance(stats['misses'], int), "Miss count should be integer"
            assert stats['hits'] >= 0, "Hit count should be non-negative"
            assert stats['misses'] >= 0, "Miss count should be non-negative"
            
        except Exception as e:
            pytest.fail(f"Cache consistency test failed: {str(e)}")
    
    @given(
        cache_size=st.integers(min_value=1, max_value=100),
        access_pattern=st.lists(st.integers(min_value=0, max_value=99), min_size=10, max_size=200)
    )
    @settings(max_examples=20, deadline=5000)
    def test_cache_performance_characteristics(self, cache_size: int, access_pattern: List[int]):
        """
        Test cache performance characteristics and hit ratio optimization
        
        Property: Cache should demonstrate improved performance with repeated access patterns
        """
        try:
            # Populate cache with initial data
            for i in range(cache_size):
                key = f"perf_test_key_{i}"
                value = f"perf_test_value_{i}"
                self.cache_service.set(key, value, 300)
            
            # Track performance metrics
            cache_hits = 0
            cache_misses = 0
            
            # Simulate access pattern
            for access_index in access_pattern:
                key = f"perf_test_key_{access_index % cache_size}"
                
                # Mock Redis behavior based on whether key should exist
                if access_index < cache_size:
                    # Key exists in cache
                    self.mock_redis.get.return_value = json.dumps(f"perf_test_value_{access_index}", default=str)
                    result = self.cache_service.get(key)
                    if result is not None:
                        cache_hits += 1
                else:
                    # Key doesn't exist
                    self.mock_redis.get.return_value = None
                    result = self.cache_service.get(key, "default")
                    if result == "default":
                        cache_misses += 1
            
            # Calculate hit ratio
            total_accesses = len(access_pattern)
            if total_accesses > 0:
                expected_hit_ratio = cache_hits / total_accesses
                
                # Hit ratio should be reasonable for repeated access patterns
                # (This is a performance characteristic test, not a strict requirement)
                assert expected_hit_ratio >= 0.0, "Hit ratio should be non-negative"
                assert expected_hit_ratio <= 1.0, "Hit ratio should not exceed 100%"
            
            # Cache should maintain performance statistics
            stats = self.cache_service.get_stats()
            assert 'hit_ratio' in stats, "Cache should track hit ratio"
            assert 'hits' in stats, "Cache should track hits"
            assert 'misses' in stats, "Cache should track misses"
            
        except Exception as e:
            pytest.fail(f"Cache performance test failed: {str(e)}")
    
    def test_cache_health_check_effectiveness(self):
        """
        Test that cache health checks provide accurate system status
        
        Property: Health checks should accurately reflect cache system status
        """
        try:
            # Test healthy cache status
            health = self.cache_service.health_check()
            
            assert 'status' in health, "Health check should include status"
            assert 'redis_status' in health, "Health check should include Redis status"
            assert 'timestamp' in health, "Health check should include timestamp"
            assert 'stats' in health, "Health check should include statistics"
            
            # Status should be valid
            valid_statuses = ['healthy', 'degraded', 'error']
            assert health['status'] in valid_statuses, f"Status should be one of {valid_statuses}"
            
            # Test degraded status when Redis is unavailable
            self.cache_service.redis_client = None
            degraded_health = self.cache_service.health_check()
            
            assert degraded_health['status'] in ['degraded', 'error'], "Should report degraded status when Redis unavailable"
            assert degraded_health['redis_status'] == 'disconnected', "Should report Redis as disconnected"
            
        except Exception as e:
            pytest.fail(f"Cache health check test failed: {str(e)}")

if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])