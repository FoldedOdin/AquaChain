# Data Retention Policy for Shipment Tracking

## Overview

This document describes the data retention policy for shipment tracking audit data, ensuring compliance with regulatory requirements while optimizing storage costs.

**Requirements:** 15.5

## Retention Period

- **Primary Storage (DynamoDB):** 2 years from shipment creation
- **Archive Storage (S3):** Indefinite (with lifecycle policies)

## Implementation

### 1. DynamoDB TTL (Time To Live)

**Purpose:** Automatically delete shipment records after 2 years

**Configuration:**
- TTL Attribute: `audit_ttl`
- TTL Value: Unix timestamp (seconds since epoch) set to 2 years from creation
- Deletion Window: Within 48 hours of expiration

**Setup:**
```bash
python infrastructure/dynamodb/configure_shipments_ttl.py
```

**How It Works:**
1. When a shipment is created, `audit_ttl` is set to current time + 2 years
2. DynamoDB automatically scans for expired items (audit_ttl < current time)
3. Expired items are deleted within 48 hours
4. Deleted items are removed from all indexes and backups

**Code Example:**
```python
from audit_trail import calculate_ttl_timestamp

# Calculate TTL for 2-year retention
ttl_timestamp = calculate_ttl_timestamp(years=2)

# Add to shipment item
shipment_item = {
    'shipment_id': 'ship_xxx',
    'order_id': 'ord_xxx',
    # ... other fields ...
    'audit_ttl': ttl_timestamp  # Unix timestamp
}
```

### 2. S3 Archival

**Purpose:** Preserve audit data before TTL deletion for long-term compliance

**Configuration:**
- Archive Bucket: `aquachain-shipment-archives`
- Archive Prefix: `shipments/YYYY/MM/`
- Storage Class: `GLACIER_IR` (Glacier Instant Retrieval)
- Format: Compressed JSON (gzip)

**Trigger:**
- CloudWatch Event Rule: Daily at 2 AM UTC
- Lambda Function: `archive_to_s3`

**Process:**
1. Query shipments with `audit_ttl` within 30 days of expiration
2. Export to compressed JSON format
3. Upload to S3 with date partitioning
4. Metadata includes shipment count and compression ratio

**Code Example:**
```python
# Archive shipments approaching expiration
from archive_to_s3 import handler

# Triggered by CloudWatch Event Rule
result = handler(event={}, context={})
# Returns: {'archived_count': 42, 's3_key': 'shipments/2025/01/...'}
```

**S3 Key Format:**
```
s3://aquachain-shipment-archives/shipments/YYYY/MM/archive-YYYY-MM-DD-HHMMSS.json.gz
```

**Archive Structure:**
```json
{
  "archived_at": "2025-01-01T02:00:00Z",
  "shipment_count": 42,
  "shipments": [
    {
      "shipment_id": "ship_xxx",
      "order_id": "ord_xxx",
      "timeline": [...],
      "webhook_events": [...],
      "admin_actions": [...]
    }
  ]
}
```

### 3. S3 Lifecycle Policies

**Purpose:** Transition archived data to cheaper storage tiers over time

**Recommended Policy:**
```json
{
  "Rules": [
    {
      "Id": "TransitionToGlacierDeepArchive",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}
```

**Storage Tiers:**
- **0-90 days:** Glacier Instant Retrieval (immediate access)
- **90-365 days:** Glacier (3-5 hour retrieval)
- **365+ days:** Deep Archive (12-48 hour retrieval)
- **After 7 years:** Automatic deletion

## Compliance

### Regulatory Requirements

**GDPR (General Data Protection Regulation):**
- ✓ Data retention limited to necessary period
- ✓ Automatic deletion after retention period
- ✓ Audit trail for data access and modifications

**SOC 2 (Service Organization Control 2):**
- ✓ Comprehensive audit logging
- ✓ Data retention policy documented
- ✓ Automated compliance enforcement

**PCI DSS (Payment Card Industry Data Security Standard):**
- ✓ Audit logs retained for minimum 1 year
- ✓ Immediate access for 3 months (Glacier IR)
- ✓ Secure archival for extended period

### Data Categories

**Retained Data:**
- Shipment timeline (all status changes)
- Webhook events (raw payloads)
- Admin actions (user ID, timestamp, details)
- Courier information
- Delivery addresses
- Package metadata

**Not Retained:**
- Payment information (stored separately)
- Customer credentials (never stored)
- Temporary session data

## Monitoring

### CloudWatch Metrics

**TTL Deletion Metrics:**
- `DynamoDB.SystemErrors` - Monitor TTL deletion failures
- `DynamoDB.UserErrors` - Monitor access to expired items

**Archive Metrics:**
- `ShipmentsArchived` - Count of shipments archived daily
- `ArchiveSize` - Size of archived data in bytes
- `ArchiveCompressionRatio` - Compression efficiency

### Alarms

**TTL Configuration:**
- Alert if TTL is disabled
- Alert if TTL attribute is changed

**Archive Failures:**
- Alert if archival Lambda fails
- Alert if S3 upload fails
- Alert if no shipments archived for 7 days (unexpected)

## Restoration

### Restore from Archive

**Use Case:** Compliance audit, legal discovery, customer inquiry

**Process:**
```python
from archive_to_s3 import restore_from_archive

# Restore specific archive
s3_key = 'shipments/2025/01/archive-2025-01-15-020000.json.gz'
shipments = restore_from_archive(s3_key)

# Search for specific shipment
target_shipment = next(
    (s for s in shipments if s['shipment_id'] == 'ship_xxx'),
    None
)
```

**Retrieval Times:**
- Glacier IR: Immediate (milliseconds)
- Glacier: 3-5 hours (Expedited: 1-5 minutes)
- Deep Archive: 12-48 hours

## Cost Optimization

### Storage Costs (Approximate)

**DynamoDB:**
- Active shipments (< 2 years): $0.25/GB/month
- Automatic deletion: No storage cost after TTL

**S3 Storage Classes:**
- Glacier IR: $0.004/GB/month
- Glacier: $0.0036/GB/month
- Deep Archive: $0.00099/GB/month

**Example:**
- 1 million shipments/year
- Average 10 KB per shipment
- Total: 10 GB/year

**Annual Costs:**
- DynamoDB (2 years): $60/year
- S3 Glacier IR (90 days): $0.10/year
- S3 Glacier (275 days): $0.27/year
- S3 Deep Archive (6+ years): $0.60/year
- **Total: ~$61/year**

### Optimization Tips

1. **Compress Archives:** Use gzip compression (70-80% reduction)
2. **Batch Archival:** Archive in daily batches, not per-shipment
3. **Lifecycle Policies:** Automatically transition to cheaper tiers
4. **Query Optimization:** Use DynamoDB Streams instead of scans
5. **Selective Archival:** Archive only completed shipments

## Verification

### Test TTL Configuration

```bash
python infrastructure/dynamodb/configure_shipments_ttl.py
```

### Test Archival Process

```bash
# Set environment variables
export SHIPMENTS_TABLE=aquachain-shipments
export ARCHIVE_BUCKET=aquachain-shipment-archives

# Run archival Lambda
python lambda/shipments/archive_to_s3.py
```

### Verify Audit Trail

```bash
python lambda/shipments/verify_audit_trail.py
```

## Maintenance

### Monthly Tasks

- [ ] Review CloudWatch metrics for TTL deletions
- [ ] Verify S3 archives are being created
- [ ] Check archive compression ratios
- [ ] Monitor storage costs

### Quarterly Tasks

- [ ] Audit compliance with retention policy
- [ ] Review and update lifecycle policies
- [ ] Test restoration process
- [ ] Update documentation

### Annual Tasks

- [ ] Review regulatory requirements
- [ ] Adjust retention period if needed
- [ ] Audit archived data integrity
- [ ] Update cost projections

## Troubleshooting

### TTL Not Deleting Items

**Symptoms:** Items past expiration still in table

**Causes:**
- TTL not enabled
- TTL attribute incorrect
- TTL value in wrong format (must be Unix timestamp in seconds)

**Solution:**
```bash
# Check TTL status
aws dynamodb describe-time-to-live --table-name aquachain-shipments

# Re-enable TTL if needed
python infrastructure/dynamodb/configure_shipments_ttl.py
```

### Archive Lambda Failing

**Symptoms:** No archives created, CloudWatch errors

**Causes:**
- S3 bucket doesn't exist
- Lambda lacks S3 permissions
- DynamoDB query timeout

**Solution:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/archive-shipments --follow

# Verify S3 bucket
aws s3 ls s3://aquachain-shipment-archives/

# Test Lambda locally
python lambda/shipments/archive_to_s3.py
```

### High Storage Costs

**Symptoms:** Unexpected DynamoDB or S3 costs

**Causes:**
- TTL not working (items not being deleted)
- Archives not transitioning to cheaper tiers
- Too many active shipments

**Solution:**
1. Verify TTL is enabled and working
2. Check S3 lifecycle policies are applied
3. Review shipment creation rate
4. Consider increasing compression

## References

- [DynamoDB TTL Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [GDPR Compliance Guide](https://gdpr.eu/)
- [SOC 2 Requirements](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-01 | 1.0 | Initial data retention policy |
