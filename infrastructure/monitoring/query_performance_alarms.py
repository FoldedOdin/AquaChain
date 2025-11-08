"""
Setup CloudWatch alarms for DynamoDB query performance monitoring (Phase 4)
Creates alarms for slow queries and GSI performance
"""

import boto3
import os
from typing import List, Dict

cloudwatch = boto3.client('cloudwatch')


class QueryPerformanceAlarmSetup:
    """
    Setup CloudWatch alarms for query performance monitoring
    """
    
    def __init__(self, sns_topic_arn: str, namespace: str = 'AquaChain/DynamoDB'):
        self.sns_topic_arn = sns_topic_arn
        self.namespace = namespace
    
    def create_query_duration_alarms(self):
        """
        Create alarms for query duration across all operations
        """
        operations = [
            'query_devices_by_user',
            'query_devices_by_status',
            'query_readings_by_device_and_metric',
            'query_readings_by_alert_level',
            'query_user_by_email',
            'query_users_by_organization_and_role'
        ]
        
        for operation in operations:
            alarm_name = f'AquaChain-SlowQuery-{operation}'
            
            try:
                cloudwatch.put_metric_alarm(
                    AlarmName=alarm_name,
                    ComparisonOperator='GreaterThanThreshold',
                    EvaluationPeriods=2,
                    MetricName='QueryDuration',
                    Namespace=self.namespace,
                    Period=300,  # 5 minutes
                    Statistic='Average',
                    Threshold=500.0,  # 500ms threshold
                    ActionsEnabled=True,
                    AlarmActions=[self.sns_topic_arn],
                    AlarmDescription=f'Alert when {operation} average duration exceeds 500ms',
                    Dimensions=[
                        {'Name': 'Operation', 'Value': operation}
                    ],
                    TreatMissingData='notBreaching',
                    Tags=[
                        {'Key': 'Project', 'Value': 'AquaChain'},
                        {'Key': 'Component', 'Value': 'QueryPerformance'},
                        {'Key': 'Phase', 'Value': 'Phase4'}
                    ]
                )
                
                print(f"✓ Created alarm: {alarm_name}")
                
            except Exception as e:
                print(f"✗ Failed to create alarm {alarm_name}: {e}")
    
    def create_slow_query_count_alarms(self):
        """
        Create alarms for slow query count (queries exceeding threshold)
        """
        alarm_name = 'AquaChain-SlowQueryCount-High'
        
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='SlowQueryCount',
                Namespace=self.namespace,
                Period=300,  # 5 minutes
                Statistic='Sum',
                Threshold=10.0,  # More than 10 slow queries in 5 minutes
                ActionsEnabled=True,
                AlarmActions=[self.sns_topic_arn],
                AlarmDescription='Alert when slow query count exceeds 10 in 5 minutes',
                TreatMissingData='notBreaching',
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'QueryPerformance'},
                    {'Key': 'Phase', 'Value': 'Phase4'}
                ]
            )
            
            print(f"✓ Created alarm: {alarm_name}")
            
        except Exception as e:
            print(f"✗ Failed to create alarm {alarm_name}: {e}")
    
    def create_gsi_throttling_alarms(self):
        """
        Create alarms for GSI read throttling
        """
        gsi_configs = [
            ('aquachain-devices', 'user_id-created_at-index'),
            ('aquachain-devices', 'status-last_seen-index'),
            ('aquachain-readings', 'device_id-metric_type-index'),
            ('aquachain-readings', 'alert_level-timestamp-index'),
            ('aquachain-users', 'email-index'),
            ('aquachain-users', 'organization_id-role-index')
        ]
        
        for table_name, index_name in gsi_configs:
            alarm_name = f'AquaChain-GSI-Throttle-{table_name}-{index_name}'
            
            try:
                cloudwatch.put_metric_alarm(
                    AlarmName=alarm_name,
                    ComparisonOperator='GreaterThanThreshold',
                    EvaluationPeriods=2,
                    MetricName='ReadThrottleEvents',
                    Namespace='AWS/DynamoDB',
                    Period=300,  # 5 minutes
                    Statistic='Sum',
                    Threshold=5.0,  # More than 5 throttle events
                    ActionsEnabled=True,
                    AlarmActions=[self.sns_topic_arn],
                    AlarmDescription=f'Alert when GSI {index_name} experiences read throttling',
                    Dimensions=[
                        {'Name': 'TableName', 'Value': table_name},
                        {'Name': 'GlobalSecondaryIndexName', 'Value': index_name}
                    ],
                    TreatMissingData='notBreaching',
                    Tags=[
                        {'Key': 'Project', 'Value': 'AquaChain'},
                        {'Key': 'Component', 'Value': 'GSIPerformance'},
                        {'Key': 'Phase', 'Value': 'Phase4'}
                    ]
                )
                
                print(f"✓ Created alarm: {alarm_name}")
                
            except Exception as e:
                print(f"✗ Failed to create alarm {alarm_name}: {e}")
    
    def create_dashboard(self):
        """
        Create CloudWatch dashboard for query performance monitoring
        """
        dashboard_name = 'AquaChain-Query-Performance'
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            [self.namespace, "QueryDuration", {"stat": "Average"}],
                            ["...", {"stat": "Maximum"}],
                            ["...", {"stat": "p99"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": os.environ.get('AWS_REGION', 'us-east-1'),
                        "title": "Query Duration (All Operations)",
                        "yAxis": {
                            "left": {
                                "label": "Milliseconds"
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            [self.namespace, "SlowQueryCount", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": os.environ.get('AWS_REGION', 'us-east-1'),
                        "title": "Slow Query Count (>500ms)",
                        "yAxis": {
                            "left": {
                                "label": "Count"
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            [self.namespace, "ItemCount", {"stat": "Average"}],
                            ["...", {"stat": "Maximum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": os.environ.get('AWS_REGION', 'us-east-1'),
                        "title": "Items Returned per Query",
                        "yAxis": {
                            "left": {
                                "label": "Count"
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", 
                             {"dimensions": {"TableName": "aquachain-devices"}, "stat": "Sum"}],
                            ["...", {"dimensions": {"TableName": "aquachain-readings"}}],
                            ["...", {"dimensions": {"TableName": "aquachain-users"}}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": os.environ.get('AWS_REGION', 'us-east-1'),
                        "title": "DynamoDB Read Capacity Units",
                        "yAxis": {
                            "left": {
                                "label": "RCUs"
                            }
                        }
                    }
                }
            ]
        }
        
        try:
            cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=str(dashboard_body).replace("'", '"')
            )
            
            print(f"✓ Created dashboard: {dashboard_name}")
            
        except Exception as e:
            print(f"✗ Failed to create dashboard: {e}")
    
    def setup_all(self):
        """
        Setup all alarms and dashboard
        """
        print("Setting up query performance monitoring...")
        print("\n1. Creating query duration alarms...")
        self.create_query_duration_alarms()
        
        print("\n2. Creating slow query count alarms...")
        self.create_slow_query_count_alarms()
        
        print("\n3. Creating GSI throttling alarms...")
        self.create_gsi_throttling_alarms()
        
        print("\n4. Creating CloudWatch dashboard...")
        self.create_dashboard()
        
        print("\n✓ Query performance monitoring setup complete!")


def main():
    """
    Main function to setup query performance monitoring
    """
    # Get SNS topic ARN from environment or use default
    sns_topic_arn = os.environ.get('ALERT_TOPIC_ARN')
    
    if not sns_topic_arn:
        print("Error: ALERT_TOPIC_ARN environment variable not set")
        print("Please set it to your SNS topic ARN for alerts")
        return
    
    setup = QueryPerformanceAlarmSetup(sns_topic_arn)
    setup.setup_all()


if __name__ == '__main__':
    main()
