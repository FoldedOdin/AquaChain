"""
Complete setup script for shipment tracking monitoring

This script sets up all monitoring components:
1. CloudWatch custom metrics (via Lambda functions)
2. CloudWatch alarms with SNS notifications
3. CloudWatch dashboard for visualization

Usage:
    python setup_monitoring.py <admin_email>

Example:
    python setup_monitoring.py admin@aquachain.com
"""
import sys
import boto3
from shipment_alarms import (
    create_sns_topic_for_alarms,
    subscribe_email_to_alarms,
    create_all_alarms
)
from shipment_dashboard import create_shipment_dashboard, get_dashboard_url


def setup_complete_monitoring(admin_email: str = None):
    """
    Set up complete monitoring infrastructure
    
    Args:
        admin_email: Email address for alarm notifications (optional)
    """
    print("="*70)
    print("SHIPMENT TRACKING MONITORING SETUP")
    print("="*70)
    print()
    
    # Step 1: Create SNS topic for alarms
    print("Step 1: Creating SNS topic for alarm notifications...")
    topic_arn = create_sns_topic_for_alarms()
    print(f"✓ SNS Topic created: {topic_arn}")
    print()
    
    # Step 2: Subscribe email to alarms
    if admin_email:
        print(f"Step 2: Subscribing {admin_email} to alarm notifications...")
        subscription_arn = subscribe_email_to_alarms(topic_arn, admin_email)
        print(f"✓ Email subscribed: {subscription_arn}")
        print("  NOTE: Check your email and confirm the subscription!")
        print()
    else:
        print("Step 2: Skipping email subscription (no email provided)")
        print("  You can subscribe later using:")
        print(f"  aws sns subscribe --topic-arn {topic_arn} --protocol email --notification-endpoint <email>")
        print()
    
    # Step 3: Create CloudWatch alarms
    print("Step 3: Creating CloudWatch alarms...")
    alarm_names = create_all_alarms(topic_arn)
    print(f"✓ Created {len(alarm_names)} alarms:")
    for name in alarm_names:
        print(f"  - {name}")
    print()
    
    # Step 4: Create CloudWatch dashboard
    print("Step 4: Creating CloudWatch dashboard...")
    dashboard_name = create_shipment_dashboard()
    dashboard_url = get_dashboard_url()
    print(f"✓ Dashboard created: {dashboard_name}")
    print()
    
    # Summary
    print("="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print()
    print("Monitoring Components:")
    print(f"  ✓ SNS Topic: {topic_arn}")
    if admin_email:
        print(f"  ✓ Email Subscription: {admin_email} (pending confirmation)")
    print(f"  ✓ CloudWatch Alarms: {len(alarm_names)} alarms")
    print(f"  ✓ CloudWatch Dashboard: {dashboard_name}")
    print()
    print("Next Steps:")
    print("  1. Confirm email subscription (check inbox)")
    print("  2. View dashboard:")
    print(f"     {dashboard_url}")
    print("  3. Deploy Lambda functions with CloudWatch metrics enabled")
    print("  4. Test alarm notifications by triggering threshold conditions")
    print()
    print("Alarm Thresholds:")
    print("  - Failed Delivery Rate: > 5%")
    print("  - Webhook Errors: > 10 per 5 minutes")
    print("  - Stale Shipments: > 10")
    print("  - Lambda Errors: > 5 per 5 minutes")
    print()
    print("CloudWatch Metrics Emitted:")
    print("  - ShipmentsCreated: Count of shipments created")
    print("  - WebhooksProcessed: Count of webhooks processed")
    print("  - DeliveryTime: Time from creation to delivery (hours)")
    print("  - FailedDeliveries: Count of failed deliveries")
    print("  - StaleShipments: Count of stale shipments")
    print("  - LambdaErrors: Count of Lambda errors by function")
    print()


def verify_monitoring_setup():
    """
    Verify that monitoring components are set up correctly
    """
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    print("Verifying monitoring setup...")
    print()
    
    # Check SNS topic
    try:
        topics = sns.list_topics()
        alarm_topic = [t for t in topics['Topics'] if 'AquaChain-Shipments-Alarms' in t['TopicArn']]
        if alarm_topic:
            print("✓ SNS Topic exists")
            topic_arn = alarm_topic[0]['TopicArn']
            
            # Check subscriptions
            subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            print(f"  Subscriptions: {len(subs['Subscriptions'])}")
            for sub in subs['Subscriptions']:
                status = sub['SubscriptionArn']
                if status == 'PendingConfirmation':
                    print(f"    - {sub['Endpoint']} (pending confirmation)")
                else:
                    print(f"    - {sub['Endpoint']} (confirmed)")
        else:
            print("✗ SNS Topic not found")
    except Exception as e:
        print(f"✗ Error checking SNS topic: {str(e)}")
    
    print()
    
    # Check alarms
    try:
        alarms = cloudwatch.describe_alarms(AlarmNamePrefix='AquaChain-Shipments-')
        alarm_count = len(alarms['MetricAlarms'])
        print(f"✓ CloudWatch Alarms: {alarm_count} alarms")
        for alarm in alarms['MetricAlarms']:
            state = alarm['StateValue']
            state_icon = "✓" if state == "OK" else "⚠" if state == "INSUFFICIENT_DATA" else "✗"
            print(f"  {state_icon} {alarm['AlarmName']}: {state}")
    except Exception as e:
        print(f"✗ Error checking alarms: {str(e)}")
    
    print()
    
    # Check dashboard
    try:
        dashboards = cloudwatch.list_dashboards(DashboardNamePrefix='AquaChain-Shipments-')
        if dashboards['DashboardEntries']:
            print("✓ CloudWatch Dashboard exists")
            for dash in dashboards['DashboardEntries']:
                print(f"  - {dash['DashboardName']}")
        else:
            print("✗ CloudWatch Dashboard not found")
    except Exception as e:
        print(f"✗ Error checking dashboard: {str(e)}")
    
    print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'verify':
            verify_monitoring_setup()
        else:
            admin_email = sys.argv[1]
            setup_complete_monitoring(admin_email)
    else:
        print("Usage:")
        print("  Setup monitoring:  python setup_monitoring.py <admin_email>")
        print("  Verify setup:      python setup_monitoring.py verify")
        print()
        print("Example:")
        print("  python setup_monitoring.py admin@aquachain.com")
        sys.exit(1)
