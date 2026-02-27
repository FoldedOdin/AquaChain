# Global Monitoring Dashboard Stack

## Overview

This stack creates the foundational DynamoDB infrastructure for the Global Monitoring Dashboard upgrade, transforming it from a basic infrastructure health panel into a comprehensive Global Water Intelligence Control Center.

## Created Resources

### 1. Pre-Aggregated Summary Table
**Table Name**: `AquaChain-PreAggregatedSummary-{env}`

Stores pre-computed global metrics in 5-minute time buckets for efficient querying at scale (100,000+ devices).

**Schema**:
- **Partition Key**: `region_date` (STRING) - Format: `{region}#YYYY-MM-DD`
- **Sort Key**: `time_bucket` (STRING) - Format: `YYYY-MM-DDTHH:MM:00Z`
- **Billing**: On-demand
- **TTL**: 30 days for 5-minute buckets
- **Streams**: Enabled (NEW_IMAGE)
- **Point-in-Time Recovery**: Enabled

**Global Secondary Index**:
- **TimeBucketRegionIndex**: Query all regions for a specific time
  - PK: `time_bucket`
  - SK: `region`
  - Projection: ALL

**Design Rationale**: Region-based partition keys distribute writes across regions to avoid hot partitions. At 100k devices, a single-date partition would create hot spots.

### 2. Audit Log Table
**Table Name**: `AquaChain-AuditLog-{env}`

Immutable audit trail for all dashboard access and operations, meeting compliance requirements.

**Schema**:
- **Partition Key**: `date` (STRING) - Format: `YYYY-MM-DD`
- **Sort Key**: `user_timestamp` (STRING) - Format: `{user_id}#{ISO8601_timestamp}`
- **Billing**: On-demand
- **TTL**: 2 years (730 days)
- **Streams**: Enabled (NEW_IMAGE)
- **Point-in-Time Recovery**: Enabled

**Global Secondary Index**:
- **UserTimestampIndex**: Query all actions by a specific user
  - PK: `user_id`
  - SK: `timestamp`
  - Projection: ALL

**Immutability**: IAM policy denies UpdateItem and DeleteItem operations to prevent tampering with audit records.

### 3. Stream-Enabled Existing Tables

The stack imports and documents stream configuration for:

- **AquaChain-Readings**: Stream triggers incremental aggregation Lambda
- **AquaChain-Alerts**: Stream triggers alert stream Lambda for WebSocket push

**Note**: Streams must be enabled manually on existing tables using the provided scripts.

## Deployment

### Quick Start

```bash
# Enable streams on existing tables
cd scripts/deployment
./enable-dynamodb-streams.sh  # Linux/Mac
# or
enable-dynamodb-streams.bat    # Windows

# Deploy the stack
cd infrastructure/cdk
cdk deploy AquaChain-GlobalMonitoringDashboard-dev
```

### Detailed Instructions

See `DOCS/deployment/global-monitoring-dashboard-deployment.md` for complete deployment guide.

## Architecture Decisions

### Why Region-Based Partition Keys?

At 100,000 devices with 5-minute readings, a simple date-based partition key would create hot partitions:
- All writes for a given day go to the same partition
- DynamoDB throttles at ~1000 writes/sec per partition
- 100k devices × 12 readings/hour = 1.2M writes/hour = 333 writes/sec (approaching limits)

Region-based partitioning distributes writes across multiple partitions:
- Writes spread across N regions
- Each region handles ~333/N writes/sec
- Eliminates hot partition risk

### Why Date-Based Audit Log Partitioning?

Audit logs have different access patterns:
- Writes are distributed across active admins (not concentrated)
- Queries are typically by date range or by user
- Date-based partitioning aligns with common query patterns
- UserTimestampIndex GSI enables efficient user-based queries

### Why Immutable Audit Logs?

Compliance requirements (GDPR, SOC 2) mandate immutable audit trails:
- IAM policy denies UpdateItem and DeleteItem at the resource level
- Even compromised Lambda functions cannot modify audit records
- Point-in-time recovery provides additional protection
- Meets regulatory requirements for audit trail integrity

## Cost Estimation

### Development Environment (~$6/month)
- Pre-Aggregated Summary: ~$4/month
- Audit Log: ~$2/month
- Existing table streams: ~$0.11/month

### Production Environment (~$65/month)
- Pre-Aggregated Summary: ~$50/month
- Audit Log: ~$10/month
- Existing table streams: ~$5/month

## Next Steps

After deploying this stack:

1. **Phase 2**: Deploy Lambda functions
   - Incremental Aggregation Lambda (triggered by Readings stream)
   - Alert Stream Lambda (triggered by Alerts stream)
   - Global Metrics API Lambda

2. **Phase 3**: Deploy ElastiCache Redis cluster
   - Multi-AZ configuration for high availability
   - Cache aggregated metrics (30-second TTL)
   - Rate limiting counters

3. **Phase 4**: Configure CloudWatch Metric Streams
   - Stream infrastructure metrics to Pre-Aggregated table
   - Eliminate slow CloudWatch API calls

4. **Phase 5**: Deploy frontend components
   - React dashboard with TypeScript
   - WebSocket integration for real-time alerts
   - Auto-refresh with staleness indicators

## Monitoring

Set up CloudWatch alarms for:
- Read/Write capacity consumption
- Throttled requests
- Stream processing lag
- TTL deletion metrics
- Point-in-time recovery status

## References

- **Requirements**: 15.1, 15.2, 15.3, 15.8, 17.2, 17.7, 19.1, 19.8, 3.2
- **Design Document**: `.kiro/specs/global-monitoring-dashboard-upgrade/design.md`
- **Tasks**: `.kiro/specs/global-monitoring-dashboard-upgrade/tasks.md`
- **Deployment Guide**: `DOCS/deployment/global-monitoring-dashboard-deployment.md`
