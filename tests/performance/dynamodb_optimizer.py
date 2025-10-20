"""
DynamoDB Performance Optimizer for AquaChain
Optimizes DynamoDB read/write capacity and indexing strategies
"""

import boto3
import json
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
import argparse
from dataclasses import dataclass
import math

@dataclass
class DynamoDBMetrics:
    """Performance metrics for a DynamoDB table."""
    table_name: str
    read_capacity_utilization: float
    write_capacity_utilization: float
    throttled_reads: int
    throttled_writes: int
    consumed_read_capacity: float
    consumed_write_capacity: float
    provisioned_read_capacity: float
    provisioned_write_capacity: float
    item_count: int
    table_size_bytes: int
    avg_item_size: float
    hot_partitions: List[str]
    query_patterns: Dict[str, int]

@dataclass
class DynamoDBOptimizationRecommendation:
    """Optimization recommendation for DynamoDB table."""
    table_name: str
    optimization_type: str  # capacity, indexing, partitioning
    current_config: Dict
    recommended_config: Dict
    expected_improvement: str
    cost_impact: str
    priority: str

class DynamoDBOptimizer:
    """Optimizer for DynamoDB table performance."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.application_autoscaling = boto3.client('application-autoscaling', region_name=aws_region)
        
        # AquaChain DynamoDB tables
        self.aquachain_tables = [
            'aquachain-readings',
            'aquachain-ledger',
            'aquachain-users',
            'aquachain-service-requests',
            'aquachain-sequence'
        ]
    
    def analyze_table_performance(self, table_name: str, 
                                days_back: int = 7) -> DynamoDBMetrics:
        """Analyze performance metrics for a DynamoDB table."""
        print(f"📊 Analyzing performance for table {table_name}...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get table description
        try:
            table = self.dynamodb.Table(table_name)
            table_description = table.meta.client.describe_table(TableName=table_name)['Table']
            
            item_count = table_description.get('ItemCount', 0)
            table_size_bytes = table_description.get('TableSizeBytes', 0)
            avg_item_size = table_size_bytes / max(1, item_count)
            
            # Get billing mode and capacity
            billing_mode = table_description.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
            
            if billing_mode == 'PROVISIONED':
                provisioned_throughput = table_description.get('ProvisionedThroughput', {})
                provisioned_read_capacity = provisioned_throughput.get('ReadCapacityUnits', 0)
                provisioned_write_capacity = provisioned_throughput.get('WriteCapacityUnits', 0)
            else:
                provisioned_read_capacity = 0
                provisioned_write_capacity = 0
                
        except Exception as e:
            print(f"Warning: Could not get table description for {table_name}: {e}")
            item_count = 0
            table_size_bytes = 0
            avg_item_size = 0
            provisioned_read_capacity = 0
            provisioned_write_capacity = 0
        
        # Get CloudWatch metrics
        consumed_read_capacity = self._get_consumed_capacity_metrics(
            table_name, 'ConsumedReadCapacityUnits', start_time, end_time
        )
        consumed_write_capacity = self._get_consumed_capacity_metrics(
            table_name, 'ConsumedWriteCapacityUnits', start_time, end_time
        )
        
        throttled_reads = self._get_throttle_metrics(
            table_name, 'ReadThrottles', start_time, end_time
        )
        throttled_writes = self._get_throttle_metrics(
            table_name, 'WriteThrottles', start_time, end_time
        )
        
        # Calculate utilization rates
        if provisioned_read_capacity > 0:
            read_capacity_utilization = (consumed_read_capacity / provisioned_read_capacity) * 100
        else:
            read_capacity_utilization = 0
            
        if provisioned_write_capacity > 0:
            write_capacity_utilization = (consumed_write_capacity / provisioned_write_capacity) * 100
        else:
            write_capacity_utilization = 0
        
        # Analyze query patterns (simplified)
        query_patterns = self._analyze_query_patterns(table_name, start_time, end_time)
        
        # Identify hot partitions (simplified)
        hot_partitions = self._identify_hot_partitions(table_name)
        
        return DynamoDBMetrics(
            table_name=table_name,
            read_capacity_utilization=read_capacity_utilization,
            write_capacity_utilization=write_capacity_utilization,
            throttled_reads=throttled_reads,
            throttled_writes=throttled_writes,
            consumed_read_capacity=consumed_read_capacity,
            consumed_write_capacity=consumed_write_capacity,
            provisioned_read_capacity=provisioned_read_capacity,
            provisioned_write_capacity=provisioned_write_capacity,
            item_count=item_count,
            table_size_bytes=table_size_bytes,
            avg_item_size=avg_item_size,
            hot_partitions=hot_partitions,
            query_patterns=query_patterns
        )
    
    def _get_consumed_capacity_metrics(self, table_name: str, metric_name: str,
                                     start_time: datetime, end_time: datetime) -> float:
        """Get consumed capacity metrics from CloudWatch."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'TableName',
                        'Value': table_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                total_consumed = sum(dp['Sum'] for dp in datapoints)
                hours = len(datapoints)
                return total_consumed / max(1, hours)  # Average per hour
            
            return 0.0
            
        except Exception as e:
            print(f"Warning: Could not get {metric_name} metrics for {table_name}: {e}")
            return 0.0
    
    def _get_throttle_metrics(self, table_name: str, metric_name: str,
                            start_time: datetime, end_time: datetime) -> int:
        """Get throttle metrics from CloudWatch."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'TableName',
                        'Value': table_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            return sum(int(dp['Sum']) for dp in datapoints)
            
        except Exception as e:
            print(f"Warning: Could not get {metric_name} metrics for {table_name}: {e}")
            return 0
    
    def _analyze_query_patterns(self, table_name: str, 
                              start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """Analyze query patterns for the table."""
        # In a real implementation, this would analyze CloudTrail logs
        # or application logs to understand query patterns
        
        # Simplified pattern analysis based on table name
        patterns = {}
        
        if 'readings' in table_name:
            patterns = {
                'device_time_range_queries': 70,  # 70% of queries
                'device_latest_reading': 20,
                'admin_bulk_queries': 10
            }
        elif 'ledger' in table_name:
            patterns = {
                'sequential_reads': 60,
                'hash_verification_queries': 30,
                'audit_range_queries': 10
            }
        elif 'users' in table_name:
            patterns = {
                'user_profile_lookups': 80,
                'role_based_queries': 15,
                'admin_user_management': 5
            }
        elif 'service-requests' in table_name:
            patterns = {
                'technician_assignment_queries': 40,
                'consumer_status_checks': 35,
                'admin_reporting_queries': 25
            }
        
        return patterns
    
    def _identify_hot_partitions(self, table_name: str) -> List[str]:
        """Identify hot partitions in the table."""
        # In a real implementation, this would analyze partition metrics
        # For now, return potential hot partitions based on table design
        
        hot_partitions = []
        
        if 'readings' in table_name:
            # Time-windowed partitions might have hot spots
            current_month = datetime.now().strftime('%Y%m')
            hot_partitions = [f"device_month#{current_month}"]
        elif 'ledger' in table_name:
            # Global sequence table has single partition
            hot_partitions = ['GLOBAL_SEQUENCE']
        elif 'sequence' in table_name:
            # Sequence generator table
            hot_partitions = ['LEDGER']
        
        return hot_partitions
    
    def generate_optimization_recommendations(self, 
                                            metrics: DynamoDBMetrics) -> List[DynamoDBOptimizationRecommendation]:
        """Generate optimization recommendations based on performance metrics."""
        recommendations = []
        
        current_config = {
            'ProvisionedReadCapacity': metrics.provisioned_read_capacity,
            'ProvisionedWriteCapacity': metrics.provisioned_write_capacity,
            'BillingMode': 'PROVISIONED' if metrics.provisioned_read_capacity > 0 else 'PAY_PER_REQUEST'
        }
        
        # Capacity optimization recommendations
        if metrics.throttled_reads > 0 or metrics.read_capacity_utilization > 80:
            # Increase read capacity
            recommended_read_capacity = max(
                metrics.provisioned_read_capacity * 1.5,
                math.ceil(metrics.consumed_read_capacity * 1.2)
            )
            
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='capacity',
                current_config=current_config,
                recommended_config={'ProvisionedReadCapacity': recommended_read_capacity},
                expected_improvement=f"Eliminate read throttling, improve read performance by ~30%",
                cost_impact="Negative (cost increase)",
                priority="high"
            ))
        
        if metrics.throttled_writes > 0 or metrics.write_capacity_utilization > 80:
            # Increase write capacity
            recommended_write_capacity = max(
                metrics.provisioned_write_capacity * 1.5,
                math.ceil(metrics.consumed_write_capacity * 1.2)
            )
            
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='capacity',
                current_config=current_config,
                recommended_config={'ProvisionedWriteCapacity': recommended_write_capacity},
                expected_improvement=f"Eliminate write throttling, improve write performance by ~30%",
                cost_impact="Negative (cost increase)",
                priority="high"
            ))
        
        # Over-provisioning optimization
        if (metrics.read_capacity_utilization < 20 and 
            metrics.provisioned_read_capacity > 5 and 
            metrics.throttled_reads == 0):
            
            recommended_read_capacity = max(5, math.ceil(metrics.consumed_read_capacity * 1.5))
            
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='capacity',
                current_config=current_config,
                recommended_config={'ProvisionedReadCapacity': recommended_read_capacity},
                expected_improvement=f"Reduce costs by ~{(1 - recommended_read_capacity/metrics.provisioned_read_capacity)*100:.0f}%",
                cost_impact="Positive (cost reduction)",
                priority="medium"
            ))
        
        if (metrics.write_capacity_utilization < 20 and 
            metrics.provisioned_write_capacity > 5 and 
            metrics.throttled_writes == 0):
            
            recommended_write_capacity = max(5, math.ceil(metrics.consumed_write_capacity * 1.5))
            
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='capacity',
                current_config=current_config,
                recommended_config={'ProvisionedWriteCapacity': recommended_write_capacity},
                expected_improvement=f"Reduce costs by ~{(1 - recommended_write_capacity/metrics.provisioned_write_capacity)*100:.0f}%",
                cost_impact="Positive (cost reduction)",
                priority="medium"
            ))
        
        # Auto-scaling recommendation
        if (metrics.read_capacity_utilization > 70 or metrics.write_capacity_utilization > 70 or
            metrics.throttled_reads > 0 or metrics.throttled_writes > 0):
            
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='autoscaling',
                current_config=current_config,
                recommended_config={
                    'AutoScaling': {
                        'ReadCapacity': {'Min': 5, 'Max': metrics.provisioned_read_capacity * 2},
                        'WriteCapacity': {'Min': 5, 'Max': metrics.provisioned_write_capacity * 2}
                    }
                },
                expected_improvement="Automatic capacity adjustment based on demand",
                cost_impact="Neutral (optimized scaling)",
                priority="high"
            ))
        
        # Indexing recommendations
        if 'readings' in metrics.table_name and 'device_time_range_queries' in metrics.query_patterns:
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='indexing',
                current_config=current_config,
                recommended_config={
                    'GSI': {
                        'IndexName': 'DeviceTimestampIndex',
                        'Keys': {'PartitionKey': 'deviceId', 'SortKey': 'timestamp'}
                    }
                },
                expected_improvement="Improve device-specific queries by ~50%",
                cost_impact="Negative (storage and capacity costs)",
                priority="medium"
            ))
        
        # Hot partition recommendations
        if metrics.hot_partitions:
            recommendations.append(DynamoDBOptimizationRecommendation(
                table_name=metrics.table_name,
                optimization_type='partitioning',
                current_config=current_config,
                recommended_config={
                    'PartitionStrategy': 'Add random suffix or use composite keys'
                },
                expected_improvement="Distribute load across partitions, reduce hot spots",
                cost_impact="Neutral (design change)",
                priority="high" if metrics.throttled_reads > 0 or metrics.throttled_writes > 0 else "medium"
            ))
        
        return recommendations
    
    def apply_optimization(self, recommendation: DynamoDBOptimizationRecommendation, 
                          dry_run: bool = True) -> bool:
        """Apply optimization recommendation to DynamoDB table."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Applying optimization to {recommendation.table_name}")
        print(f"  Type: {recommendation.optimization_type}")
        print(f"  Recommended config: {recommendation.recommended_config}")
        print(f"  Expected improvement: {recommendation.expected_improvement}")
        
        if dry_run:
            print("  Skipping actual update (dry run mode)")
            return True
        
        try:
            if recommendation.optimization_type == 'capacity':
                # Update table capacity
                update_params = {}
                
                if 'ProvisionedReadCapacity' in recommendation.recommended_config:
                    update_params['ReadCapacityUnits'] = recommendation.recommended_config['ProvisionedReadCapacity']
                
                if 'ProvisionedWriteCapacity' in recommendation.recommended_config:
                    update_params['WriteCapacityUnits'] = recommendation.recommended_config['ProvisionedWriteCapacity']
                
                if update_params:
                    response = self.dynamodb_client.update_table(
                        TableName=recommendation.table_name,
                        ProvisionedThroughput=update_params
                    )
                    print(f"  ✅ Updated table capacity")
            
            elif recommendation.optimization_type == 'autoscaling':
                # Configure auto-scaling
                self._configure_autoscaling(
                    recommendation.table_name,
                    recommendation.recommended_config['AutoScaling']
                )
                print(f"  ✅ Configured auto-scaling")
            
            elif recommendation.optimization_type == 'indexing':
                # Create GSI (Global Secondary Index)
                gsi_config = recommendation.recommended_config['GSI']
                
                # Note: This is a simplified example
                # Real implementation would need to handle GSI creation properly
                print(f"  ⚠️  GSI creation requires careful planning and may take time")
                print(f"     Recommended GSI: {gsi_config}")
            
            elif recommendation.optimization_type == 'partitioning':
                # Partitioning changes require application-level changes
                print(f"  ⚠️  Partitioning optimization requires application code changes")
                print(f"     Strategy: {recommendation.recommended_config['PartitionStrategy']}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to apply optimization: {e}")
            return False
    
    def _configure_autoscaling(self, table_name: str, autoscaling_config: Dict):
        """Configure auto-scaling for DynamoDB table."""
        try:
            # Register scalable targets
            if 'ReadCapacity' in autoscaling_config:
                self.application_autoscaling.register_scalable_target(
                    ServiceNamespace='dynamodb',
                    ResourceId=f'table/{table_name}',
                    ScalableDimension='dynamodb:table:ReadCapacityUnits',
                    MinCapacity=autoscaling_config['ReadCapacity']['Min'],
                    MaxCapacity=autoscaling_config['ReadCapacity']['Max']
                )
                
                # Create scaling policy
                self.application_autoscaling.put_scaling_policy(
                    PolicyName=f'{table_name}-read-scaling-policy',
                    ServiceNamespace='dynamodb',
                    ResourceId=f'table/{table_name}',
                    ScalableDimension='dynamodb:table:ReadCapacityUnits',
                    PolicyType='TargetTrackingScaling',
                    TargetTrackingScalingPolicyConfiguration={
                        'TargetValue': 70.0,
                        'PredefinedMetricSpecification': {
                            'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
                        }
                    }
                )
            
            if 'WriteCapacity' in autoscaling_config:
                self.application_autoscaling.register_scalable_target(
                    ServiceNamespace='dynamodb',
                    ResourceId=f'table/{table_name}',
                    ScalableDimension='dynamodb:table:WriteCapacityUnits',
                    MinCapacity=autoscaling_config['WriteCapacity']['Min'],
                    MaxCapacity=autoscaling_config['WriteCapacity']['Max']
                )
                
                # Create scaling policy
                self.application_autoscaling.put_scaling_policy(
                    PolicyName=f'{table_name}-write-scaling-policy',
                    ServiceNamespace='dynamodb',
                    ResourceId=f'table/{table_name}',
                    ScalableDimension='dynamodb:table:WriteCapacityUnits',
                    PolicyType='TargetTrackingScaling',
                    TargetTrackingScalingPolicyConfiguration={
                        'TargetValue': 70.0,
                        'PredefinedMetricSpecification': {
                            'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
                        }
                    }
                )
                
        except Exception as e:
            print(f"Warning: Could not configure auto-scaling: {e}")
    
    def optimize_all_tables(self, dry_run: bool = True, 
                           apply_high_priority_only: bool = False) -> Dict[str, List[DynamoDBOptimizationRecommendation]]:
        """Optimize all AquaChain DynamoDB tables."""
        print("🚀 Optimizing all AquaChain DynamoDB tables")
        print("=" * 60)
        
        all_recommendations = {}
        
        for table_name in self.aquachain_tables:
            try:
                print(f"\n📊 Analyzing {table_name}...")
                
                # Analyze performance
                metrics = self.analyze_table_performance(table_name)
                
                # Generate recommendations
                recommendations = self.generate_optimization_recommendations(metrics)
                all_recommendations[table_name] = recommendations
                
                # Print current metrics
                print(f"  Item Count: {metrics.item_count:,}")
                print(f"  Table Size: {metrics.table_size_bytes / (1024*1024):.1f} MB")
                print(f"  Read Capacity Utilization: {metrics.read_capacity_utilization:.1f}%")
                print(f"  Write Capacity Utilization: {metrics.write_capacity_utilization:.1f}%")
                print(f"  Throttled Reads: {metrics.throttled_reads}")
                print(f"  Throttled Writes: {metrics.throttled_writes}")
                
                # Apply recommendations
                for rec in recommendations:
                    if apply_high_priority_only and rec.priority != 'high':
                        continue
                    
                    self.apply_optimization(rec, dry_run=dry_run)
                
            except Exception as e:
                print(f"  ❌ Failed to optimize {table_name}: {e}")
                all_recommendations[table_name] = []
        
        return all_recommendations
    
    def print_optimization_summary(self, all_recommendations: Dict[str, List[DynamoDBOptimizationRecommendation]]):
        """Print summary of optimization recommendations."""
        print("\n" + "=" * 60)
        print("📋 DYNAMODB OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        total_recommendations = sum(len(recs) for recs in all_recommendations.values())
        high_priority = sum(1 for recs in all_recommendations.values() 
                          for rec in recs if rec.priority == 'high')
        
        print(f"Total Tables Analyzed: {len(all_recommendations)}")
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
        
        print("\n📊 Recommendations by Table:")
        for table_name, recommendations in all_recommendations.items():
            if recommendations:
                print(f"\n  {table_name}:")
                for rec in recommendations:
                    priority_icon = "🔴" if rec.priority == 'high' else "🟡" if rec.priority == 'medium' else "🟢"
                    print(f"    {priority_icon} {rec.optimization_type.title()}: {rec.expected_improvement}")
                    print(f"       Cost Impact: {rec.cost_impact}")
            else:
                print(f"\n  {table_name}: ✅ No optimizations needed")

def main():
    """Main function to run DynamoDB optimization."""
    parser = argparse.ArgumentParser(description='AquaChain DynamoDB Performance Optimizer')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--table-name', type=str, 
                       help='Specific table to optimize (default: all)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Perform dry run without applying changes (default: True)')
    parser.add_argument('--apply', action='store_true', 
                       help='Actually apply optimizations (overrides dry-run)')
    parser.add_argument('--high-priority-only', action='store_true', 
                       help='Only apply high priority optimizations')
    parser.add_argument('--days-back', type=int, default=7, 
                       help='Days of metrics to analyze (default: 7)')
    
    args = parser.parse_args()
    
    try:
        optimizer = DynamoDBOptimizer(aws_region=args.aws_region)
        
        print("🔬 AquaChain DynamoDB Performance Optimizer")
        print("=" * 50)
        
        dry_run = args.dry_run and not args.apply
        
        if args.table_name:
            # Optimize specific table
            print(f"Optimizing table: {args.table_name}")
            
            metrics = optimizer.analyze_table_performance(
                args.table_name, days_back=args.days_back
            )
            recommendations = optimizer.generate_optimization_recommendations(metrics)
            
            for rec in recommendations:
                if args.high_priority_only and rec.priority != 'high':
                    continue
                optimizer.apply_optimization(rec, dry_run=dry_run)
            
            optimizer.print_optimization_summary({args.table_name: recommendations})
        else:
            # Optimize all tables
            all_recommendations = optimizer.optimize_all_tables(
                dry_run=dry_run,
                apply_high_priority_only=args.high_priority_only
            )
            
            optimizer.print_optimization_summary(all_recommendations)
        
        print("\n🎯 DynamoDB optimization completed!")
        return 0
        
    except Exception as e:
        print(f"💥 DynamoDB optimization failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())