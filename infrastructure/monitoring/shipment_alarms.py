"""
CloudWatch alarms for shipment tracking monitoring

This module creates CloudWatch alarms for monitoring shipment operations:
- Failed delivery rate > 5%
- Webhook errors > 10 per 5 minutes
- Stale shipments > 10
- Lambda errors

Requirements: 14.3, 14.4
"""
import boto3
import os
from typing import List, Dict, Any

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('ALARM_SNS_TOPIC_ARN', '')
NAMESPACE = 'AquaChain/Shipments'


def create_all_alarms(sns_topic_arn: str = None) -> List[str]:
    """
    Create all CloudWatch alarms for shipment monitoring
    
    Args:
        sns_topic_arn: SNS topic ARN for alarm notifications
        
    Returns:
        List of created alarm names
    """
    if not sns_topic_arn:
        sns_topic_arn = SNS_TOPIC_ARN
    
    if not sns_topic_arn:
        print("WARNING: No SNS topic ARN provided, alarms will be created without notifications")
    
    alarm_names = []
    
    # Create failed delivery rate alarm
    alarm_names.append(create_failed_delivery_rate_alarm(sns_topic_arn))
    
    # Create webhook errors alarm
    alarm_names.append(create_webhook_errors_alarm(sns_topic_arn))
    
    # Create stale shipments alarm
    alarm_names.append(create_stale_shipments_alarm(sns_topic_arn))
    
    # Create Lambda errors alarms
    alarm_names.extend(create_lambda_errors_alarms(sns_topic_arn))
    
    print(f"Created {len(alarm_names)} CloudWatch alarms")
    return alarm_names


def create_failed_delivery_rate_alarm(sns_topic_arn: str) -> str:
    """
    Create alarm for failed delivery rate > 5%
    
    Monitors the ratio of FailedDeliveries to ShipmentsCreated.
    Triggers when the rate exceeds 5% over a 1-hour period.
    
    Requirements: 14.3
    
    Args:
        sns_topic_arn: SNS topic ARN for notifications
        
    Returns:
        Alarm name
    """
    alarm_name = 'AquaChain-Shipments-HighFailedDeliveryRate'
    
    try:
        # Create alarm using metric math
        # Rate = (FailedDeliveries / ShipmentsCreated) * 100
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription='Alert when failed delivery rate exceeds 5% over 1 hour',
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            MetricName=None,  # Using metric math instead
            Metrics=[
                {
                    'Id': 'failed',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': NAMESPACE,
                            'MetricName': 'FailedDeliveries'
                        },
                        'Period': 3600,  # 1 hour
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'created',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': NAMESPACE,
                            'MetricName': 'ShipmentsCreated'
                        },
                        'Period': 3600,  # 1 hour
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'rate',
                    'Expression': '(failed / created) * 100',
                    'Label': 'Failed Delivery Rate (%)',
                    'ReturnData': True
                }
            ],
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=5.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        
        print(f"Created alarm: {alarm_name}")
        return alarm_name
        
    except Exception as e:
        print(f"ERROR: Failed to create alarm {alarm_name}: {str(e)}")
        raise


def create_webhook_errors_alarm(sns_topic_arn: str) -> str:
    """
    Create alarm for webhook errors > 10 per 5 minutes
    
    Monitors WebhookErrors metric.
    Triggers when errors exceed 10 in a 5-minute period.
    
    Requirements: 14.4
    
    Args:
        sns_topic_arn: SNS topic ARN for notifications
        
    Returns:
        Alarm name
    """
    alarm_name = 'AquaChain-Shipments-HighWebhookErrors'
    
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription='Alert when webhook errors exceed 10 per 5 minutes',
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            MetricName='WebhookErrors',
            Namespace=NAMESPACE,
            Statistic='Sum',
            Period=300,  # 5 minutes
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=10.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        
        print(f"Created alarm: {alarm_name}")
        return alarm_name
        
    except Exception as e:
        print(f"ERROR: Failed to create alarm {alarm_name}: {str(e)}")
        raise


def create_stale_shipments_alarm(sns_topic_arn: str) -> str:
    """
    Create alarm for stale shipments > 10
    
    Monitors StaleShipments metric.
    Triggers when count exceeds 10.
    
    Requirements: 14.3
    
    Args:
        sns_topic_arn: SNS topic ARN for notifications
        
    Returns:
        Alarm name
    """
    alarm_name = 'AquaChain-Shipments-HighStaleShipments'
    
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription='Alert when stale shipments exceed 10',
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
            MetricName='StaleShipments',
            Namespace=NAMESPACE,
            Statistic='Maximum',
            Period=3600,  # 1 hour
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=10.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        
        print(f"Created alarm: {alarm_name}")
        return alarm_name
        
    except Exception as e:
        print(f"ERROR: Failed to create alarm {alarm_name}: {str(e)}")
        raise


def create_lambda_errors_alarms(sns_topic_arn: str) -> List[str]:
    """
    Create alarms for Lambda function errors
    
    Creates separate alarms for each Lambda function:
    - create_shipment
    - webhook_handler
    - get_shipment_status
    - polling_fallback
    - stale_shipment_detector
    
    Requirements: 14.4
    
    Args:
        sns_topic_arn: SNS topic ARN for notifications
        
    Returns:
        List of alarm names
    """
    lambda_functions = [
        'create_shipment',
        'webhook_handler',
        'get_shipment_status',
        'polling_fallback',
        'stale_shipment_detector'
    ]
    
    alarm_names = []
    
    for function_name in lambda_functions:
        alarm_name = f'AquaChain-Shipments-{function_name}-Errors'
        
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                AlarmDescription=f'Alert when {function_name} Lambda function has errors',
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn] if sns_topic_arn else [],
                MetricName='LambdaErrors',
                Namespace=NAMESPACE,
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                Statistic='Sum',
                Period=300,  # 5 minutes
                EvaluationPeriods=1,
                DatapointsToAlarm=1,
                Threshold=5.0,
                ComparisonOperator='GreaterThanThreshold',
                TreatMissingData='notBreaching'
            )
            
            print(f"Created alarm: {alarm_name}")
            alarm_names.append(alarm_name)
            
        except Exception as e:
            print(f"ERROR: Failed to create alarm {alarm_name}: {str(e)}")
            # Continue with other alarms
            continue
    
    return alarm_names


def delete_all_alarms() -> None:
    """
    Delete all shipment tracking alarms
    
    Useful for cleanup or redeployment.
    """
    alarm_prefix = 'AquaChain-Shipments-'
    
    try:
        # List all alarms with prefix
        response = cloudwatch.describe_alarms(
            AlarmNamePrefix=alarm_prefix
        )
        
        alarm_names = [alarm['AlarmName'] for alarm in response.get('MetricAlarms', [])]
        
        if not alarm_names:
            print("No alarms found to delete")
            return
        
        # Delete alarms
        cloudwatch.delete_alarms(AlarmNames=alarm_names)
        
        print(f"Deleted {len(alarm_names)} alarms: {', '.join(alarm_names)}")
        
    except Exception as e:
        print(f"ERROR: Failed to delete alarms: {str(e)}")
        raise


def create_sns_topic_for_alarms() -> str:
    """
    Create SNS topic for alarm notifications
    
    Returns:
        SNS topic ARN
    """
    topic_name = 'AquaChain-Shipments-Alarms'
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        
        print(f"Created SNS topic: {topic_arn}")
        return topic_arn
        
    except Exception as e:
        print(f"ERROR: Failed to create SNS topic: {str(e)}")
        raise


def subscribe_email_to_alarms(topic_arn: str, email: str) -> str:
    """
    Subscribe email address to alarm notifications
    
    Args:
        topic_arn: SNS topic ARN
        email: Email address to subscribe
        
    Returns:
        Subscription ARN
    """
    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        
        subscription_arn = response['SubscriptionArn']
        
        print(f"Subscribed {email} to alarm notifications")
        print(f"Subscription ARN: {subscription_arn}")
        print("NOTE: Email confirmation required - check inbox")
        
        return subscription_arn
        
    except Exception as e:
        print(f"ERROR: Failed to subscribe email: {str(e)}")
        raise


if __name__ == '__main__':
    """
    Setup script for CloudWatch alarms
    
    Usage:
        python shipment_alarms.py
    """
    import sys
    
    print("Setting up CloudWatch alarms for shipment tracking...")
    
    # Create SNS topic for alarms
    topic_arn = create_sns_topic_for_alarms()
    
    # Subscribe email if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        subscribe_email_to_alarms(topic_arn, email)
    
    # Create all alarms
    alarm_names = create_all_alarms(topic_arn)
    
    print("\n" + "="*60)
    print("CloudWatch Alarms Setup Complete!")
    print("="*60)
    print(f"\nSNS Topic ARN: {topic_arn}")
    print(f"\nCreated {len(alarm_names)} alarms:")
    for name in alarm_names:
        print(f"  - {name}")
    print("\nAlarms are now monitoring shipment operations.")
    print("You will receive notifications when thresholds are exceeded.")
