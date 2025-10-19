# AquaChain Infrastructure Setup

This directory contains the infrastructure setup code for the AquaChain water quality monitoring system. The infrastructure is built on AWS serverless services and follows security best practices.

## Architecture Overview

The AquaChain system consists of the following AWS components:

- **DynamoDB**: Time-series data storage with immutable ledger
- **S3**: Data lake and audit trail with Object Lock
- **IoT Core**: Secure device communication and message routing
- **KMS**: Encryption key management for data protection
- **Lambda**: Data processing and business logic
- **API Gateway**: REST and WebSocket APIs
- **Cognito**: User authentication and authorization

## Directory Structure

```
infrastructure/
├── dynamodb/
│   ├── tables.py          # DynamoDB table definitions
│   └── operations.py      # Database operations and utilities
├── s3/
│   └── buckets.py         # S3 bucket configuration with Object Lock
├── kms/
│   └── keys.py            # KMS key management for encryption
├── iot/
│   ├── core_setup.py      # IoT Core configuration
│   └── provisioning_lambda.py  # Device provisioning function
├── setup_infrastructure.py     # Main setup orchestration script
└── README.md              # This file
```

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Python 3.11+** with boto3 installed
3. **AWS account** with sufficient permissions to create:
   - DynamoDB tables
   - S3 buckets
   - KMS keys
   - IoT Core resources
   - IAM roles and policies
   - Lambda functions

## Quick Start

### 1. Install Dependencies

```bash
pip install boto3
```

### 2. Configure AWS Credentials

```bash
aws configure
```

### 3. Run Infrastructure Setup

```bash
python infrastructure/setup_infrastructure.py --region us-east-1
```

For cross-account audit trail replication:

```bash
python infrastructure/setup_infrastructure.py --region us-east-1 --replica-account 123456789012
```

## Component Details

### DynamoDB Tables

The system creates the following DynamoDB tables:

1. **aquachain-readings**: Time-windowed sensor data storage
   - Partition Key: `deviceId_month` (format: DEV-1234#202510)
   - Sort Key: `timestamp` (ISO 8601)
   - TTL: 90 days for hot data
   - Streams: Enabled for ledger replication

2. **aquachain-ledger**: Immutable ledger with hash chaining
   - Partition Key: `partition_key` (fixed: "GLOBAL_SEQUENCE")
   - Sort Key: `sequenceNumber` (auto-incrementing)
   - Streams: Enabled for audit trail

3. **aquachain-sequence**: Atomic sequence number generation
   - Partition Key: `sequenceType` ("LEDGER")
   - Used for global ordering of ledger entries

4. **aquachain-users**: User profile management
   - Partition Key: `userId` (Cognito Sub)
   - GSI: Email index for lookups

5. **aquachain-service-requests**: Technician assignment
   - Partition Key: `requestId` (UUID)
   - Sort Key: `timestamp`
   - Multiple GSIs for consumer, technician, and status queries

### S3 Buckets

1. **Data Lake Bucket** (`aquachain-data-lake-{account-id}`)
   - Raw sensor data storage
   - ML model storage
   - Lifecycle policies for cost optimization
   - KMS encryption with dedicated key

2. **Audit Trail Bucket** (`aquachain-audit-trail-{account-id}`)
   - Object Lock enabled (7-year retention)
   - Hash chain verification data
   - Cross-account replication for tamper evidence
   - Compliance-grade encryption

3. **Replica Bucket** (`aquachain-audit-replica-{replica-account}`)
   - Read-only cross-account replica
   - Independent audit verification
   - Separate encryption key

### KMS Keys

1. **S3 Encryption Key** (`alias/aquachain-s3-key`)
   - Symmetric key for S3 data encryption
   - Used by data processing services

2. **Audit Encryption Key** (`alias/aquachain-audit-key`)
   - Symmetric key for audit trail encryption
   - Restricted access for compliance

3. **Ledger Signing Key** (`alias/aquachain-ledger-signing-key`)
   - Asymmetric RSA key for ledger entry signing
   - Provides cryptographic proof of integrity

4. **Replica Encryption Key** (`alias/aquachain-replica-key`)
   - Cross-account encryption for replica bucket
   - Enables independent audit verification

### IoT Core Configuration

1. **Device Policies**: Restrict device permissions to specific topics
2. **Thing Types**: Define AquaChain sensor device type
3. **Provisioning Templates**: Just-in-Time device provisioning
4. **Topic Rules**: Route messages to processing functions
5. **Certificate Management**: X.509 certificates for device authentication

## Security Features

### Data Protection
- **Encryption at Rest**: All data encrypted with KMS keys
- **Encryption in Transit**: TLS 1.2+ for all communications
- **Object Lock**: Immutable audit trail storage
- **Cross-Account Replication**: Independent audit verification

### Access Control
- **IAM Roles**: Least privilege access for services
- **Device Certificates**: X.509 certificates for IoT devices
- **JWT Tokens**: Cognito-based user authentication
- **Resource Policies**: Fine-grained access control

### Audit and Compliance
- **Hash Chain**: Cryptographic integrity verification
- **Immutable Ledger**: Tamper-evident data storage
- **Audit Logs**: Complete activity tracking
- **Compliance Reports**: Automated report generation

## Monitoring and Alerting

The infrastructure includes:

- **CloudWatch Alarms**: Error rate and performance monitoring
- **DynamoDB Streams**: Real-time data change tracking
- **IoT Device Management**: Device health monitoring
- **Cost Optimization**: Lifecycle policies and reserved capacity

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure AWS credentials have sufficient permissions
   - Check IAM policies for required actions

2. **Resource Already Exists**
   - The setup script handles existing resources gracefully
   - Check AWS console for resource status

3. **Region Availability**
   - Ensure all services are available in the selected region
   - Some features may not be available in all regions

### Validation

After setup, validate the infrastructure:

```python
from infrastructure.setup_infrastructure import AquaChainInfrastructureManager

manager = AquaChainInfrastructureManager()
validation_results = manager._validate_infrastructure()
print(validation_results)
```

## Cost Optimization

The infrastructure is designed for cost efficiency:

- **Serverless Architecture**: Pay-per-use pricing
- **DynamoDB On-Demand**: Automatic scaling without provisioning
- **S3 Lifecycle Policies**: Automatic data archiving
- **Reserved Capacity**: Consider for predictable workloads

## Next Steps

After infrastructure setup:

1. **Deploy Lambda Functions**: Use SAM or CDK for function deployment
2. **Configure API Gateway**: Set up REST and WebSocket APIs
3. **Set up Monitoring**: Create CloudWatch dashboards
4. **Test Device Provisioning**: Validate IoT device onboarding
5. **Load Testing**: Verify performance under expected load

## Support

For issues or questions:

1. Check AWS CloudWatch logs for error details
2. Validate IAM permissions and resource policies
3. Review AWS service limits and quotas
4. Consult AWS documentation for service-specific guidance