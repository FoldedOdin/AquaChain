# Performance Dashboard Guide

## Overview

The AquaChain Performance Dashboard provides centralized monitoring of all system components through CloudWatch. This guide explains all metrics, alarm thresholds, and troubleshooting procedures.

## Dashboard Access

**Dashboard Name:** `AquaChain-Performance-{environment}`

**Access:**
1. Open AWS CloudWatch Console
2. Navigate to Dashboards
3. Select `AquaChain-Performance-dev` or `AquaChain-Performance-prod`

**Auto-Refresh:** Dashboard automatically refreshes every 60 seconds

---

## Metrics Reference

### API Gateway Metrics

#### Response Times
- **p50 (Median)**: Half of requests complete faster than this time
- **p95**: 95% of requests complete faster than this time
- **p99**: 99% of requests complete faster than this time

**Normal Range:**
- p50: < 200ms
- p95: < 500ms
- p99: < 1000ms

**What to Monitor:**
- Sudden spikes indicate performance degradation
- Gradual increases suggest capacity issues

#### Request Count & Errors
- **Total Requests**: Number of API calls per period
- **4XX Errors**: Client errors (bad requests, unauthorized, etc.)
- **5XX Errors**: Server errors (internal errors, timeouts)

**Normal Range:**
- 4XX: < 5% of total requests
- 5XX: < 0.1% of total requests

#### Throttling Events
- **Throttled Requests**: Requests rejected due to rate limiting

**Normal Range:** 0 throttled requests

#### Error Rate
- **Calculated**: (4XX + 5XX) / Total Requests * 100

**Normal Range:** < 2%

---

### Lambda Function Metrics

#### Duration
- **Average Duration**: Mean execution time across all invocations
- **p95 Duration**: 95th percentile execution time
- **Max Duration**: Longest execution time in period

**Normal Range:**
- Average: < 500ms
- p95: < 1000ms
- Max: < 3000ms

**What to Monitor:**
- Approaching timeout limits (typically 30s)
- Sudden increases in duration

#### Errors & Throttles
- **Errors**: Failed Lambda invocations
- **Throttles**: Invocations rejected due to concurrency limits
- **Concurrent Executions**: Number of functions running simultaneously

**Normal Range:**
- Errors: < 1% of invocations
- Throttles: 0
- Concurrent Executions: < 80% of reserved concurrency

#### Invocations & Error Rate
- **Total Invocations**: Number of function executions
- **Error Rate**: Percentage of failed invocations

**Normal Range:** Error rate < 1%

#### Cold Starts
- **Cold Starts**: Number of Lambda cold starts (first invocation or after idle period)

**Normal Range:** < 10% of total invocations

**Optimization Tips:**
- Use provisioned concurrency for critical functions
- Optimize function initialization code
- Consider keeping functions warm with scheduled pings

---

### DynamoDB Metrics

#### Capacity Utilization
- **Read Capacity Consumed**: Read capacity units used
- **Write Capacity Consumed**: Write capacity units used

**Normal Range:** < 80% of provisioned capacity

**What to Monitor:**
- Approaching provisioned limits
- Consistent high utilization (consider auto-scaling)

#### Throttled Requests
- **Read Throttles**: Read requests rejected due to capacity limits
- **Write Throttles**: Write requests rejected due to capacity limits

**Normal Range:** 0 throttled requests

**If Throttling Occurs:**
1. Check capacity utilization
2. Enable auto-scaling if not already enabled
3. Review query patterns for optimization
4. Consider on-demand billing mode

#### Query Latency
- **GetItem Latency**: Time to retrieve single item
- **PutItem Latency**: Time to write single item
- **Query Latency**: Time to execute query operation

**Normal Range:**
- GetItem: < 10ms
- PutItem: < 20ms
- Query: < 50ms

#### System Errors
- **System Errors**: DynamoDB service errors (not throttling)

**Normal Range:** 0 system errors

---

### IoT Core Metrics

#### Device Connections
- **Successful Connections**: Devices successfully connected
- **Connection Errors**: Failed connection attempts
- **Authentication Failures**: Certificate or credential failures

**Normal Range:**
- Success rate: > 95%
- Auth failures: < 1% of attempts

**If Auth Failures Increase:**
1. Check certificate expiration dates
2. Verify device credentials
3. Review IoT policy permissions
4. Check for certificate rotation issues

#### Connected Devices
- **Active Devices**: Current number of connected devices

**What to Monitor:**
- Sudden drops indicate connectivity issues
- Gradual decline suggests device failures

#### Message Rates
- **Messages Published**: Messages sent from devices to AWS
- **Messages Delivered**: Messages sent from AWS to devices

**Normal Range:** Consistent with expected device behavior

**What to Monitor:**
- Sudden drops in publish rate (device issues)
- Message delivery failures (connectivity issues)

#### Rule Execution
- **Throttled Messages**: Messages throttled by IoT rules
- **Rule Not Found**: Messages with no matching rule

**Normal Range:** 0 throttled or unmatched messages

---

### ML Model Metrics

#### Prediction Latency
- **Average Latency**: Mean time to generate prediction
- **p95 Latency**: 95th percentile prediction time
- **p99 Latency**: 99th percentile prediction time

**Normal Range:**
- Average: < 200ms
- p95: < 300ms
- p99: < 500ms

**Target:** < 50ms overhead from monitoring

#### Drift Score
- **Drift Score**: Measure of model performance degradation (0-1 scale)

**Normal Range:** < 0.15

**Drift Score Interpretation:**
- 0.00 - 0.10: Normal operation
- 0.10 - 0.15: Monitor closely
- 0.15+: Retraining recommended

**If Drift Detected:**
1. Review recent prediction patterns
2. Check training data quality
3. Trigger manual retraining if needed
4. Investigate data distribution changes

#### Prediction Count
- **Total Predictions**: Number of predictions made

**What to Monitor:**
- Sudden drops indicate service issues
- Unexpected spikes may indicate anomalies

#### Prediction Confidence
- **Average Confidence**: Mean confidence score across predictions
- **Min Confidence**: Lowest confidence score in period

**Normal Range:**
- Average: > 0.80 (80%)
- Min: > 0.60 (60%)

**If Confidence Drops:**
1. Review input data quality
2. Check for edge cases
3. Consider model retraining
4. Investigate feature drift

#### Error Rate
- **Error Rate**: Percentage of failed predictions

**Normal Range:** < 0.5%

---

## CloudWatch Alarms

### API Response Time Alarm
**Threshold:** p95 > 1000ms (1 second)  
**Evaluation:** 2 consecutive periods

**Triggered When:** API response times are consistently slow

**Actions:**
1. Check Lambda function performance
2. Review DynamoDB query latency
3. Investigate external API calls
4. Check for throttling or capacity issues

### Lambda Error Rate Alarm
**Threshold:** Error rate > 1%  
**Evaluation:** 2 consecutive periods

**Triggered When:** Lambda functions are failing frequently

**Actions:**
1. Check CloudWatch Logs for error details
2. Review recent code deployments
3. Verify IAM permissions
4. Check external service dependencies

### DynamoDB Throttling Alarm
**Threshold:** > 5 throttle events  
**Evaluation:** 1 period

**Triggered When:** DynamoDB is rejecting requests due to capacity

**Actions:**
1. Enable auto-scaling if not configured
2. Increase provisioned capacity temporarily
3. Review query patterns for optimization
4. Consider switching to on-demand mode

### IoT Connection Failures Alarm
**Threshold:** > 10 connection failures  
**Evaluation:** 2 consecutive periods

**Triggered When:** Devices are failing to connect

**Actions:**
1. Check certificate expiration
2. Verify IoT policy permissions
3. Review device logs
4. Check network connectivity
5. Investigate certificate rotation issues

### ML Drift Score Alarm
**Threshold:** Drift score > 0.15  
**Evaluation:** 2 out of 3 periods

**Triggered When:** Model performance is degrading

**Actions:**
1. Review drift detection logs
2. Analyze recent prediction patterns
3. Trigger model retraining
4. Investigate data distribution changes
5. Update baseline metrics if needed

### ML Low Confidence Alarm
**Threshold:** Average confidence < 0.70 (70%)  
**Evaluation:** 2 out of 3 periods

**Triggered When:** Model predictions have low confidence

**Actions:**
1. Review input data quality
2. Check for missing features
3. Investigate edge cases
4. Consider model retraining
5. Review feature engineering

---

## Troubleshooting Guide

### High API Latency

**Symptoms:**
- p95 latency > 1 second
- User complaints about slow responses

**Investigation Steps:**
1. Check Lambda duration metrics
2. Review DynamoDB query latency
3. Check for throttling events
4. Review API Gateway logs
5. Investigate cold starts

**Common Causes:**
- Lambda cold starts
- Inefficient database queries
- External API timeouts
- Insufficient capacity

**Solutions:**
- Enable Lambda provisioned concurrency
- Optimize database queries
- Add caching layer
- Increase capacity limits

### Lambda Errors

**Symptoms:**
- Error rate > 1%
- Failed invocations in logs

**Investigation Steps:**
1. Check CloudWatch Logs for stack traces
2. Review recent deployments
3. Verify IAM permissions
4. Check environment variables
5. Test with sample inputs

**Common Causes:**
- Code bugs
- Missing permissions
- Invalid input data
- External service failures
- Timeout issues

**Solutions:**
- Roll back to previous version
- Fix code bugs
- Update IAM policies
- Add input validation
- Increase timeout limits

### DynamoDB Throttling

**Symptoms:**
- Throttled requests > 0
- ProvisionedThroughputExceededException errors

**Investigation Steps:**
1. Check capacity utilization
2. Review query patterns
3. Check for hot partitions
4. Analyze access patterns

**Common Causes:**
- Insufficient provisioned capacity
- Hot partition keys
- Burst traffic
- Inefficient queries

**Solutions:**
- Enable auto-scaling
- Increase provisioned capacity
- Redesign partition keys
- Implement caching
- Use batch operations

### IoT Connection Issues

**Symptoms:**
- Connection failures > 10
- Devices offline
- Authentication errors

**Investigation Steps:**
1. Check certificate expiration
2. Review IoT policies
3. Check device logs
4. Verify network connectivity
5. Test with AWS IoT console

**Common Causes:**
- Expired certificates
- Invalid credentials
- Network issues
- Policy restrictions
- Certificate rotation failures

**Solutions:**
- Rotate certificates
- Update device credentials
- Fix network configuration
- Update IoT policies
- Verify certificate provisioning

### ML Model Drift

**Symptoms:**
- Drift score > 0.15
- Prediction accuracy declining
- Unusual prediction patterns

**Investigation Steps:**
1. Review drift detection logs
2. Analyze prediction distribution
3. Compare to baseline metrics
4. Check training data quality
5. Review feature values

**Common Causes:**
- Data distribution changes
- Seasonal variations
- New edge cases
- Feature drift
- Outdated training data

**Solutions:**
- Trigger model retraining
- Update baseline metrics
- Collect new training data
- Review feature engineering
- Adjust drift threshold

---

## Performance Optimization Recommendations

### API Gateway
- Enable caching for frequently accessed endpoints
- Use request validation to reject invalid requests early
- Implement throttling to protect backend services
- Use API Gateway custom domain with CloudFront

### Lambda Functions
- Optimize cold start times:
  - Minimize deployment package size
  - Use Lambda layers for dependencies
  - Enable provisioned concurrency for critical functions
- Right-size memory allocation
- Use connection pooling for database connections
- Implement circuit breakers for external services

### DynamoDB
- Enable auto-scaling for capacity management
- Use DynamoDB Accelerator (DAX) for caching
- Optimize partition key design
- Use batch operations where possible
- Enable point-in-time recovery

### IoT Core
- Implement exponential backoff for reconnections
- Use persistent sessions to reduce connection overhead
- Batch messages when possible
- Monitor certificate expiration proactively
- Use IoT Device Defender for security monitoring

### ML Models
- Monitor drift continuously
- Automate retraining workflows
- Implement A/B testing for model updates
- Use SageMaker endpoints with auto-scaling
- Cache predictions for repeated inputs

---

## Alarm Threshold Rationale

### API Response Time: 1 second
- Based on user experience research
- Allows for network latency
- Provides buffer before user frustration

### Lambda Error Rate: 1%
- Industry standard for acceptable error rate
- Allows for transient failures
- Triggers investigation before user impact

### DynamoDB Throttling: 5 events
- Indicates capacity planning issue
- Low threshold for early detection
- Prevents cascading failures

### IoT Connection Failures: 10 failures
- Accounts for transient network issues
- Indicates systematic problem
- Balances sensitivity with noise

### ML Drift Score: 0.15
- Based on statistical significance
- Provides early warning
- Allows time for retraining

---

## Dashboard Maintenance

### Regular Reviews
- **Daily:** Check for active alarms
- **Weekly:** Review trend patterns
- **Monthly:** Analyze capacity utilization
- **Quarterly:** Update alarm thresholds

### Metric Retention
- **High-resolution metrics:** 3 hours
- **1-minute metrics:** 15 days
- **5-minute metrics:** 63 days
- **1-hour metrics:** 455 days

### Dashboard Updates
- Add new metrics as features are deployed
- Remove deprecated metrics
- Adjust alarm thresholds based on historical data
- Update documentation with lessons learned

---

## Additional Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [API Gateway Metrics](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html)
- [Lambda Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)
- [DynamoDB Metrics](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/metrics-dimensions.html)
- [IoT Core Metrics](https://docs.aws.amazon.com/iot/latest/developerguide/metrics_dimensions.html)

---

**Last Updated:** October 25, 2025  
**Version:** 1.0  
**Maintained By:** DevOps Team
