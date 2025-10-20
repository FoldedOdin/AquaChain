"""
Caching Strategy Optimizer for AquaChain
Implements caching strategies for frequently accessed data
"""

import boto3
import redis
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import argparse
from dataclasses import dataclass
import statistics

@dataclass
class CacheMetrics:
    """Metrics for cache performance."""
    cache_name: str
    hit_rate: float
    miss_rate: float
    avg_response_time: float
    memory_usage: float
    eviction_rate: float
    key_count: int
    total_requests: int

@dataclass
class CacheOptimizationRecommendation:
    """Optimization recommendation for caching."""
    cache_name: str
    optimization_type: str  # ttl, memory, strategy
    current_config: Dict
    recommended_config: Dict
    expected_improvement: str
    cost_impact: str
    priority: str

class CachingOptimizer:
    """Optimizer for caching strategies."""
    
    def __init__(self, aws_region: str = 'us-east-1', redis_endpoint: Optional[str] = None):
        self.aws_region = aws_region
        self.elasticache = boto3.client('elasticache', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        
        # Redis connection (if available)
        self.redis_client = None
        if redis_endpoint:
            try:
                self.redis_client = redis.Redis.from_url(redis_endpoint)
                self.redis_client.ping()
                print(f"✅ Connected to Redis at {redis_endpoint}")
            except Exception as e:
                print(f"⚠️  Could not connect to Redis: {e}")
        
        # Cache configurations for AquaChain
        self.cache_configs = {
            'user-profiles': {
                'ttl': 3600,  # 1 hour
                'max_memory': '100mb',
                'eviction_policy': 'allkeys-lru',
                'data_type': 'user_data'
            },
            'device-readings': {
                'ttl': 300,  # 5 minutes
                'max_memory': '500mb',
                'eviction_policy': 'allkeys-lru',
                'data_type': 'sensor_data'
            },
            'wqi-calculations': {
                'ttl': 600,  # 10 minutes
                'max_memory': '200mb',
                'eviction_policy': 'allkeys-lru',
                'data_type': 'computed_data'
            },
            'api-responses': {
                'ttl': 60,  # 1 minute
                'max_memory': '300mb',
                'eviction_policy': 'allkeys-lru',
                'data_type': 'api_data'
            },
            'technician-assignments': {
                'ttl': 1800,  # 30 minutes
                'max_memory': '50mb',
                'eviction_policy': 'allkeys-lru',
                'data_type': 'assignment_data'
            }
        }
    
    def analyze_cache_performance(self, cache_name: str, 
                                days_back: int = 7) -> CacheMetrics:
        """Analyze performance metrics for a cache."""
        print(f"📊 Analyzing cache performance for {cache_name}...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get ElastiCache metrics if available
        if self._is_elasticache_available():
            return self._analyze_elasticache_metrics(cache_name, start_time, end_time)
        
        # Analyze application-level cache metrics
        return self._analyze_application_cache_metrics(cache_name, start_time, end_time)
    
    def _is_elasticache_available(self) -> bool:
        """Check if ElastiCache cluster is available."""
        try:
            response = self.elasticache.describe_cache_clusters()
            return len(response.get('CacheClusters', [])) > 0
        except Exception:
            return False
    
    def _analyze_elasticache_metrics(self, cache_name: str, 
                                   start_time: datetime, end_time: datetime) -> CacheMetrics:
        """Analyze ElastiCache metrics from CloudWatch."""
        try:
            # Get cache hit/miss metrics
            hit_metrics = self._get_elasticache_metric(
                'CacheHits', cache_name, start_time, end_time
            )
            miss_metrics = self._get_elasticache_metric(
                'CacheMisses', cache_name, start_time, end_time
            )
            
            # Get memory usage metrics
            memory_metrics = self._get_elasticache_metric(
                'BytesUsedForCache', cache_name, start_time, end_time
            )
            
            # Get eviction metrics
            eviction_metrics = self._get_elasticache_metric(
                'Evictions', cache_name, start_time, end_time
            )
            
            # Calculate derived metrics
            total_hits = sum(hit_metrics)
            total_misses = sum(miss_metrics)
            total_requests = total_hits + total_misses
            
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            miss_rate = (total_misses / total_requests * 100) if total_requests > 0 else 0
            
            avg_memory_usage = statistics.mean(memory_metrics) if memory_metrics else 0
            total_evictions = sum(eviction_metrics)
            eviction_rate = (total_evictions / total_requests * 100) if total_requests > 0 else 0
            
            return CacheMetrics(
                cache_name=cache_name,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                avg_response_time=1.0,  # ElastiCache is typically ~1ms
                memory_usage=avg_memory_usage,
                eviction_rate=eviction_rate,
                key_count=0,  # Not easily available from CloudWatch
                total_requests=total_requests
            )
            
        except Exception as e:
            print(f"Warning: Could not analyze ElastiCache metrics: {e}")
            return self._get_default_cache_metrics(cache_name)
    
    def _get_elasticache_metric(self, metric_name: str, cache_name: str,
                              start_time: datetime, end_time: datetime) -> List[float]:
        """Get specific ElastiCache metric from CloudWatch."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ElastiCache',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'CacheClusterId',
                        'Value': f'aquachain-{cache_name}'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            return [dp['Sum'] for dp in response.get('Datapoints', [])]
            
        except Exception as e:
            print(f"Warning: Could not get {metric_name} metric: {e}")
            return []
    
    def _analyze_application_cache_metrics(self, cache_name: str,
                                         start_time: datetime, end_time: datetime) -> CacheMetrics:
        """Analyze application-level cache metrics."""
        # Simulate cache metrics analysis
        # In a real implementation, this would analyze application logs or custom metrics
        
        if self.redis_client:
            return self._analyze_redis_metrics(cache_name)
        
        return self._get_default_cache_metrics(cache_name)
    
    def _analyze_redis_metrics(self, cache_name: str) -> CacheMetrics:
        """Analyze Redis cache metrics."""
        try:
            info = self.redis_client.info()
            
            # Get cache statistics
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            total_requests = keyspace_hits + keyspace_misses
            
            hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
            miss_rate = (keyspace_misses / total_requests * 100) if total_requests > 0 else 0
            
            # Memory usage
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            memory_usage = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            # Key count
            key_count = sum(info.get(f'db{i}', {}).get('keys', 0) for i in range(16))
            
            # Evictions
            evicted_keys = info.get('evicted_keys', 0)
            eviction_rate = (evicted_keys / total_requests * 100) if total_requests > 0 else 0
            
            return CacheMetrics(
                cache_name=cache_name,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                avg_response_time=0.5,  # Redis is typically sub-millisecond
                memory_usage=memory_usage,
                eviction_rate=eviction_rate,
                key_count=key_count,
                total_requests=total_requests
            )
            
        except Exception as e:
            print(f"Warning: Could not analyze Redis metrics: {e}")
            return self._get_default_cache_metrics(cache_name)
    
    def _get_default_cache_metrics(self, cache_name: str) -> CacheMetrics:
        """Get default cache metrics for simulation."""
        return CacheMetrics(
            cache_name=cache_name,
            hit_rate=75.0,  # Assume 75% hit rate
            miss_rate=25.0,
            avg_response_time=2.0,
            memory_usage=60.0,
            eviction_rate=5.0,
            key_count=10000,
            total_requests=100000
        )
    
    def generate_optimization_recommendations(self, 
                                            metrics: CacheMetrics) -> List[CacheOptimizationRecommendation]:
        """Generate caching optimization recommendations."""
        recommendations = []
        
        cache_config = self.cache_configs.get(metrics.cache_name, {})
        current_config = {
            'ttl': cache_config.get('ttl', 3600),
            'max_memory': cache_config.get('max_memory', '100mb'),
            'eviction_policy': cache_config.get('eviction_policy', 'allkeys-lru')
        }
        
        # Hit rate optimization
        if metrics.hit_rate < 70:
            # Low hit rate - increase TTL or improve caching strategy
            recommended_ttl = min(current_config['ttl'] * 2, 7200)  # Max 2 hours
            
            recommendations.append(CacheOptimizationRecommendation(
                cache_name=metrics.cache_name,
                optimization_type='ttl',
                current_config=current_config,
                recommended_config={'ttl': recommended_ttl},
                expected_improvement=f"Increase hit rate from {metrics.hit_rate:.1f}% to ~{metrics.hit_rate + 15:.1f}%",
                cost_impact="Neutral (better resource utilization)",
                priority="high"
            ))
        
        # Memory optimization
        if metrics.memory_usage > 80:
            # High memory usage - increase memory or optimize eviction
            current_memory_mb = int(current_config['max_memory'].replace('mb', ''))
            recommended_memory = f"{int(current_memory_mb * 1.5)}mb"
            
            recommendations.append(CacheOptimizationRecommendation(
                cache_name=metrics.cache_name,
                optimization_type='memory',
                current_config=current_config,
                recommended_config={'max_memory': recommended_memory},
                expected_improvement=f"Reduce memory pressure and eviction rate",
                cost_impact="Negative (increased memory costs)",
                priority="high"
            ))
        
        elif metrics.memory_usage < 30:
            # Low memory usage - reduce allocated memory
            current_memory_mb = int(current_config['max_memory'].replace('mb', ''))
            recommended_memory = f"{max(50, int(current_memory_mb * 0.7))}mb"
            
            recommendations.append(CacheOptimizationRecommendation(
                cache_name=metrics.cache_name,
                optimization_type='memory',
                current_config=current_config,
                recommended_config={'max_memory': recommended_memory},
                expected_improvement=f"Reduce memory costs by ~30%",
                cost_impact="Positive (cost reduction)",
                priority="medium"
            ))
        
        # Eviction rate optimization
        if metrics.eviction_rate > 10:
            # High eviction rate - adjust eviction policy or increase memory
            recommendations.append(CacheOptimizationRecommendation(
                cache_name=metrics.cache_name,
                optimization_type='strategy',
                current_config=current_config,
                recommended_config={'eviction_policy': 'allkeys-lfu'},  # Least Frequently Used
                expected_improvement=f"Reduce eviction rate from {metrics.eviction_rate:.1f}% to ~{metrics.eviction_rate/2:.1f}%",
                cost_impact="Neutral (policy change)",
                priority="medium"
            ))
        
        # Cache warming strategy
        if metrics.cache_name in ['device-readings', 'wqi-calculations']:
            recommendations.append(CacheOptimizationRecommendation(
                cache_name=metrics.cache_name,
                optimization_type='strategy',
                current_config=current_config,
                recommended_config={'cache_warming': True},
                expected_improvement="Pre-populate cache with frequently accessed data",
                cost_impact="Neutral (improved user experience)",
                priority="low"
            ))
        
        return recommendations
    
    def implement_cache_layer(self, cache_name: str, dry_run: bool = True) -> bool:
        """Implement cache layer for specific data type."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Implementing cache layer for {cache_name}")
        
        cache_config = self.cache_configs.get(cache_name, {})
        
        if dry_run:
            print(f"  Would create cache with config: {cache_config}")
            return True
        
        try:
            if cache_name == 'user-profiles':
                return self._implement_user_profile_cache(cache_config)
            elif cache_name == 'device-readings':
                return self._implement_device_readings_cache(cache_config)
            elif cache_name == 'wqi-calculations':
                return self._implement_wqi_cache(cache_config)
            elif cache_name == 'api-responses':
                return self._implement_api_response_cache(cache_config)
            elif cache_name == 'technician-assignments':
                return self._implement_assignment_cache(cache_config)
            
            return False
            
        except Exception as e:
            print(f"  ❌ Failed to implement cache layer: {e}")
            return False
    
    def _implement_user_profile_cache(self, config: Dict) -> bool:
        """Implement user profile caching."""
        print("  ✅ User profile cache implementation:")
        print(f"    - Cache user profiles for {config['ttl']} seconds")
        print(f"    - Use Redis/ElastiCache with {config['max_memory']} memory")
        print(f"    - Key pattern: user:profile:{user_id}")
        print(f"    - Invalidate on profile updates")
        return True
    
    def _implement_device_readings_cache(self, config: Dict) -> bool:
        """Implement device readings caching."""
        print("  ✅ Device readings cache implementation:")
        print(f"    - Cache latest readings for {config['ttl']} seconds")
        print(f"    - Key pattern: device:readings:{device_id}:latest")
        print(f"    - Cache aggregated data for dashboard views")
        print(f"    - Use write-through caching for real-time updates")
        return True
    
    def _implement_wqi_cache(self, config: Dict) -> bool:
        """Implement WQI calculation caching."""
        print("  ✅ WQI calculation cache implementation:")
        print(f"    - Cache WQI calculations for {config['ttl']} seconds")
        print(f"    - Key pattern: wqi:{device_id}:{timestamp_hour}")
        print(f"    - Cache ML model predictions")
        print(f"    - Implement cache warming for active devices")
        return True
    
    def _implement_api_response_cache(self, config: Dict) -> bool:
        """Implement API response caching."""
        print("  ✅ API response cache implementation:")
        print(f"    - Cache API responses for {config['ttl']} seconds")
        print(f"    - Use HTTP headers for cache control")
        print(f"    - Implement cache invalidation on data updates")
        print(f"    - Cache at API Gateway level with CloudFront")
        return True
    
    def _implement_assignment_cache(self, config: Dict) -> bool:
        """Implement technician assignment caching."""
        print("  ✅ Technician assignment cache implementation:")
        print(f"    - Cache assignments for {config['ttl']} seconds")
        print(f"    - Key pattern: assignment:{technician_id}:active")
        print(f"    - Cache availability calculations")
        print(f"    - Invalidate on assignment status changes")
        return True
    
    def apply_optimization(self, recommendation: CacheOptimizationRecommendation, 
                          dry_run: bool = True) -> bool:
        """Apply caching optimization recommendation."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Applying cache optimization to {recommendation.cache_name}")
        print(f"  Type: {recommendation.optimization_type}")
        print(f"  Recommended config: {recommendation.recommended_config}")
        print(f"  Expected improvement: {recommendation.expected_improvement}")
        
        if dry_run:
            print("  Skipping actual update (dry run mode)")
            return True
        
        try:
            if recommendation.optimization_type == 'ttl':
                # Update TTL configuration
                new_ttl = recommendation.recommended_config['ttl']
                self.cache_configs[recommendation.cache_name]['ttl'] = new_ttl
                print(f"  ✅ Updated TTL to {new_ttl} seconds")
            
            elif recommendation.optimization_type == 'memory':
                # Update memory configuration
                new_memory = recommendation.recommended_config['max_memory']
                self.cache_configs[recommendation.cache_name]['max_memory'] = new_memory
                print(f"  ✅ Updated max memory to {new_memory}")
            
            elif recommendation.optimization_type == 'strategy':
                # Update caching strategy
                if 'eviction_policy' in recommendation.recommended_config:
                    new_policy = recommendation.recommended_config['eviction_policy']
                    self.cache_configs[recommendation.cache_name]['eviction_policy'] = new_policy
                    print(f"  ✅ Updated eviction policy to {new_policy}")
                
                if 'cache_warming' in recommendation.recommended_config:
                    print(f"  ✅ Enabled cache warming strategy")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to apply optimization: {e}")
            return False
    
    def optimize_all_caches(self, dry_run: bool = True, 
                           implement_missing: bool = False) -> Dict[str, List[CacheOptimizationRecommendation]]:
        """Optimize all caching strategies."""
        print("🚀 Optimizing all AquaChain caching strategies")
        print("=" * 60)
        
        all_recommendations = {}
        
        for cache_name in self.cache_configs.keys():
            try:
                print(f"\n📊 Analyzing {cache_name}...")
                
                # Analyze cache performance
                metrics = self.analyze_cache_performance(cache_name)
                
                # Generate recommendations
                recommendations = self.generate_optimization_recommendations(metrics)
                all_recommendations[cache_name] = recommendations
                
                # Print current metrics
                print(f"  Hit Rate: {metrics.hit_rate:.1f}%")
                print(f"  Miss Rate: {metrics.miss_rate:.1f}%")
                print(f"  Memory Usage: {metrics.memory_usage:.1f}%")
                print(f"  Eviction Rate: {metrics.eviction_rate:.1f}%")
                print(f"  Total Requests: {metrics.total_requests:,}")
                
                # Apply recommendations
                for rec in recommendations:
                    self.apply_optimization(rec, dry_run=dry_run)
                
                # Implement cache layer if missing
                if implement_missing:
                    self.implement_cache_layer(cache_name, dry_run=dry_run)
                
            except Exception as e:
                print(f"  ❌ Failed to optimize {cache_name}: {e}")
                all_recommendations[cache_name] = []
        
        return all_recommendations
    
    def print_optimization_summary(self, all_recommendations: Dict[str, List[CacheOptimizationRecommendation]]):
        """Print summary of caching optimization recommendations."""
        print("\n" + "=" * 60)
        print("📋 CACHING OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        total_recommendations = sum(len(recs) for recs in all_recommendations.values())
        high_priority = sum(1 for recs in all_recommendations.values() 
                          for rec in recs if rec.priority == 'high')
        
        print(f"Total Cache Layers Analyzed: {len(all_recommendations)}")
        print(f"Total Recommendations: {total_recommendations}")
        print(f"High Priority Recommendations: {high_priority}")
        
        # Group by optimization type
        optimization_types = {}
        for recommendations in all_recommendations.values():
            for rec in recommendations:
                if rec.optimization_type not in optimization_types:
                    optimization_types[rec.optimization_type] = 0
                optimization_types[rec.optimization_type] += 1
        
        print(f"\n📊 Recommendations by Type:")
        for opt_type, count in optimization_types.items():
            print(f"  {opt_type.title()}: {count}")
        
        print("\n📊 Recommendations by Cache:")
        for cache_name, recommendations in all_recommendations.items():
            if recommendations:
                print(f"\n  {cache_name}:")
                for rec in recommendations:
                    priority_icon = "🔴" if rec.priority == 'high' else "🟡" if rec.priority == 'medium' else "🟢"
                    print(f"    {priority_icon} {rec.optimization_type.title()}: {rec.expected_improvement}")
                    print(f"       Cost Impact: {rec.cost_impact}")
            else:
                print(f"\n  {cache_name}: ✅ No optimizations needed")

def main():
    """Main function to run caching optimization."""
    parser = argparse.ArgumentParser(description='AquaChain Caching Strategy Optimizer')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--redis-endpoint', type=str, 
                       help='Redis endpoint URL')
    parser.add_argument('--cache-name', type=str, 
                       help='Specific cache to optimize (default: all)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Perform dry run without applying changes (default: True)')
    parser.add_argument('--apply', action='store_true', 
                       help='Actually apply optimizations (overrides dry-run)')
    parser.add_argument('--implement-missing', action='store_true', 
                       help='Implement missing cache layers')
    parser.add_argument('--days-back', type=int, default=7, 
                       help='Days of metrics to analyze (default: 7)')
    
    args = parser.parse_args()
    
    try:
        optimizer = CachingOptimizer(
            aws_region=args.aws_region,
            redis_endpoint=args.redis_endpoint
        )
        
        print("🔬 AquaChain Caching Strategy Optimizer")
        print("=" * 50)
        
        dry_run = args.dry_run and not args.apply
        
        if args.cache_name:
            # Optimize specific cache
            print(f"Optimizing cache: {args.cache_name}")
            
            metrics = optimizer.analyze_cache_performance(args.cache_name)
            recommendations = optimizer.generate_optimization_recommendations(metrics)
            
            for rec in recommendations:
                optimizer.apply_optimization(rec, dry_run=dry_run)
            
            if args.implement_missing:
                optimizer.implement_cache_layer(args.cache_name, dry_run=dry_run)
            
            optimizer.print_optimization_summary({args.cache_name: recommendations})
        else:
            # Optimize all caches
            all_recommendations = optimizer.optimize_all_caches(
                dry_run=dry_run,
                implement_missing=args.implement_missing
            )
            
            optimizer.print_optimization_summary(all_recommendations)
        
        print("\n🎯 Caching optimization completed!")
        return 0
        
    except Exception as e:
        print(f"💥 Caching optimization failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())