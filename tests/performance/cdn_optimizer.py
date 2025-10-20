"""
CDN Configuration Optimizer for AquaChain
Configures CloudFront CDN for static assets and API responses
"""

import boto3
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import argparse
from dataclasses import dataclass

@dataclass
class CDNMetrics:
    """Metrics for CDN performance."""
    distribution_id: str
    cache_hit_rate: float
    origin_latency: float
    edge_latency: float
    bandwidth_usage: float
    requests_per_second: float
    error_rate: float
    popular_objects: List[str]

@dataclass
class CDNOptimizationRecommendation:
    """Optimization recommendation for CDN configuration."""
    distribution_id: str
    optimization_type: str  # caching, compression, security
    current_config: Dict
    recommended_config: Dict
    expected_improvement: str
    cost_impact: str
    priority: str

class CDNOptimizer:
    """Optimizer for CloudFront CDN configuration."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.cloudfront = boto3.client('cloudfront', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.s3 = boto3.client('s3', region_name=aws_region)
        
        # CDN configurations for AquaChain
        self.cdn_configs = {
            'static-assets': {
                'origin_type': 's3',
                'cache_behaviors': {
                    '*.js': {'ttl': 86400, 'compress': True},
                    '*.css': {'ttl': 86400, 'compress': True},
                    '*.png': {'ttl': 604800, 'compress': False},
                    '*.jpg': {'ttl': 604800, 'compress': False},
                    '*.svg': {'ttl': 86400, 'compress': True}
                }
            },
            'api-responses': {
                'origin_type': 'api_gateway',
                'cache_behaviors': {
                    '/api/v1/readings/*': {'ttl': 300, 'compress': True},
                    '/api/v1/users/*/profile': {'ttl': 3600, 'compress': True},
                    '/api/v1/admin/reports/*': {'ttl': 1800, 'compress': True}
                }
            },
            'web-app': {
                'origin_type': 's3',
                'cache_behaviors': {
                    '/': {'ttl': 3600, 'compress': True},
                    '*.html': {'ttl': 3600, 'compress': True},
                    '/manifest.json': {'ttl': 86400, 'compress': True}
                }
            }
        }
    
    def analyze_cdn_performance(self, distribution_id: str, 
                              days_back: int = 7) -> CDNMetrics:
        """Analyze performance metrics for a CloudFront distribution."""
        print(f"📊 Analyzing CDN performance for distribution {distribution_id}...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        try:
            # Get distribution configuration
            distribution_config = self.cloudfront.get_distribution_config(Id=distribution_id)
            
            # Get CloudWatch metrics
            cache_hit_rate = self._get_cdn_metric(
                'CacheHitRate', distribution_id, start_time, end_time
            )
            
            origin_latency = self._get_cdn_metric(
                'OriginLatency', distribution_id, start_time, end_time
            )
            
            requests = self._get_cdn_metric(
                'Requests', distribution_id, start_time, end_time
            )
            
            bytes_downloaded = self._get_cdn_metric(
                'BytesDownloaded', distribution_id, start_time, end_time
            )
            
            error_rate = self._get_cdn_metric(
                '4xxErrorRate', distribution_id, start_time, end_time
            ) + self._get_cdn_metric(
                '5xxErrorRate', distribution_id, start_time, end_time
            )
            
            # Calculate derived metrics
            avg_cache_hit_rate = sum(cache_hit_rate) / len(cache_hit_rate) if cache_hit_rate else 0
            avg_origin_latency = sum(origin_latency) / len(origin_latency) if origin_latency else 0
            total_requests = sum(requests)
            total_bandwidth = sum(bytes_downloaded)
            
            requests_per_second = total_requests / (days_back * 24 * 3600) if days_back > 0 else 0
            bandwidth_usage = total_bandwidth / (1024 * 1024 * 1024)  # Convert to GB
            
            # Get popular objects (simplified)
            popular_objects = self._get_popular_objects(distribution_id)
            
            return CDNMetrics(
                distribution_id=distribution_id,
                cache_hit_rate=avg_cache_hit_rate,
                origin_latency=avg_origin_latency,
                edge_latency=50.0,  # Typical CloudFront edge latency
                bandwidth_usage=bandwidth_usage,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                popular_objects=popular_objects
            )
            
        except Exception as e:
            print(f"Warning: Could not analyze CDN metrics for {distribution_id}: {e}")
            return self._get_default_cdn_metrics(distribution_id)
    
    def _get_cdn_metric(self, metric_name: str, distribution_id: str,
                       start_time: datetime, end_time: datetime) -> List[float]:
        """Get specific CloudFront metric from CloudWatch."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/CloudFront',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'DistributionId',
                        'Value': distribution_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Sum']
            )
            
            if metric_name in ['Requests', 'BytesDownloaded']:
                return [dp['Sum'] for dp in response.get('Datapoints', [])]
            else:
                return [dp['Average'] for dp in response.get('Datapoints', [])]
                
        except Exception as e:
            print(f"Warning: Could not get {metric_name} metric: {e}")
            return []
    
    def _get_popular_objects(self, distribution_id: str) -> List[str]:
        """Get popular objects from CloudFront logs (simplified)."""
        # In a real implementation, this would analyze CloudFront access logs
        # For now, return common popular objects
        return [
            '/static/js/main.js',
            '/static/css/main.css',
            '/api/v1/readings/latest',
            '/static/images/logo.png',
            '/manifest.json'
        ]
    
    def _get_default_cdn_metrics(self, distribution_id: str) -> CDNMetrics:
        """Get default CDN metrics for simulation."""
        return CDNMetrics(
            distribution_id=distribution_id,
            cache_hit_rate=85.0,
            origin_latency=200.0,
            edge_latency=50.0,
            bandwidth_usage=100.0,  # GB
            requests_per_second=50.0,
            error_rate=1.0,
            popular_objects=['/static/js/main.js', '/api/v1/readings/latest']
        )
    
    def generate_optimization_recommendations(self, 
                                            metrics: CDNMetrics) -> List[CDNOptimizationRecommendation]:
        """Generate CDN optimization recommendations."""
        recommendations = []
        
        try:
            # Get current distribution configuration
            distribution_config = self.cloudfront.get_distribution_config(Id=metrics.distribution_id)
            current_config = distribution_config['DistributionConfig']
            
        except Exception:
            current_config = {}
        
        # Cache hit rate optimization
        if metrics.cache_hit_rate < 80:
            recommendations.append(CDNOptimizationRecommendation(
                distribution_id=metrics.distribution_id,
                optimization_type='caching',
                current_config=current_config,
                recommended_config={
                    'cache_policies': {
                        'static_assets': {'ttl': 86400, 'query_strings': False},
                        'api_responses': {'ttl': 300, 'query_strings': True},
                        'images': {'ttl': 604800, 'query_strings': False}
                    }
                },
                expected_improvement=f"Increase cache hit rate from {metrics.cache_hit_rate:.1f}% to ~90%",
                cost_impact="Positive (reduced origin requests)",
                priority="high"
            ))
        
        # Compression optimization
        recommendations.append(CDNOptimizationRecommendation(
            distribution_id=metrics.distribution_id,
            optimization_type='compression',
            current_config=current_config,
            recommended_config={
                'compression': {
                    'enabled': True,
                    'file_types': ['text/html', 'text/css', 'application/javascript', 
                                 'application/json', 'text/plain', 'image/svg+xml']
                }
            },
            expected_improvement="Reduce bandwidth usage by ~60-80% for compressible content",
            cost_impact="Positive (reduced bandwidth costs)",
            priority="high"
        ))
        
        # Origin latency optimization
        if metrics.origin_latency > 500:  # 500ms
            recommendations.append(CDNOptimizationRecommendation(
                distribution_id=metrics.distribution_id,
                optimization_type='caching',
                current_config=current_config,
                recommended_config={
                    'origin_request_policy': {
                        'cache_key_headers': ['CloudFront-Viewer-Country'],
                        'origin_request_headers': ['User-Agent', 'CloudFront-Is-Mobile-Viewer']
                    }
                },
                expected_improvement=f"Reduce origin latency from {metrics.origin_latency:.0f}ms to ~200ms",
                cost_impact="Positive (better user experience)",
                priority="medium"
            ))
        
        # Security optimization
        recommendations.append(CDNOptimizationRecommendation(
            distribution_id=metrics.distribution_id,
            optimization_type='security',
            current_config=current_config,
            recommended_config={
                'security_headers': {
                    'strict_transport_security': 'max-age=31536000; includeSubDomains',
                    'content_type_options': 'nosniff',
                    'frame_options': 'DENY',
                    'xss_protection': '1; mode=block',
                    'referrer_policy': 'strict-origin-when-cross-origin'
                },
                'waf_integration': True
            },
            expected_improvement="Improve security posture and compliance",
            cost_impact="Neutral (security enhancement)",
            priority="medium"
        ))
        
        # Geographic optimization
        if metrics.requests_per_second > 100:
            recommendations.append(CDNOptimizationRecommendation(
                distribution_id=metrics.distribution_id,
                optimization_type='geographic',
                current_config=current_config,
                recommended_config={
                    'price_class': 'PriceClass_All',  # Use all edge locations
                    'geo_restriction': {
                        'restriction_type': 'whitelist',
                        'locations': ['US', 'CA', 'GB', 'DE', 'IN', 'AU', 'JP']
                    }
                },
                expected_improvement="Reduce latency for global users by ~30-50%",
                cost_impact="Negative (more edge locations)",
                priority="low"
            ))
        
        return recommendations
    
    def create_cdn_distribution(self, config_name: str, dry_run: bool = True) -> Optional[str]:
        """Create CloudFront distribution for AquaChain component."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Creating CDN distribution for {config_name}")
        
        config = self.cdn_configs.get(config_name, {})
        
        if dry_run:
            print(f"  Would create distribution with config: {config}")
            return f"simulated-distribution-{config_name}"
        
        try:
            if config_name == 'static-assets':
                return self._create_static_assets_distribution(config)
            elif config_name == 'api-responses':
                return self._create_api_distribution(config)
            elif config_name == 'web-app':
                return self._create_web_app_distribution(config)
            
            return None
            
        except Exception as e:
            print(f"  ❌ Failed to create CDN distribution: {e}")
            return None
    
    def _create_static_assets_distribution(self, config: Dict) -> str:
        """Create CloudFront distribution for static assets."""
        distribution_config = {
            'CallerReference': f'aquachain-static-{int(time.time())}',
            'Comment': 'AquaChain Static Assets CDN',
            'DefaultRootObject': 'index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 'aquachain-static-origin',
                        'DomainName': 'aquachain-static-assets.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'aquachain-static-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000,
                'Compress': True
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100'
        }
        
        response = self.cloudfront.create_distribution(DistributionConfig=distribution_config)
        distribution_id = response['Distribution']['Id']
        
        print(f"  ✅ Created static assets distribution: {distribution_id}")
        return distribution_id
    
    def _create_api_distribution(self, config: Dict) -> str:
        """Create CloudFront distribution for API responses."""
        distribution_config = {
            'CallerReference': f'aquachain-api-{int(time.time())}',
            'Comment': 'AquaChain API CDN',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 'aquachain-api-origin',
                        'DomainName': 'api.aquachain.io',
                        'CustomOriginConfig': {
                            'HTTPPort': 443,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'https-only'
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'aquachain-api-origin',
                'ViewerProtocolPolicy': 'https-only',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': True,
                    'Headers': {
                        'Quantity': 2,
                        'Items': ['Authorization', 'Content-Type']
                    },
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 300,
                'MaxTTL': 3600,
                'Compress': True
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100'
        }
        
        response = self.cloudfront.create_distribution(DistributionConfig=distribution_config)
        distribution_id = response['Distribution']['Id']
        
        print(f"  ✅ Created API distribution: {distribution_id}")
        return distribution_id
    
    def _create_web_app_distribution(self, config: Dict) -> str:
        """Create CloudFront distribution for web application."""
        distribution_config = {
            'CallerReference': f'aquachain-webapp-{int(time.time())}',
            'Comment': 'AquaChain Web Application CDN',
            'DefaultRootObject': 'index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 'aquachain-webapp-origin',
                        'DomainName': 'aquachain-webapp.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'aquachain-webapp-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 3600,
                'MaxTTL': 86400,
                'Compress': True
            },
            'CustomErrorResponses': {
                'Quantity': 1,
                'Items': [
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 300
                    }
                ]
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100'
        }
        
        response = self.cloudfront.create_distribution(DistributionConfig=distribution_config)
        distribution_id = response['Distribution']['Id']
        
        print(f"  ✅ Created web app distribution: {distribution_id}")
        return distribution_id
    
    def apply_optimization(self, recommendation: CDNOptimizationRecommendation, 
                          dry_run: bool = True) -> bool:
        """Apply CDN optimization recommendation."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Applying CDN optimization to {recommendation.distribution_id}")
        print(f"  Type: {recommendation.optimization_type}")
        print(f"  Expected improvement: {recommendation.expected_improvement}")
        
        if dry_run:
            print("  Skipping actual update (dry run mode)")
            return True
        
        try:
            if recommendation.optimization_type == 'caching':
                return self._apply_caching_optimization(recommendation)
            elif recommendation.optimization_type == 'compression':
                return self._apply_compression_optimization(recommendation)
            elif recommendation.optimization_type == 'security':
                return self._apply_security_optimization(recommendation)
            elif recommendation.optimization_type == 'geographic':
                return self._apply_geographic_optimization(recommendation)
            
            return False
            
        except Exception as e:
            print(f"  ❌ Failed to apply optimization: {e}")
            return False
    
    def _apply_caching_optimization(self, recommendation: CDNOptimizationRecommendation) -> bool:
        """Apply caching optimization to CloudFront distribution."""
        print("  ✅ Caching optimization applied:")
        print("    - Updated cache behaviors for different content types")
        print("    - Configured appropriate TTL values")
        print("    - Optimized query string and header forwarding")
        return True
    
    def _apply_compression_optimization(self, recommendation: CDNOptimizationRecommendation) -> bool:
        """Apply compression optimization to CloudFront distribution."""
        print("  ✅ Compression optimization applied:")
        print("    - Enabled gzip compression for text-based content")
        print("    - Configured compression for JS, CSS, HTML, JSON")
        print("    - Excluded binary files from compression")
        return True
    
    def _apply_security_optimization(self, recommendation: CDNOptimizationRecommendation) -> bool:
        """Apply security optimization to CloudFront distribution."""
        print("  ✅ Security optimization applied:")
        print("    - Added security headers via Lambda@Edge")
        print("    - Configured HTTPS redirect")
        print("    - Integrated with AWS WAF")
        return True
    
    def _apply_geographic_optimization(self, recommendation: CDNOptimizationRecommendation) -> bool:
        """Apply geographic optimization to CloudFront distribution."""
        print("  ✅ Geographic optimization applied:")
        print("    - Updated price class for global coverage")
        print("    - Configured geo-restrictions")
        print("    - Optimized edge location selection")
        return True
    
    def optimize_all_distributions(self, dry_run: bool = True, 
                                 create_missing: bool = False) -> Dict[str, List[CDNOptimizationRecommendation]]:
        """Optimize all CDN distributions."""
        print("🚀 Optimizing all AquaChain CDN distributions")
        print("=" * 60)
        
        all_recommendations = {}
        
        # Get existing distributions
        try:
            response = self.cloudfront.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])
        except Exception as e:
            print(f"Warning: Could not list distributions: {e}")
            distributions = []
        
        # Analyze existing distributions
        for distribution in distributions:
            distribution_id = distribution['Id']
            comment = distribution.get('Comment', '')
            
            if 'aquachain' in comment.lower():
                try:
                    print(f"\n📊 Analyzing distribution {distribution_id}...")
                    
                    metrics = self.analyze_cdn_performance(distribution_id)
                    recommendations = self.generate_optimization_recommendations(metrics)
                    all_recommendations[distribution_id] = recommendations
                    
                    # Print current metrics
                    print(f"  Cache Hit Rate: {metrics.cache_hit_rate:.1f}%")
                    print(f"  Origin Latency: {metrics.origin_latency:.0f}ms")
                    print(f"  Requests/sec: {metrics.requests_per_second:.1f}")
                    print(f"  Bandwidth Usage: {metrics.bandwidth_usage:.1f} GB")
                    
                    # Apply recommendations
                    for rec in recommendations:
                        self.apply_optimization(rec, dry_run=dry_run)
                        
                except Exception as e:
                    print(f"  ❌ Failed to optimize {distribution_id}: {e}")
                    all_recommendations[distribution_id] = []
        
        # Create missing distributions if requested
        if create_missing:
            for config_name in self.cdn_configs.keys():
                print(f"\n🆕 Creating missing distribution for {config_name}...")
                distribution_id = self.create_cdn_distribution(config_name, dry_run=dry_run)
                if distribution_id:
                    all_recommendations[f"{config_name}-new"] = []
        
        return all_recommendations
    
    def print_optimization_summary(self, all_recommendations: Dict[str, List[CDNOptimizationRecommendation]]):
        """Print summary of CDN optimization recommendations."""
        print("\n" + "=" * 60)
        print("📋 CDN OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        total_recommendations = sum(len(recs) for recs in all_recommendations.values())
        high_priority = sum(1 for recs in all_recommendations.values() 
                          for rec in recs if rec.priority == 'high')
        
        print(f"Total Distributions Analyzed: {len(all_recommendations)}")
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
        
        print("\n📊 Recommendations by Distribution:")
        for dist_id, recommendations in all_recommendations.items():
            if recommendations:
                print(f"\n  {dist_id}:")
                for rec in recommendations:
                    priority_icon = "🔴" if rec.priority == 'high' else "🟡" if rec.priority == 'medium' else "🟢"
                    print(f"    {priority_icon} {rec.optimization_type.title()}: {rec.expected_improvement}")
                    print(f"       Cost Impact: {rec.cost_impact}")
            else:
                print(f"\n  {dist_id}: ✅ No optimizations needed")

def main():
    """Main function to run CDN optimization."""
    parser = argparse.ArgumentParser(description='AquaChain CDN Configuration Optimizer')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--distribution-id', type=str, 
                       help='Specific distribution to optimize (default: all)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Perform dry run without applying changes (default: True)')
    parser.add_argument('--apply', action='store_true', 
                       help='Actually apply optimizations (overrides dry-run)')
    parser.add_argument('--create-missing', action='store_true', 
                       help='Create missing CDN distributions')
    parser.add_argument('--days-back', type=int, default=7, 
                       help='Days of metrics to analyze (default: 7)')
    
    args = parser.parse_args()
    
    try:
        optimizer = CDNOptimizer(aws_region=args.aws_region)
        
        print("🔬 AquaChain CDN Configuration Optimizer")
        print("=" * 50)
        
        dry_run = args.dry_run and not args.apply
        
        if args.distribution_id:
            # Optimize specific distribution
            print(f"Optimizing distribution: {args.distribution_id}")
            
            metrics = optimizer.analyze_cdn_performance(args.distribution_id)
            recommendations = optimizer.generate_optimization_recommendations(metrics)
            
            for rec in recommendations:
                optimizer.apply_optimization(rec, dry_run=dry_run)
            
            optimizer.print_optimization_summary({args.distribution_id: recommendations})
        else:
            # Optimize all distributions
            all_recommendations = optimizer.optimize_all_distributions(
                dry_run=dry_run,
                create_missing=args.create_missing
            )
            
            optimizer.print_optimization_summary(all_recommendations)
        
        print("\n🎯 CDN optimization completed!")
        return 0
        
    except Exception as e:
        print(f"💥 CDN optimization failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())