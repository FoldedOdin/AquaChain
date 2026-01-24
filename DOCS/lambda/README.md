# AquaChain Data Processing Pipeline - Lambda Functions

This directory contains the AWS Lambda functions that implement the core data processing pipeline for the AquaChain water quality monitoring system.

## Architecture Overview

The data processing pipeline consists of four main Lambda functions that work together to process IoT sensor data, calculate water quality metrics, maintain a tamper-evident ledger, and create audit trails.

```
IoT Device → Data Processing → ML Inference → Ledger Service → Audit Trail
     ↓              ↓              ↓              ↓              ↓
   MQTT/TLS    Validation &    WQI Calculation  Hash Chaining   S3 Object Lock
              Sanitization    & Anomaly Det.   & KMS Signing   & Replication
```

## Lambda Functions

### 1. Data Processing Function (`data_processing/`)

**Purpose**: Validates, sanitizes, and orchestrates the processing of IoT device data.

**Key Features**:
- JSON schema validation for IoT device data
- Data range validation for sensor parameters (pH, turbidity, TDS, etc.)
- Duplicate detection using device ID and timestamp
- Raw data storage in S3 data lake
- ML inference orchestration
- Critical event detection and alerting
- Dead letter queue integration for failed processing

**Triggers**: 
- AWS IoT Rules Engine
- Direct invocation from API Gateway

**Environment Variables**:
- `READINGS_TABLE`: DynamoDB table for processed readings
- `DATA_LAKE_BUCKET`: S3 bucket for raw data storage
- `ML_INFERENCE_FUNCTION`: ARN of ML inference function
- `DLQ_URL`: Dead letter queue URL

### 2. ML Inference Function (`ml_inference/`)

**Purpose**: Calculates Water Quality Index (WQI) and detects anomalies using Random Forest models.

**Key Features**:
- Random Forest regression for WQI calculation
- Random Forest classification for anomaly detection
- Model loading from S3 with caching and versioning
- Feature engineering (temporal, location, derived features)
- Fallback calculations when ML models are unavailable
- Model explainability with feature importance

**Model Types**:
- **WQI Model**: Predicts water quality index (0-100 scale)
- **Anomaly Model**: Classifies events as normal/sensor_fault/contamination
- **Feature Scaler**: Normalizes input features

**Environment Variables**:
- `MODEL_BUCKET`: S3 bucket containing ML models
- `MODEL_KEY_PREFIX`: S3 prefix for model files

### 3. Secure Ledger Service (`ledger_service/`)

**Purpose**: Maintains a tamper-evident ledger with cryptographic verification.

**Key Features**:
- Global sequence number generation with atomic increments
- Hash chaining algorithm with SHA-256
- KMS asymmetric key signing for cryptographic proof
- DynamoDB conditional writes for consistency
- Hash chain verification utilities
- Audit proof generation

**Security Features**:
- Cryptographic hash chaining prevents tampering
- KMS signing provides non-repudiation
- Atomic sequence numbers ensure ordering
- Conditional writes prevent race conditions

**Environment Variables**:
- `LEDGER_TABLE`: DynamoDB table for ledger entries
- `SEQUENCE_TABLE`: DynamoDB table for sequence generation
- `SIGNING_KEY_ALIAS`: KMS key alias for signing

### 4. Audit Trail Processor (`audit_trail_processor/`)

**Purpose**: Processes DynamoDB streams to create immutable audit records in S3.

**Key Features**:
- DynamoDB Streams processing for real-time audit trail creation
- S3 Object Lock storage for 7-year retention
- Cross-account replication for independent verification
- Idempotent processing with deduplication
- Audit record integrity verification
- Compliance reporting

**Compliance Features**:
- Object Lock prevents deletion/modification
- Cross-account replication for independent audit
- Hash verification for integrity checking
- Retention policy enforcement

**Environment Variables**:
- `AUDIT_BUCKET`: S3 bucket for audit trail storage
- `REPLICA_BUCKET`: Cross-account replica bucket
- `DEDUPLICATION_TABLE`: DynamoDB table for event deduplication

## Data Flow

### 1. IoT Data Ingestion
```
ESP32 Device → AWS IoT Core → IoT Rules Engine → Data Processing Lambda
```

### 2. Data Processing Pipeline
```
Data Processing Lambda:
1. Validate JSON schema
2. Check data ranges
3. Detect duplicates
4. Store raw data in S3
5. Invoke ML inference
6. Store processed data in DynamoDB
7. Trigger alerts if critical
```

### 3. ML Inference
```
ML Inference Lambda:
1. Load models from S3
2. Prepare feature vector
3. Calculate WQI score
4. Detect anomalies
5. Return results with confidence
```

### 4. Ledger Creation
```
Ledger Service:
1. Get next sequence number
2. Get previous hash for chaining
3. Create chain hash
4. Sign with KMS
5. Store in DynamoDB
```

### 5. Audit Trail
```
DynamoDB Streams → Audit Trail Processor:
1. Process stream events
2. Create audit record
3. Store in S3 with Object Lock
4. Replicate cross-account
5. Mark as processed
```

## Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.11 runtime
- Required IAM roles and policies

### Deploy with SAM
```bash
# Build the application
sam build

# Deploy to AWS
sam deploy --guided

# Or deploy with parameters
sam deploy \
  --template-file deployment_config.yaml \
  --stack-name aquachain-data-processing \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=production \
    DataLakeBucket=aquachain-data-lake-123456789012
```

### Environment-Specific Configuration
```bash
# Development
sam deploy --parameter-overrides Environment=dev

# Staging  
sam deploy --parameter-overrides Environment=staging

# Production
sam deploy --parameter-overrides Environment=production
```

## Monitoring and Observability

### CloudWatch Metrics
- Function duration and memory usage
- Error rates and success rates
- Concurrent executions
- Dead letter queue message counts

### Custom Metrics
- Data processing latency
- ML inference accuracy
- Ledger verification success rate
- Audit trail completeness

### Alarms
- High error rates (>5% for 5 minutes)
- Long function duration (>30 seconds)
- DLQ message accumulation
- ML model loading failures

### X-Ray Tracing
All functions are instrumented with AWS X-Ray for distributed tracing:
- End-to-end request tracing
- Performance bottleneck identification
- Error root cause analysis

## Security

### Data Protection
- All data encrypted in transit (TLS 1.2+)
- All data encrypted at rest (KMS)
- Sensitive data masked in logs
- IAM least privilege access

### Cryptographic Security
- SHA-256 hashing for data integrity
- RSA-2048 KMS signing for non-repudiation
- Hash chaining for tamper detection
- Object Lock for immutability

### Access Control
- Function-specific IAM roles
- Resource-based policies
- VPC endpoints for private communication
- API Gateway authentication

## Testing

### Unit Tests
```bash
# Run unit tests for all functions
cd data_processing && python -m pytest tests/
cd ml_inference && python -m pytest tests/
cd ledger_service && python -m pytest tests/
cd audit_trail_processor && python -m pytest tests/
```

### Integration Tests
```bash
# Run integration tests
python integration_tests/test_data_pipeline.py
```

### Load Testing
```bash
# Simulate IoT device load
python load_tests/simulate_iot_devices.py --devices 1000 --duration 300
```

## Troubleshooting

### Common Issues

1. **ML Model Loading Failures**
   - Check S3 bucket permissions
   - Verify model file exists and is valid
   - Check Lambda memory allocation (increase to 1024MB)

2. **Ledger Sequence Conflicts**
   - Check DynamoDB conditional write failures
   - Verify sequence table initialization
   - Monitor concurrent execution limits

3. **Audit Trail Processing Delays**
   - Check DynamoDB Streams configuration
   - Verify S3 Object Lock settings
   - Monitor dead letter queue

4. **High Error Rates**
   - Check CloudWatch logs for specific errors
   - Verify IAM permissions
   - Check external service dependencies

### Debug Commands
```bash
# Check function logs
aws logs tail /aws/lambda/AquaChain-Data-Processing --follow

# Invoke function directly
aws lambda invoke \
  --function-name AquaChain-Data-Processing \
  --payload file://test_payload.json \
  response.json

# Check DLQ messages
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/aquachain-data-processing-dlq
```

## Performance Optimization

### Memory and Timeout Settings
- **Data Processing**: 512MB, 30s timeout
- **ML Inference**: 1024MB, 15s timeout  
- **Ledger Service**: 512MB, 30s timeout
- **Audit Processor**: 512MB, 60s timeout

### Concurrency Limits
- Data Processing: 100 concurrent executions (prevents runaway scaling)
- Other functions: Default AWS limits

### Caching Strategies
- ML models cached in Lambda memory
- DynamoDB connection pooling
- S3 client reuse across invocations

## Cost Optimization

### Lambda Pricing
- Use ARM-based Graviton2 processors where possible
- Right-size memory allocation based on profiling
- Optimize cold start times

### Storage Costs
- S3 Intelligent Tiering for data lake
- DynamoDB On-Demand for variable workloads
- Lifecycle policies for log retention

### Data Transfer
- Use VPC endpoints to avoid NAT gateway costs
- Compress large payloads
- Batch operations where possible

## Compliance and Audit

### Regulatory Requirements
- 7-year data retention (Object Lock)
- Tamper-evident logging (hash chaining)
- Independent audit capability (cross-account replication)
- Data integrity verification (cryptographic signatures)

### Audit Reports
```bash
# Generate compliance report
aws lambda invoke \
  --function-name AquaChain-Audit-Trail-Processor \
  --payload '{"operation": "generate_compliance_report", "startDate": "2025-01-01", "endDate": "2025-01-31"}' \
  compliance_report.json
```

## Support and Maintenance

### Regular Maintenance Tasks
- ML model retraining and deployment
- Log retention policy review
- Performance metric analysis
- Security patch updates

### Monitoring Checklist
- [ ] All functions executing successfully
- [ ] Error rates below 1%
- [ ] ML model accuracy above 85%
- [ ] Audit trail completeness 100%
- [ ] Cross-account replication working
- [ ] Object Lock retention policies active

For additional support, refer to the main AquaChain documentation or contact the development team.