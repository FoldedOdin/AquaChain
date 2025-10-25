# DynamoDB Global Tables Setup Guide

## Overview

Global Tables provide multi-region, fully replicated DynamoDB tables for disaster recovery and low-latency global access.

## Architecture

```
Primary Region (ap-south-1)
    ↓ ↑ (bidirectional replication)
Secondary Region (us-west-2)
    ↓ ↑
Tertiary Region (eu-west-1)
```

## Implementation

### Step 1: Update DataStack for Global Tables

```python
# infrastructure/cdk/stacks/data_stack.py

from aws_cdk import (
    aws_dynamodb as dynamodb,
    Duration
)

class AquaChainDataStack(Stack):
    def _create_readings_table(self):
        """Create readings table with global replication"""
        
        table = dynamodb.TableV2(
            self, "ReadingsTable",
            table_name=f"aquachain-readings-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="deviceId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            
            # Enable Global Tables
            replicas=[
                dynamodb.ReplicaTableProps(
                    region="us-west-2",
                    global_secondary_index_options={
                        "WQIIndex": dynamodb.ReplicaGlobalSecondaryIndexOptions(
                            read_capacity=dynamodb.Capacity.autoscaled(
                                max_capacity=100
                            )
                        )
                    }
                ),
                dynamodb.ReplicaTableProps(
                    region="eu-west-1",
                    global_secondary_index_options={
                        "WQIIndex": dynamodb.ReplicaGlobalSecondaryIndexOptions(
                            read_capacity=dynamodb.Capacity.autoscaled(
                                max_capacity=100
                            )
                        )
                    }
                )
            ],
            
            # Billing mode
            billing=dynamodb.Billing.on_demand(),
            
            # Point-in-time recovery
            point_in_time_recovery=True,
            
            # Encryption
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            
            # Stream for replication
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            
            # Deletion protection
            deletion_protection=self.config['environment'] == 'prod',
            
            # Time to live
            time_to_live_attribute="ttl"
        )
        
        return table
```

### Step 2: Enable Global Tables via CLI

```bash
# Create table in primary region
aws dynamodb create-table \
  --table-name aquachain-readings-prod \
  --attribute-definitions \
    AttributeName=deviceId,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=deviceId,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
  --region ap-south-1

# Create global table
aws dynamodb create-global-table \
  --global-table-name aquachain-readings-prod \
  --replication-group \
    RegionName=ap-south-1 \
    RegionName=us-west-2 \
    RegionName=eu-west-1 \
  --region ap-south-1
```

### Step 3: Verify Replication

```python
# scripts/verify_global_tables.py

import boto3
from datetime import datetime

def verify_global_table_replication(table_name: str):
    """Verify data is replicating across regions"""
    
    regions = ['ap-south-1', 'us-west-2', 'eu-west-1']
    
    # Write test item to primary region
    primary_dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = primary_dynamodb.Table(table_name)
    
    test_item = {
        'deviceId': 'TEST-REPLICATION',
        'timestamp': datetime.utcnow().isoformat(),
        'test_data': 'Global table replication test'
    }
    
    table.put_item(Item=test_item)
    print(f"✅ Test item written to primary region (ap-south-1)")
    
    # Wait for replication
    import time
    time.sleep(5)
    
    # Verify in all regions
    for region in regions:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        
        try:
            response = table.get_item(
                Key={
                    'deviceId': test_item['deviceId'],
                    'timestamp': test_item['timestamp']
                }
            )
            
            if 'Item' in response:
                print(f"✅ Test item found in {region}")
            else:
                print(f"❌ Test item NOT found in {region}")
                
        except Exception as e:
            print(f"❌ Error checking {region}: {e}")
    
    # Cleanup
    table.delete_item(
        Key={
            'deviceId': test_item['deviceId'],
            'timestamp': test_item['timestamp']
        }
    )
    print("🧹 Test item cleaned up")

if __name__ == "__main__":
    verify_global_table_replication('aquachain-readings-prod')
```

## Monitoring Global Tables

### CloudWatch Metrics

```python
# Monitor replication lag
import boto3

cloudwatch = boto3.client('cloudwatch')

# Get replication latency
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ReplicationLatency',
    Dimensions=[
        {
            'Name': 'TableName',
            'Value': 'aquachain-readings-prod'
        },
        {
            'Name': 'ReceivingRegion',
            'Value': 'us-west-2'
        }
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,
    Statistics=['Average', 'Maximum']
)

print(f"Replication Latency: {response['Datapoints']}")
```

### Create CloudWatch Alarms

```python
# In MonitoringStack
replication_lag_alarm = cloudwatch.Alarm(
    self, "ReplicationLagAlarm",
    alarm_name=f"aquachain-replication-lag-{config['environment']}",
    metric=cloudwatch.Metric(
        namespace="AWS/DynamoDB",
        metric_name="ReplicationLatency",
        dimensions_map={
            "TableName": "aquachain-readings-prod",
            "ReceivingRegion": "us-west-2"
        },
        statistic="Average",
        period=Duration.minutes(5)
    ),
    threshold=1000,  # 1 second in milliseconds
    evaluation_periods=2,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarm_description="Alert when replication lag exceeds 1 second"
)

replication_lag_alarm.add_alarm_action(
    cloudwatch_actions.SnsAction(critical_alerts_topic)
)
```

## Failover Procedures

### Automatic Failover with Route 53

```python
# infrastructure/cdk/stacks/failover_stack.py

from aws_cdk import (
    aws_route53 as route53,
    aws_route53_targets as targets
)

# Create health check for primary region
health_check = route53.CfnHealthCheck(
    self, "PrimaryRegionHealthCheck",
    health_check_config=route53.CfnHealthCheck.HealthCheckConfigProperty(
        type="HTTPS",
        resource_path="/health",
        fully_qualified_domain_name="api.aquachain.com",
        port=443,
        request_interval=30,
        failure_threshold=3
    )
)

# Create failover record
route53.ARecord(
    self, "APIFailoverRecord",
    zone=hosted_zone,
    record_name="api",
    target=route53.RecordTarget.from_alias(
        targets.ApiGateway(primary_api)
    ),
    geo_location=route53.GeoLocation.country("IN"),
    set_identifier="Primary-India"
)

route53.ARecord(
    self, "APIFailoverRecordSecondary",
    zone=hosted_zone,
    record_name="api",
    target=route53.RecordTarget.from_alias(
        targets.ApiGateway(secondary_api)
    ),
    geo_location=route53.GeoLocation.country("US"),
    set_identifier="Secondary-US"
)
```

### Manual Failover Script

```bash
#!/bin/bash
# scripts/failover-to-secondary.sh

echo "🚨 Initiating failover to secondary region..."

# Update Route 53 to point to secondary region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://failover-config.json

# Update application configuration
aws ssm put-parameter \
  --name /aquachain/active-region \
  --value us-west-2 \
  --overwrite

# Notify team
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:aquachain-alerts \
  --subject "FAILOVER: Switched to Secondary Region" \
  --message "Primary region (ap-south-1) failed. Now serving from us-west-2"

echo "✅ Failover complete. Active region: us-west-2"
```

## Cost Considerations

### Global Tables Pricing

- **Replicated Write Requests:** $1.875 per million writes (2x normal cost)
- **Storage:** Charged in each region
- **Data Transfer:** Inter-region transfer costs apply

### Example Monthly Cost

For 1 million writes/day across 3 regions:
- Writes: 30M × $1.875/M = $56.25
- Storage (10GB per region): 30GB × $0.25/GB = $7.50
- Data Transfer: ~$9/GB × 10GB = $90
- **Total: ~$154/month**

## Best Practices

1. **Use Global Tables for:**
   - Critical data requiring high availability
   - Multi-region applications
   - Disaster recovery

2. **Don't Use Global Tables for:**
   - Temporary data
   - Region-specific data
   - Cost-sensitive applications

3. **Monitoring:**
   - Set up replication lag alarms
   - Monitor write conflicts
   - Track cross-region costs

4. **Testing:**
   - Regular failover drills
   - Verify data consistency
   - Test conflict resolution

## Troubleshooting

### High Replication Lag

```bash
# Check DynamoDB Streams
aws dynamodb describe-table \
  --table-name aquachain-readings-prod \
  --region ap-south-1 \
  --query 'Table.StreamSpecification'

# Check for throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=aquachain-readings-prod \
  --start-time 2025-10-24T00:00:00Z \
  --end-time 2025-10-24T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Replication Conflicts

Global Tables use "last writer wins" conflict resolution. Monitor conflicts:

```python
# Check for conflicts
cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ConflictResolution',
    Dimensions=[
        {'Name': 'TableName', 'Value': 'aquachain-readings-prod'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=24),
    EndTime=datetime.utcnow(),
    Period=3600,
    Statistics=['Sum']
)
```

## Resources

- [DynamoDB Global Tables Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html)
- [Global Tables Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html)
- [Monitoring Global Tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables.monitoring.html)
