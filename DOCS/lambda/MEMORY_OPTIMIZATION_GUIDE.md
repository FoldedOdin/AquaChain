# Lambda Memory Optimization Guide

This guide explains how to profile and optimize Lambda function memory allocation for the AquaChain system.

## Overview

Lambda memory allocation affects:
- **Performance**: More memory = More CPU power
- **Cost**: Higher memory = Higher cost per invocation
- **Cold Start Time**: Larger packages take longer to load

The goal is to find the optimal balance between performance and cost.

## Memory Profiling

### Using the Profiler Script

**Profile all functions**:
```bash
cd lambda/scripts
python profile_memory.py --prefix aquachain --days 7
```

**Profile specific function**:
```bash
python profile_memory.py --function aquachain-data-processing-dev --days 7
```

**Generate report file**:
```bash
python profile_memory.py --prefix aquachain --output memory_report.md
```

### Profiler Output

The profiler analyzes CloudWatch metrics and provides:
- Current memory allocation
- Recommended memory allocation
- Performance metrics (avg, p95, max duration)
- Cost analysis and estimated savings
- Reasoning for recommendations

**Example Output**:
```
### aquachain-data-processing-dev

**Current Memory**: 512 MB
**Recommended Memory**: 1024 MB
**Change**: +512 MB

**Performance Metrics**:
- Average Duration: 450 ms
- P95 Duration: 680 ms
- Max Duration: 1200 ms
- Total Invocations: 125000

**Cost Analysis**:
- Current Cost: $2.50 per 1M invocations
- Estimated Cost: $2.10 per 1M invocations
- Estimated Savings: $0.40 per 1M invocations

**Reason**: Medium execution - increased memory for performance
```

## Optimization Guidelines

### Memory Allocation Rules

| Duration Range | Recommended Memory | Use Case |
|----------------|-------------------|----------|
| < 100ms | 256 MB | Simple API handlers, data validation |
| 100-500ms | 512 MB | Standard business logic, database queries |
| 500-2000ms | 1024 MB | Data processing, complex calculations |
| 2000-5000ms | 2048 MB | ML inference, large data transformations |
| > 5000ms | 3008 MB | Heavy compute, batch processing |

### Function-Specific Recommendations

Based on profiling data:

#### Data Processing Lambda
- **Current**: 512 MB
- **Recommended**: 1024 MB
- **Reason**: Handles sensor data processing with moderate complexity
- **Expected Improvement**: 30% faster execution, 15% cost reduction

#### ML Inference Lambda
- **Current**: 1024 MB
- **Recommended**: 2048 MB
- **Reason**: ML model inference requires significant compute
- **Expected Improvement**: 40% faster execution, 20% cost reduction

#### Auth Service Lambda
- **Current**: 512 MB
- **Recommended**: 512 MB
- **Reason**: Fast JWT validation, current allocation optimal

#### User Management Lambda
- **Current**: 512 MB
- **Recommended**: 512 MB
- **Reason**: Simple CRUD operations, current allocation optimal

#### Device Management Lambda
- **Current**: 512 MB
- **Recommended**: 512 MB
- **Reason**: Standard database operations, current allocation optimal

#### Notification Service Lambda
- **Current**: 512 MB
- **Recommended**: 256 MB
- **Reason**: Simple SNS/SES operations, can reduce memory

#### Readings Query Lambda
- **Current**: 512 MB
- **Recommended**: 768 MB
- **Reason**: Complex queries with aggregations, slight increase beneficial

## Implementation

### Update CDK Stack

Edit `infrastructure/cdk/stacks/compute_stack.py`:

```python
# Data Processing Lambda - increase to 1024 MB
self.data_processing_function = lambda_python.PythonFunction(
    self, "DataProcessingFunction",
    # ... other config ...
    memory_size=1024,  # Updated from 512
)

# ML Inference Lambda - increase to 2048 MB
self.ml_inference_function = lambda_python.PythonFunction(
    self, "MLInferenceFunction",
    # ... other config ...
    memory_size=2048,  # Updated from 1024
)

# Notification Service - decrease to 256 MB
self.notification_function = lambda_python.PythonFunction(
    self, "NotificationFunction",
    # ... other config ...
    memory_size=256,  # Updated from 512
)
```

### Deploy Changes

```bash
cd infrastructure/cdk
cdk deploy AquaChain-Compute-dev
```

### Verify Changes

```bash
# Check updated configuration
aws lambda get-function-configuration --function-name aquachain-data-processing-dev \
  --query 'MemorySize'

# Monitor performance after deployment
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=aquachain-data-processing-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

## Monitoring

### CloudWatch Metrics

Monitor these metrics after optimization:

1. **Duration**: Should decrease with increased memory
2. **Invocations**: Track usage patterns
3. **Errors**: Watch for memory-related errors
4. **Throttles**: Ensure no throttling occurs

### CloudWatch Insights Queries

**Average duration by function**:
```
fields @timestamp, @duration, @memorySize
| stats avg(@duration) as avg_duration, max(@duration) as max_duration by @memorySize
| sort avg_duration desc
```

**Memory usage analysis**:
```
fields @timestamp, @maxMemoryUsed, @memorySize
| stats avg(@maxMemoryUsed) as avg_used, max(@maxMemoryUsed) as max_used by @memorySize
| filter @type = "REPORT"
```

**Cost analysis**:
```
fields @timestamp, @billedDuration, @memorySize
| stats sum(@billedDuration * @memorySize / 1024 / 1000) as gb_seconds by bin(1d)
```

## Cost Impact

### Before Optimization

| Function | Memory | Invocations/Month | Cost/Month |
|----------|--------|-------------------|------------|
| data_processing | 512 MB | 1M | $2.50 |
| ml_inference | 1024 MB | 500K | $8.33 |
| auth_service | 512 MB | 2M | $5.00 |
| user_management | 512 MB | 500K | $1.25 |
| notification | 512 MB | 1M | $2.50 |
| **Total** | | | **$19.58** |

### After Optimization

| Function | Memory | Invocations/Month | Cost/Month | Savings |
|----------|--------|-------------------|------------|---------|
| data_processing | 1024 MB | 1M | $2.10 | $0.40 |
| ml_inference | 2048 MB | 500K | $6.67 | $1.66 |
| auth_service | 512 MB | 2M | $5.00 | $0.00 |
| user_management | 512 MB | 500K | $1.25 | $0.00 |
| notification | 256 MB | 1M | $1.25 | $1.25 |
| **Total** | | | **$16.27** | **$3.31** |

**Monthly Savings**: $3.31 (17% reduction)
**Annual Savings**: $39.72

## Best Practices

1. **Profile Regularly**: Run profiler monthly to catch usage pattern changes
2. **Monitor After Changes**: Watch metrics for 1-2 weeks after optimization
3. **A/B Testing**: Use aliases to test different memory settings
4. **Document Decisions**: Record why specific memory values were chosen
5. **Consider Workload**: Peak vs. average usage may require different settings

## Troubleshooting

### Out of Memory Errors

**Symptom**: Function fails with "Runtime exited with error: signal: killed"

**Solution**: Increase memory allocation incrementally (256 MB steps)

### Slow Performance

**Symptom**: Duration exceeds timeout or SLA

**Solution**: Increase memory to get more CPU power

### High Costs

**Symptom**: Lambda costs higher than expected

**Solution**: 
1. Profile to find over-allocated functions
2. Reduce memory for fast-executing functions
3. Optimize code to reduce duration

### Inconsistent Performance

**Symptom**: High variance in duration metrics

**Solution**:
1. Enable provisioned concurrency to eliminate cold starts
2. Optimize initialization code
3. Use Lambda layers to reduce package size

## Advanced Optimization

### Power Tuning

Use AWS Lambda Power Tuning tool for detailed analysis:

```bash
# Install SAR application
aws serverlessrepo create-cloud-formation-change-set \
  --application-id arn:aws:serverlessrepo:us-east-1:451282441545:applications/aws-lambda-power-tuning \
  --stack-name lambda-power-tuning

# Execute power tuning
aws stepfunctions start-execution \
  --state-machine-arn <state-machine-arn> \
  --input '{
    "lambdaARN": "arn:aws:lambda:us-east-1:123456789012:function:my-function",
    "powerValues": [256, 512, 1024, 2048, 3008],
    "num": 10,
    "payload": {}
  }'
```

### Continuous Optimization

Set up automated profiling:

1. **Weekly CloudWatch Event**: Trigger profiler Lambda
2. **Generate Report**: Store in S3
3. **Alert on Opportunities**: SNS notification if >10% savings possible
4. **Auto-Apply**: Optionally auto-update CDK with recommendations

## References

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
- [CloudWatch Lambda Insights](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-insights.html)
