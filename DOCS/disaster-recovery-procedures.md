# AquaChain Disaster Recovery Procedures

## Overview

This document outlines the disaster recovery (DR) procedures for the AquaChain water quality monitoring system. The DR implementation provides automated backup, cross-region replication, and recovery testing to ensure business continuity and data protection.

## Architecture

### Backup Strategy

#### Automated Backups
- **DynamoDB Tables**: Daily backups with 35-day retention (production), weekly backups with 7-day retention (dev/staging)
- **S3 Buckets**: Daily backups for critical buckets (audit trail, ML models)
- **Continuous Backups**: Hourly backups for critical tables in production (7-day retention)

#### Cross-Region Replication
- **Audit Trail**: Real-time replication to secondary region with read-only access
- **ML Models**: Cross-region backup for model artifacts
- **Hash Chain Verification**: Immutable replication for compliance

### Recovery Objectives

- **Recovery Time Objective (RTO)**: 4 hours for full system recovery
- **Recovery Point Objective (RPO)**: 1 hour maximum data loss
- **Critical Path RTO**: 30 minutes for data ingestion pipeline
- **Audit Trail RPO**: 0 (real-time replication)

## Automated Procedures

### Backup Automation

The system automatically creates backups using AWS Backup service with enhanced automation:

```yaml
Backup Schedule:
  Production:
    - Daily backups at 2:00 AM UTC
    - Hourly continuous backups for critical tables
    - Cross-region replication enabled
    - 35-day retention period
  
  Staging:
    - Daily backups at 2:00 AM UTC
    - Cross-region replication enabled
    - 30-day retention period
  
  Development:
    - Weekly backups on Sunday at 2:00 AM UTC
    - 7-day retention period
```

### DR Testing Automation

Automated DR tests run weekly on Saturdays at 4:00 AM UTC for staging and production:

1. **Backup Validation**: Verify all required backups are available and recent
2. **Restore Testing**: Create test resources from latest backups
3. **Data Validation**: Verify restored data integrity and accessibility
4. **Cross-Region Replication Validation**: Check replication status and lag
5. **Automated Failover Testing**: Test failover triggers and procedures
6. **Cleanup**: Remove test resources to avoid costs

### Automated Failover System

The system includes automated failover capabilities for regional disasters:

#### Failover Triggers
- **Regional Health Monitoring**: Continuous monitoring of service health across regions
- **Composite Alarms**: Multi-service health checks that trigger failover decisions
- **Threshold-Based Activation**: Failover triggered when health score drops below 50%

#### Failover Process
1. **Outage Assessment**: Automated validation of regional outage conditions
2. **DNS Failover**: Route 53 health checks redirect traffic to secondary region
3. **Resource Scaling**: Automatic scaling of secondary region resources
4. **Data Validation**: Verification of cross-region data consistency
5. **Service Validation**: End-to-end testing of critical system functions

#### Failover Validation
- **Health Checks**: Automated validation of secondary region services
- **Performance Testing**: Verification of system performance in secondary region
- **Rollback Capability**: Automatic rollback if failover validation fails

### Monitoring and Alerting

- **Backup Failures**: Immediate alerts via SNS/PagerDuty
- **DR Test Failures**: Weekly test result notifications
- **Cross-Region Replication**: Monitor replication lag and failures
- **Custom Metrics**: Track DR test success rates and backup coverage

## Manual Procedures

### Using the DR Management Script

The `scripts/disaster_recovery.py` script provides manual DR operations:

#### List Available Backups
```bash
python scripts/disaster_recovery.py --environment prod list-backups
```

#### Validate Backup Status
```bash
python scripts/disaster_recovery.py --environment prod validate-backups
```

#### Run Manual DR Test
```bash
python scripts/disaster_recovery.py --environment prod run-dr-test
```

#### Create Manual Backup
```bash
python scripts/disaster_recovery.py --environment prod create-backup \
  --resource-arn arn:aws:dynamodb:us-east-1:ACCOUNT:table/aquachain-table-ledger-prod
```

#### Get DR Metrics
```bash
python scripts/disaster_recovery.py --environment prod get-metrics --days 30
```

#### Test Automated Failover System
```bash
python scripts/disaster_recovery.py --environment prod test-failover
```

#### Generate Comprehensive DR Report
```bash
python scripts/disaster_recovery.py --environment prod generate-report --output dr-report.txt
```

### AWS Console Operations

#### Restore from Backup

1. **Navigate to AWS Backup Console**
2. **Select Recovery Points**
3. **Choose the backup to restore**
4. **Configure restore parameters**:
   - New resource name (for testing)
   - Billing mode (use PAY_PER_REQUEST for tests)
   - Encryption settings
5. **Start restore job**
6. **Monitor progress in AWS Backup console**

#### Cross-Region Failover

1. **Verify secondary region resources**
2. **Update DNS/Route 53 records** to point to secondary region
3. **Scale up secondary region resources**
4. **Update application configuration** for new region
5. **Validate functionality** in secondary region

## Emergency Response Procedures

### Data Loss Incident

1. **Immediate Assessment**
   - Determine scope and timeline of data loss
   - Identify affected tables/buckets
   - Check backup availability

2. **Recovery Actions**
   ```bash
   # Validate available backups
   python scripts/disaster_recovery.py --environment prod validate-backups
   
   # Identify recovery point
   python scripts/disaster_recovery.py --environment prod list-backups
   
   # Restore from backup (use AWS Console for production restores)
   ```

3. **Verification**
   - Verify data integrity after restore
   - Check hash chain consistency for ledger data
   - Validate application functionality

4. **Communication**
   - Notify stakeholders of incident and recovery status
   - Document lessons learned
   - Update procedures if needed

### Regional Outage

1. **Activate Secondary Region**
   - Verify secondary region resources are healthy
   - Scale up compute resources in secondary region
   - Update Route 53 health checks and DNS

2. **Application Configuration**
   - Update environment variables for new region
   - Verify cross-region data replication status
   - Test critical application paths

3. **Monitoring**
   - Monitor application performance in secondary region
   - Track any data synchronization issues
   - Prepare for failback when primary region recovers

### Complete System Failure

1. **Assessment Phase** (0-30 minutes)
   - Determine extent of failure
   - Activate incident response team
   - Notify stakeholders

2. **Recovery Phase** (30 minutes - 4 hours)
   - Deploy infrastructure in secondary region
   - Restore data from latest backups
   - Configure application services
   - Update DNS and routing

3. **Validation Phase** (4-6 hours)
   - Test all critical system functions
   - Verify data integrity and completeness
   - Conduct end-to-end testing

4. **Communication Phase** (Ongoing)
   - Provide regular status updates
   - Document recovery actions
   - Plan for primary region restoration

## Testing Procedures

### Weekly Automated Tests

The system runs automated DR tests every Saturday:

1. **Backup Validation**
   - Verify all critical resources have recent backups
   - Check backup sizes and completion status
   - Validate cross-region replication

2. **Restore Testing**
   - Create test table from latest DynamoDB backup
   - Verify table is accessible and contains data
   - Test basic read/write operations

3. **Cleanup**
   - Remove test resources
   - Generate test report
   - Send notifications to DR team

### Monthly Manual Tests

Conduct comprehensive manual DR tests monthly:

1. **Full System Restore Test**
   - Restore all critical components in test environment
   - Verify end-to-end functionality
   - Test user authentication and authorization
   - Validate data processing pipeline

2. **Cross-Region Failover Test**
   - Simulate primary region failure
   - Activate secondary region resources
   - Test application functionality
   - Measure recovery time

3. **Documentation Review**
   - Review and update DR procedures
   - Verify contact information
   - Update recovery time estimates

### Annual DR Drill

Conduct full-scale DR drill annually:

1. **Scenario Planning**
   - Define realistic disaster scenario
   - Set success criteria
   - Assign roles and responsibilities

2. **Execution**
   - Simulate complete system failure
   - Execute recovery procedures
   - Document all actions and timings

3. **Post-Drill Analysis**
   - Analyze performance against RTO/RPO targets
   - Identify improvement opportunities
   - Update procedures and training

## Compliance and Audit

### Audit Trail Protection

- **Immutable Storage**: S3 Object Lock with 7-year retention
- **Cross-Account Replication**: Read-only replica in separate AWS account
- **Hash Chain Verification**: Cryptographic integrity verification
- **Access Logging**: All access to audit data is logged

### Compliance Requirements

- **Data Retention**: 7-year retention for audit trail data
- **Backup Verification**: Monthly verification of backup integrity
- **Recovery Testing**: Quarterly recovery testing with documentation
- **Incident Documentation**: All DR incidents must be documented

### Reporting

Monthly DR reports include:
- Backup success rates
- DR test results
- RTO/RPO compliance metrics
- Cross-region replication status
- Compliance audit findings

## Contacts and Escalation

### Primary Contacts

- **DR Team Lead**: [Contact Information]
- **Infrastructure Team**: [Contact Information]
- **Security Team**: [Contact Information]
- **Compliance Officer**: [Contact Information]

### Escalation Matrix

1. **Level 1**: Infrastructure Team (0-30 minutes)
2. **Level 2**: DR Team Lead (30-60 minutes)
3. **Level 3**: Engineering Management (1-2 hours)
4. **Level 4**: Executive Team (2+ hours)

### Communication Channels

- **Primary**: PagerDuty alerts
- **Secondary**: Slack #incident-response
- **Backup**: Email distribution list
- **External**: Customer status page

## Appendix

### Resource Naming Conventions

```
Backup Vaults: aquachain-vault-{purpose}-{environment}
State Machines: aquachain-statemachine-{purpose}-{environment}
Lambda Functions: aquachain-function-{purpose}-{environment}
SNS Topics: aquachain-topic-{purpose}-{environment}
```

### Key Metrics

- **Backup Success Rate**: Target 99.9%
- **DR Test Success Rate**: Target 95%
- **Mean Time to Recovery**: Target < 4 hours
- **Cross-Region Replication Lag**: Target < 15 minutes

### Useful Commands

```bash
# Check backup status
aws backup list-backup-jobs --by-backup-vault-name aquachain-vault-main-prod

# Monitor Step Function execution
aws stepfunctions describe-execution --execution-arn [EXECUTION_ARN]

# Check cross-region replication
aws s3api get-bucket-replication --bucket aquachain-bucket-audit-trail-prod

# View CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/DisasterRecovery \
  --metric-name RestoreTestSuccess \
  --start-time 2025-10-01T00:00:00Z \
  --end-time 2025-10-20T00:00:00Z \
  --period 86400 \
  --statistics Sum
```