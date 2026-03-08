#!/usr/bin/env python3
"""
Create CloudWatch alarms for ledger table unauthorized modifications
"""

import boto3
import json

def create_ledger_alarms():
    cloudwatch = boto3.client('cloudwatch', region_name='ap-south-1')
    sns = boto3.client('sns', region_name='ap-south-1')
    
    print("=" * 70)
    print("CREATING LEDGER SECURITY ALARMS")
    print("=" * 70)
    print()
    
    # Get or create SNS topic for security alerts
    topic_name = 'aquachain-ledger-security-alerts'
    
    try:
        # Try to create SNS topic (idempotent)
        topic_response = sns.create_topic(Name=topic_name)
        topic_arn = topic_response['TopicArn']
        print(f"✓ SNS Topic: {topic_arn}")
        print()
    except Exception as e:
        print(f"❌ Error creating SNS topic: {e}")
        return False
    
    alarms_created = []
    
    # Alarm 1: Unauthorized Update Attempts
    alarm1_name = 'aquachain-ledger-unauthorized-updates'
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm1_name,
            AlarmDescription='Alert when UpdateItem is attempted on ledger table',
            ActionsEnabled=True,
            AlarmActions=[topic_arn],
            MetricName='UserErrors',
            Namespace='AWS/DynamoDB',
            Statistic='Sum',
            Dimensions=[
                {
                    'Name': 'TableName',
                    'Value': 'aquachain-ledger'
                },
                {
                    'Name': 'Operation',
                    'Value': 'UpdateItem'
                }
            ],
            Period=60,  # 1 minute
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='notBreaching'
        )
        alarms_created.append(alarm1_name)
        print(f"✓ Created alarm: {alarm1_name}")
    except Exception as e:
        print(f"⚠️  Error creating alarm '{alarm1_name}': {e}")
    
    # Alarm 2: Unauthorized Delete Attempts
    alarm2_name = 'aquachain-ledger-unauthorized-deletes'
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm2_name,
            AlarmDescription='Alert when DeleteItem is attempted on ledger table',
            ActionsEnabled=True,
            AlarmActions=[topic_arn],
            MetricName='UserErrors',
            Namespace='AWS/DynamoDB',
            Statistic='Sum',
            Dimensions=[
                {
                    'Name': 'TableName',
                    'Value': 'aquachain-ledger'
                },
                {
                    'Name': 'Operation',
                    'Value': 'DeleteItem'
                }
            ],
            Period=60,  # 1 minute
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='notBreaching'
        )
        alarms_created.append(alarm2_name)
        print(f"✓ Created alarm: {alarm2_name}")
    except Exception as e:
        print(f"⚠️  Error creating alarm '{alarm2_name}': {e}")
    
    # Alarm 3: Batch Write Attempts (can include deletes)
    alarm3_name = 'aquachain-ledger-batch-write-attempts'
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm3_name,
            AlarmDescription='Alert when BatchWriteItem is attempted on ledger table',
            ActionsEnabled=True,
            AlarmActions=[topic_arn],
            MetricName='UserErrors',
            Namespace='AWS/DynamoDB',
            Statistic='Sum',
            Dimensions=[
                {
                    'Name': 'TableName',
                    'Value': 'aquachain-ledger'
                },
                {
                    'Name': 'Operation',
                    'Value': 'BatchWriteItem'
                }
            ],
            Period=60,  # 1 minute
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='notBreaching'
        )
        alarms_created.append(alarm3_name)
        print(f"✓ Created alarm: {alarm3_name}")
    except Exception as e:
        print(f"⚠️  Error creating alarm '{alarm3_name}': {e}")
    
    # Alarm 4: High Error Rate (general security indicator)
    alarm4_name = 'aquachain-ledger-high-error-rate'
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm4_name,
            AlarmDescription='Alert when ledger table has high error rate',
            ActionsEnabled=True,
            AlarmActions=[topic_arn],
            MetricName='UserErrors',
            Namespace='AWS/DynamoDB',
            Statistic='Sum',
            Dimensions=[
                {
                    'Name': 'TableName',
                    'Value': 'aquachain-ledger'
                }
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=1,
            Threshold=10.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='notBreaching'
        )
        alarms_created.append(alarm4_name)
        print(f"✓ Created alarm: {alarm4_name}")
    except Exception as e:
        print(f"⚠️  Error creating alarm '{alarm4_name}': {e}")
    
    print()
    print("=" * 70)
    print(f"SUCCESS - Created {len(alarms_created)} alarms")
    print("=" * 70)
    print()
    print("Alarms Created:")
    for alarm in alarms_created:
        print(f"  • {alarm}")
    print()
    print(f"SNS Topic: {topic_arn}")
    print()
    print("Next Steps:")
    print("  1. Subscribe to SNS topic for email notifications:")
    print(f"     aws sns subscribe --topic-arn {topic_arn} \\")
    print(f"       --protocol email --notification-endpoint your-email@example.com")
    print()
    print("  2. Test alarms (optional):")
    print("     aws cloudwatch set-alarm-state --alarm-name aquachain-ledger-unauthorized-updates \\")
    print("       --state-value ALARM --state-reason 'Testing alarm'")
    print()
    
    return True

if __name__ == "__main__":
    success = create_ledger_alarms()
    exit(0 if success else 1)
