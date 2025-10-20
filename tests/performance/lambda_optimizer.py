"""
Lambda Performance Optimizer for AquaChain
Optimizes Lambda function performance and reduces cold start times
"""

import boto3
import json
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
import argparse
from dataclasses import dataclass
import concurrent.futures

@dataclass
class LambdaPerformanceMetrics:
    """Performance metrics for a Lambda function."""
    function_name: str
    avg_duration: float
    p95_duration: float
    p99_duration: float
    cold_start_rate: float
    error_rate: float
    throttle_rate: float
    memory_utilization: float
    current_memory: int
    current_timeout: int
    invocations_per_minute: float

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation for a Lambda function."""
    function_name: str
    current_config: Dict
    recommended_config: Dict
    expected_improvement: str
    cost_impact: str
    priority: str  # high, medium, low

class LambdaOptimizer:
    """Optimizer for Lambda function performance."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.lambda_client = boto3.client('lambda', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.logs_client = boto3.client('logs', region_name=aws_region)
        
        # AquaChain Lambda functions
        self.aquachain_functions = [
            'AquaChain-data-processing',
            'AquaChain-ml-inference',
            'AquaChain-alert-detection',
            'AquaChain-notification-service',
            'AquaChain-user-management',
            'AquaChain-service-assignment',
            'AquaChain-audit-processor'
        ]
    
    def analyze_function_performance(self, function_name: str, 
                                   days_back: int = 7) -> LambdaPerformanceMetrics:
        """Analyze performance metrics for a Lambda function."""
        print(f"📊 Analyzing performance for {function_name}...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get function configuration
        try:
            function_config = self.lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            current_memory = function_config['MemorySize']
            current_timeout = function_config['Timeout']
        except Exception as e:
            print(f"Warning: Could not get function config for {function_name}: {e}")
            current_memory = 128
            current_timeout = 30
        
        # Get CloudWatch metrics
        metrics = {}
        
        # Duration metrics
        duration_stats = self._get_metric_statistics(
            'AWS/Lambda', 'Duration', function_name, start_time, end_time
        )
        
        # Invocation metrics
        invocation_stats = self._get_metric_statistics(
            'AWS/Lambda', 'Invocations', function_name, start_time, end_time
        )
        
        # Error metrics
        error_stats = self._get_metric_statistics(
            'AWS/Lambda', 'Errors', function_name, start_time, end_time
        )
        
        # Throttle metrics
        throttle_stats = self._get_metric_statistics(
            'AWS/Lambda', 'Throttles', function_name, start_time, end_time
        )
        
        # Calculate derived metrics
        durations = [dp['Average'] for dp in duration_stats]
        invocations = [dp['Sum'] for dp in invocation_stats]
        errors = [dp['Sum'] for dp in error_stats]
        throttles = [dp['Sum'] for dp in throttle_stats]
        
        avg_duration = statistics.mean(durations) if durations else 0
        p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else avg_duration
        p99_duration = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else avg_duration
        
        total_invocations = sum(invocations)
        total_errors = sum(errors)
        total_throttles = sum(throttles)
        
        error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0
        throttle_rate = (total_throttles / total_invocations * 100) if total_invocations > 0 else 0
        invocations_per_minute = total_invocations / (days_back * 24 * 60)
        
        # Estimate cold start rate (simplified)
        cold_start_rate = self._estimate_cold_start_rate(function_name, start_time, end_time)
        
        # Estimate memory utilization
        memory_utilization = self._estimate_memory_utilization(function_name, start_time, end_time)
        
        return LambdaPerformanceMetrics(
            function_name=function_name,
            avg_duration=avg_duration,
            p95_duration=p95_duration,
            p99_duration=p99_duration,
            cold_start_rate=cold_start_rate,
            error_rate=error_rate,
            throttle_rate=throttle_rate,
            memory_utilization=memory_utilization,
            current_memory=current_memory,
            current_timeout=current_timeout,
            invocations_per_minute=invocations_per_minute
        )
    
    def _get_metric_statistics(self, namespace: str, metric_name: str, 
                              function_name: str, start_time: datetime, 
                              end_time: datetime) -> List[Dict]:
        """Get CloudWatch metric statistics."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Average', 'Sum', 'Maximum']
            )
            return response.get('Datapoints', [])
        except Exception as e:
            print(f"Warning: Could not get {metric_name} metrics for {function_name}: {e}")
            return []
    
    def _estimate_cold_start_rate(self, function_name: str, 
                                 start_time: datetime, end_time: datetime) -> float:
        """Estimate cold start rate by analyzing CloudWatch logs."""
        try:
            log_group_name = f'/aws/lambda/{function_name}'
            
            # Query for INIT_START events (cold starts)
            query = """
            fields @timestamp, @message
            | filter @message like /INIT_START/
            | stats count() as cold_starts
            """
            
            response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query
            )
            
            query_id = response['queryId']
            
            # Wait for query to complete
            time.sleep(2)
            
            results = self.logs_client.get_query_results(queryId=query_id)
            
            if results['results']:
                cold_starts = float(results['results'][0][0]['value'])
                
                # Get total invocations for the same period
                invocation_stats = self._get_metric_statistics(
                    'AWS/Lambda', 'Invocations', function_name, start_time, end_time
                )
                total_invocations = sum(dp['Sum'] for dp in invocation_stats)
                
                if total_invocations > 0:
                    return (cold_starts / total_invocations) * 100
            
            return 0.0
            
        except Exception as e:
            print(f"Warning: Could not estimate cold start rate for {function_name}: {e}")
            return 0.0
    
    def _estimate_memory_utilization(self, function_name: str, 
                                   start_time: datetime, end_time: datetime) -> float:
        """Estimate memory utilization from CloudWatch logs."""
        try:
            log_group_name = f'/aws/lambda/{function_name}'
            
            # Query for memory usage in REPORT lines
            query = """
            fields @timestamp, @message
            | filter @message like /REPORT/
            | parse @message "Max Memory Used: * MB"
            | stats avg(@1) as avg_memory_used
            """
            
            response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query
            )
            
            query_id = response['queryId']
            
            # Wait for query to complete
            time.sleep(2)
            
            results = self.logs_client.get_query_results(queryId=query_id)
            
            if results['results'] and results['results'][0]:
                avg_memory_used = float(results['results'][0][0]['value'])
                
                # Get current memory allocation
                function_config = self.lambda_client.get_function_configuration(
                    FunctionName=function_name
                )
                allocated_memory = function_config['MemorySize']
                
                return (avg_memory_used / allocated_memory) * 100
            
            return 50.0  # Default estimate
            
        except Exception as e:
            print(f"Warning: Could not estimate memory utilization for {function_name}: {e}")
            return 50.0
    
    def generate_optimization_recommendations(self, 
                                            metrics: LambdaPerformanceMetrics) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on performance metrics."""
        recommendations = []
        
        current_config = {
            'MemorySize': metrics.current_memory,
            'Timeout': metrics.current_timeout
        }
        
        # Memory optimization
        if metrics.memory_utilization < 30:
            # Over-provisioned memory
            recommended_memory = max(128, int(metrics.current_memory * 0.7))
            recommendations.append(OptimizationRecommendation(
                function_name=metrics.function_name,
                current_config=current_config,
                recommended_config={'MemorySize': recommended_memory},
                expected_improvement="Reduce cost by ~30% with minimal performance impact",
                cost_impact="Positive (cost reduction)",
                priority="medium"
            ))
        elif metrics.memory_utilization > 80:
            # Under-provisioned memory
            recommended_memory = min(3008, int(metrics.current_memory * 1.5))
            recommendations.append(OptimizationRecommendation(
                function_name=metrics.function_name,
                current_config=current_config,
                recommended_config={'MemorySize': recommended_memory},
                expected_improvement="Improve performance by ~20-40%",
                cost_impact="Negative (cost increase)",
                priority="high"
            ))
        
        # Cold start optimization
        if metrics.cold_start_rate > 10 and metrics.invocations_per_minute > 5:
            recommendations.append(OptimizationRecommendation(
                function_name=metrics.function_name,
                current_config=current_config,
                recommended_config={'ProvisionedConcurrency': 2},
                expected_improvement="Reduce cold starts by ~90%",
                cost_impact="Negative (cost increase)",
                priority="high"
            ))
        
        # Timeout optimization
        if metrics.p99_duration < (metrics.current_timeout * 1000 * 0.5):
            # Timeout is too high
            recommended_timeout = max(30, int(metrics.p99_duration / 1000 * 2))
            recommendations.append(OptimizationRecommendation(
                function_name=metrics.function_name,
                current_config=current_config,
                recommended_config={'Timeout': recommended_timeout},
                expected_improvement="Faster failure detection and recovery",
                cost_impact="Neutral",
                priority="low"
            ))
        
        # Performance optimization for high-latency functions
        if metrics.p95_duration > 5000:  # 5 seconds
            recommendations.append(OptimizationRecommendation(
                function_name=metrics.function_name,
                current_config=current_config,
                recommended_config={'MemorySize': min(3008, metrics.current_memory * 2)},
                expected_improvement="Reduce latency by ~30-50%",
                cost_impact="Negative (cost increase)",
                priority="high"
            ))
        
        return recommendations
    
    def apply_optimization(self, recommendation: OptimizationRecommendation, 
                          dry_run: bool = True) -> bool:
        """Apply optimization recommendation to Lambda function."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Applying optimization to {recommendation.function_name}")
        print(f"  Recommended config: {recommendation.recommended_config}")
        print(f"  Expected improvement: {recommendation.expected_improvement}")
        
        if dry_run:
            print("  Skipping actual update (dry run mode)")
            return True
        
        try:
            # Apply configuration updates
            update_config = {}
            
            if 'MemorySize' in recommendation.recommended_config:
                update_config['MemorySize'] = recommendation.recommended_config['MemorySize']
            
            if 'Timeout' in recommendation.recommended_config:
                update_config['Timeout'] = recommendation.recommended_config['Timeout']
            
            if update_config:
                response = self.lambda_client.update_function_configuration(
                    FunctionName=recommendation.function_name,
                    **update_config
                )
                print(f"  ✅ Updated function configuration")
            
            # Handle provisioned concurrency separately
            if 'ProvisionedConcurrency' in recommendation.recommended_config:
                try:
                    self.lambda_client.put_provisioned_concurrency_config(
                        FunctionName=recommendation.function_name,
                        Qualifier='$LATEST',
                        ProvisionedConcurrencyUnits=recommendation.recommended_config['ProvisionedConcurrency']
                    )
                    print(f"  ✅ Configured provisioned concurrency")
                except Exception as e:
                    print(f"  ⚠️  Could not configure provisioned concurrency: {e}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to apply optimization: {e}")
            return False
    
    def optimize_all_functions(self, dry_run: bool = True, 
                             apply_high_priority_only: bool = False) -> Dict[str, List[OptimizationRecommendation]]:
        """Optimize all AquaChain Lambda functions."""
        print("🚀 Optimizing all AquaChain Lambda functions")
        print("=" * 60)
        
        all_recommendations = {}
        
        for function_name in self.aquachain_functions:
            try:
                print(f"\n📊 Analyzing {function_name}...")
                
                # Analyze performance
                metrics = self.analyze_function_performance(function_name)
                
                # Generate recommendations
                recommendations = self.generate_optimization_recommendations(metrics)
                all_recommendations[function_name] = recommendations
                
                # Print current metrics
                print(f"  Current Memory: {metrics.current_memory} MB")
                print(f"  Memory Utilization: {metrics.memory_utilization:.1f}%")
                print(f"  Avg Duration: {metrics.avg_duration:.0f}ms")
                print(f"  P95 Duration: {metrics.p95_duration:.0f}ms")
                print(f"  Cold Start Rate: {metrics.cold_start_rate:.1f}%")
                print(f"  Error Rate: {metrics.error_rate:.2f}%")
                
                # Apply recommendations
                for rec in recommendations:
                    if apply_high_priority_only and rec.priority != 'high':
                        continue
                    
                    self.apply_optimization(rec, dry_run=dry_run)
                
            except Exception as e:
                print(f"  ❌ Failed to optimize {function_name}: {e}")
                all_recommendations[function_name] = []
        
        return all_recommendations
    
    def create_lambda_layers(self, dry_run: bool = True):
        """Create optimized Lambda layers for common dependencies."""
        print("📦 Creating optimized Lambda layers...")
        
        # Common layer configurations
        layers = [
            {
                'name': 'aquachain-common-layer',
                'description': 'Common utilities and shared code for AquaChain functions',
                'compatible_runtimes': ['python3.11'],
                'dependencies': ['boto3', 'botocore', 'requests', 'json-logging']
            },
            {
                'name': 'aquachain-ml-layer',
                'description': 'ML libraries for AquaChain inference functions',
                'compatible_runtimes': ['python3.11'],
                'dependencies': ['scikit-learn', 'numpy', 'pandas', 'joblib']
            },
            {
                'name': 'aquachain-crypto-layer',
                'description': 'Cryptographic libraries for ledger operations',
                'compatible_runtimes': ['python3.11'],
                'dependencies': ['cryptography', 'hashlib', 'hmac']
            }
        ]
        
        for layer_config in layers:
            print(f"  Creating layer: {layer_config['name']}")
            
            if dry_run:
                print(f"    [DRY RUN] Would create layer with dependencies: {layer_config['dependencies']}")
                continue
            
            try:
                # In a real implementation, this would:
                # 1. Create a deployment package with the dependencies
                # 2. Upload to Lambda as a layer
                # 3. Update functions to use the layer
                
                print(f"    ✅ Layer {layer_config['name']} created (simulated)")
                
            except Exception as e:
                print(f"    ❌ Failed to create layer {layer_config['name']}: {e}")
    
    def print_optimization_summary(self, all_recommendations: Dict[str, List[OptimizationRecommendation]]):
        """Print summary of optimization recommendations."""
        print("\n" + "=" * 60)
        print("📋 OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        total_recommendations = sum(len(recs) for recs in all_recommendations.values())
        high_priority = sum(1 for recs in all_recommendations.values() 
                          for rec in recs if rec.priority == 'high')
        
        print(f"Total Functions Analyzed: {len(all_recommendations)}")
        print(f"Total Recommendations: {total_recommendations}")
        print(f"High Priority Recommendations: {high_priority}")
        
        print("\n📊 Recommendations by Function:")
        for function_name, recommendations in all_recommendations.items():
            if recommendations:
                print(f"\n  {function_name}:")
                for rec in recommendations:
                    priority_icon = "🔴" if rec.priority == 'high' else "🟡" if rec.priority == 'medium' else "🟢"
                    print(f"    {priority_icon} {rec.expected_improvement}")
                    print(f"       Config: {rec.recommended_config}")
                    print(f"       Cost Impact: {rec.cost_impact}")
            else:
                print(f"\n  {function_name}: ✅ No optimizations needed")

def main():
    """Main function to run Lambda optimization."""
    parser = argparse.ArgumentParser(description='AquaChain Lambda Performance Optimizer')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--function-name', type=str, 
                       help='Specific function to optimize (default: all)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Perform dry run without applying changes (default: True)')
    parser.add_argument('--apply', action='store_true', 
                       help='Actually apply optimizations (overrides dry-run)')
    parser.add_argument('--high-priority-only', action='store_true', 
                       help='Only apply high priority optimizations')
    parser.add_argument('--create-layers', action='store_true', 
                       help='Create optimized Lambda layers')
    parser.add_argument('--days-back', type=int, default=7, 
                       help='Days of metrics to analyze (default: 7)')
    
    args = parser.parse_args()
    
    try:
        optimizer = LambdaOptimizer(aws_region=args.aws_region)
        
        print("🔬 AquaChain Lambda Performance Optimizer")
        print("=" * 50)
        
        dry_run = args.dry_run and not args.apply
        
        if args.function_name:
            # Optimize specific function
            print(f"Optimizing function: {args.function_name}")
            
            metrics = optimizer.analyze_function_performance(
                args.function_name, days_back=args.days_back
            )
            recommendations = optimizer.generate_optimization_recommendations(metrics)
            
            for rec in recommendations:
                if args.high_priority_only and rec.priority != 'high':
                    continue
                optimizer.apply_optimization(rec, dry_run=dry_run)
            
            optimizer.print_optimization_summary({args.function_name: recommendations})
        else:
            # Optimize all functions
            all_recommendations = optimizer.optimize_all_functions(
                dry_run=dry_run,
                apply_high_priority_only=args.high_priority_only
            )
            
            optimizer.print_optimization_summary(all_recommendations)
        
        # Create layers if requested
        if args.create_layers:
            optimizer.create_lambda_layers(dry_run=dry_run)
        
        print("\n🎯 Lambda optimization completed!")
        return 0
        
    except Exception as e:
        print(f"💥 Lambda optimization failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())