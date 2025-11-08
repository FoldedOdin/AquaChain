# Training Data Validation - Quick Start Guide

## Overview

Automated validation system for ML training data with S3 triggers, quality checks, and CloudWatch monitoring.

## Quick Setup

### 1. Deploy Infrastructure

```bash
cd infrastructure/cdk
cdk deploy AquaChainPhase3InfrastructureStack
cdk deploy TrainingDataValidationStack
```

### 2. Upload Training Data

```bash
# Upload CSV file
aws s3 cp training_data.csv s3://aquachain-ml-training-data/training-data/

# Upload Parquet file
aws s3 cp training_data.parquet s3://aquachain-ml-training-data/training-data/
```

### 3. Check Validation Results

```bash
# View CloudWatch logs
aws logs tail /aws/lambda/aquachain-data-validation --follow

# Check CloudWatch dashboard
# https://console.aws.amazon.com/cloudwatch/home#dashboards:name=aquachain-data-validation
```

## Data Format Requirements

### Required Columns

Water quality features (any subset):
- `pH` - pH level (0-14)
- `turbidity` - Turbidity in NTU (0-100)
- `tds` - Total Dissolved Solids in mg/L (0-2000)
- `temperature` - Temperature in Celsius (0-50)
- `humidity` - Humidity percentage (0-100)

Label column (last column):
- `wqi` - Water Quality Index (0-100)
- `anomaly_label` - Anomaly classification (0=normal, 1=fault, 2=contamination)

### Example CSV

```csv
pH,turbidity,tds,temperature,humidity,wqi
7.0,1.5,250,25,60,85
7.2,2.0,280,26,65,88
6.8,1.8,300,24,55,82
```

## Validation Checks

### Automatic Checks

1. **NaN Detection** - Fails if any NaN values found
2. **Infinite Detection** - Fails if any infinite values found
3. **Range Validation** - Warns if values outside expected ranges
4. **Label Distribution** - Fails if any class < 5% representation
5. **Distribution Analysis** - Warns on high skewness/kurtosis

### Expected Ranges

| Feature | Physical Range | Recommended Range |
|---------|---------------|-------------------|
| pH | 0.0 - 14.0 | 6.5 - 8.5 |
| turbidity | 0.0 - 100.0 | 0.0 - 5.0 |
| tds | 0.0 - 2000.0 | 50.0 - 500.0 |
| temperature | 0.0 - 50.0 | 15.0 - 30.0 |
| humidity | 0.0 - 100.0 | 30.0 - 70.0 |

## Validation Results

### Success Response

```json
{
  "validation_id": "validation_1729900000",
  "passed": true,
  "total_rows": 10000,
  "errors": [],
  "warnings": []
}
```

### Failure Response

```json
{
  "validation_id": "validation_1729900000",
  "passed": false,
  "total_rows": 10000,
  "errors": [
    "Found 15 NaN values in 2 features",
    "2 classes below 5% threshold"
  ],
  "warnings": [
    "pH: 5 values below 0, 3 values above 14"
  ],
  "recommendations": [
    "Collect 45 more samples for class 2"
  ]
}
```

## Manual Validation

### Python Example

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Validate data
response = lambda_client.invoke(
    FunctionName='aquachain-data-validation',
    Payload=json.dumps({
        'action': 'validate',
        'bucket': 'aquachain-ml-training-data',
        'key': 'training-data/my_data.csv',
        'feature_columns': ['pH', 'turbidity', 'tds'],
        'label_column': 'wqi'
    })
)

result = json.loads(response['Payload'].read())
print(f"Validation {'PASSED' if result['passed'] else 'FAILED'}")
```

### CLI Example

```bash
aws lambda invoke \
  --function-name aquachain-data-validation \
  --payload '{"action":"validate","bucket":"aquachain-ml-training-data","key":"training-data/test.csv","feature_columns":["pH","turbidity"],"label_column":"wqi"}' \
  response.json

cat response.json | jq .
```

## Monitoring

### CloudWatch Metrics

View metrics in CloudWatch console:
- Namespace: `AquaChain/DataValidation`
- Metrics: ValidationSuccess, ValidationFailure, RowsValidated

### SNS Alerts

Subscribe to alerts:
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:aquachain-phase3-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Query Validation History

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aquachain-data-validation')

# Get recent validations
response = table.query(
    IndexName='TimestampIndex',
    KeyConditionExpression='passed = :passed',
    ExpressionAttributeValues={':passed': 'false'},
    ScanIndexForward=False,
    Limit=10
)

for item in response['Items']:
    print(f"{item['validation_id']}: {item['timestamp']}")
    print(f"  Errors: {item['errors']}")
```

## Troubleshooting

### Validation Not Triggering

1. Check S3 bucket notification configuration:
```bash
aws s3api get-bucket-notification-configuration \
  --bucket aquachain-ml-training-data
```

2. Verify Lambda permissions:
```bash
aws lambda get-policy \
  --function-name aquachain-data-validation
```

### High Failure Rate

1. Check CloudWatch logs for error patterns
2. Review validation results in DynamoDB
3. Verify data format matches requirements
4. Check for data quality issues at source

### Performance Issues

1. Monitor Lambda duration in CloudWatch
2. Check memory usage (increase if needed)
3. Consider batch processing for large files
4. Enable Lambda reserved concurrency if needed

## Testing

### Run Unit Tests

```bash
cd lambda/ml_training
python -m pytest test_training_data_validator.py -v
```

### Test with Sample Data

```python
import pandas as pd
import numpy as np

# Generate test data
data = pd.DataFrame({
    'pH': np.random.normal(7.0, 0.5, 1000),
    'turbidity': np.random.lognormal(0, 0.5, 1000),
    'tds': np.random.normal(300, 100, 1000),
    'wqi': np.random.uniform(50, 100, 1000)
})

# Save and upload
data.to_csv('test_data.csv', index=False)

# Upload to S3
import boto3
s3 = boto3.client('s3')
s3.upload_file('test_data.csv', 
               'aquachain-ml-training-data', 
               'training-data/test_data.csv')
```

## Best Practices

1. **Data Preparation:**
   - Clean data before upload
   - Remove duplicates
   - Handle missing values appropriately

2. **File Organization:**
   - Use descriptive filenames with timestamps
   - Organize by date or experiment
   - Keep raw and processed data separate

3. **Monitoring:**
   - Set up SNS email alerts
   - Review validation dashboard weekly
   - Track validation trends over time

4. **Error Handling:**
   - Fix data quality issues at source
   - Document validation failures
   - Iterate on data collection process

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review validation results in DynamoDB
3. Consult IMPLEMENTATION_SUMMARY.md for details
4. Contact ML team for data quality guidance

---

**Quick Links:**
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home#dashboards:name=aquachain-data-validation)
- [Lambda Function](https://console.aws.amazon.com/lambda/home#/functions/aquachain-data-validation)
- [S3 Bucket](https://console.aws.amazon.com/s3/buckets/aquachain-ml-training-data)

