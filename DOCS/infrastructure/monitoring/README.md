# AquaChain Monitoring, Logging, and Observability

This directory contains the complete monitoring infrastructure for the AquaChain water quality monitoring system. The monitoring setup implements comprehensive observability with CloudWatch, X-Ray distributed tracing, SLI/SLO monitoring, and PagerDuty integration.

## 🎯 Overview

The AquaChain monitoring system provides:

- **Real-time Monitoring**: CloudWatch dashboards and custom metrics
- **Distributed Tracing**: AWS X-Ray for end-to-end request tracking
- **SLI/SLO Monitoring**: Service Level Indicators and Objectives with error budget tracking
- **Alerting**: Multi-channel notifications with PagerDuty integration
- **Performance Monitoring**: Application performance monitoring with baselines
- **Compliance**: Audit trail and compliance reporting capabilities

## 📊 Key Metrics and SLOs

### Service Level Objectives (SLOs)

| SLO | Target | Description |
|-----|--------|-------------|
| Alert Latency | 95% under 30s | Water quality alerts delivered within 30 seconds |
| Data Ingestion Availability | 99.5% | IoT sensor data successfully processed |
| API Response Time | 99% under 2s | API requests completed within 2 seconds |
| System Uptime | 99.5% | Overall system availability |
| Technician Assignment Success | 98% | Service requests successfully assigned |
| ML Inference Accuracy | 85% | High confidence ML predictions |

### Critical Metrics

- **Alert Latency**: End-to-end time from sensor reading to notification delivery
- **Device Uptime**: Percentage of IoT devices reporting within expected intervals
- **Error Rate**: System-wide error rate across all components
- **Throughput**: Messages per second, requests per second
- **End-to-End Latency**: Complete request flow timing

## 🏗️ Architecture Components

### 1. CloudWatch Monitoring (`cloudwatch_setup.py`)

**Features:**
- Custom metrics for business KPIs
- System health dashboards
- Alert latency monitoring
- Automated alerting with SNS integration
- Log group management with retention policies

**Dashboards:**
- `AquaChain-SystemHealth`: Overall system metrics
- `AquaChain-AlertLatency`: Alert performance monitoring
- `AquaChain-Monitoring-Overview`: Executive summary

### 2. X-Ray Distributed Tracing (`xray_setup.py`)

**Features:**
- End-to-end request tracing
- Lambda function tracing
- API Gateway tracing
- Performance bottleneck identification
- Service map visualization

**Tracing Utilities (`lambda/shared/xray_utils.py`):**
- `@trace_lambda_handler`: Automatic Lambda tracing
- `@trace_critical_path`: Critical operation tracing
- `@trace_data_flow`: Data pipeline tracing
- `@trace_external_call`: External service call tracing

### 3. SLI/SLO Monitoring (`sli_slo_setup.py`)

**Features:**
- Service Level Indicator definitions
- Error budget calculation and tracking
- SLO compliance monitoring
- Automated error budget alerting
- Trend analysis and reporting

**SLO Calculator (`lambda/slo_calculator/`):**
- Automated SLI calculation
- Error budget consumption tracking
- Compliance reporting
- Scheduled execution via CloudWatch Events

### 4. PagerDuty Integration (`pagerduty_integration.py`)

**Features:**
- Incident creation and management
- Alert escalation workflows
- Maintenance window management
- Custom incident handlers for AquaChain scenarios

**Lambda Integration (`lambda/pagerduty_integration/`):**
- CloudWatch alarm to PagerDuty incident mapping
- Contextual incident details
- Automated incident resolution

## 🚀 Setup and Deployment

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Python 3.11+ installed
3. Required Python packages: `boto3`, `requests`
4. PagerDuty integration key (optional)

### Quick Setup

```bash
# Run complete monitoring setup
cd infrastructure/monitoring
python setup_complete_monitoring.py --region us-east-1 --pagerduty-key YOUR_KEY

# Validate setup
python setup_complete_monitoring.py --validate
```

### Manual Setup

1. **CloudWatch Monitoring:**
```python
from cloudwatch_setup import CloudWatchMonitoringSetup
monitoring = CloudWatchMonitoringSetup()
result = monitoring.setup_complete_monitoring()
```

2. **X-Ray Tracing:**
```python
from xray_setup import XRaySetup
xray = XRaySetup()
result = xray.setup_complete_xray_tracing()
```

3. **SLI/SLO Monitoring:**
```python
from sli_slo_setup import setup_complete_sli_slo_monitoring
result = setup_complete_sli_slo_monitoring()
```

### Lambda Function Deployment

Deploy the monitoring Lambda functions:

```bash
# SLO Calculator (scheduled execution)
cd lambda/slo_calculator
zip -r slo_calculator.zip .
aws lambda create-function --function-name aquachain-slo-calculator --runtime python3.11 --zip-file fileb://slo_calculator.zip

# PagerDuty Integration (SNS triggered)
cd lambda/pagerduty_integration
zip -r pagerduty_integration.zip .
aws lambda create-function --function-name aquachain-pagerduty-integration --runtime python3.11 --zip-file fileb://pagerduty_integration.zip
```

## 📈 Dashboards

### System Health Dashboard
- Real-time system metrics
- Component health status
- Error rates and latencies
- Business KPI tracking

### Alert Latency Dashboard
- Alert delivery performance
- SLA compliance tracking
- Latency distribution analysis
- Notification success rates

### Performance Dashboard
- End-to-end latency metrics
- Component performance breakdown
- Throughput and reliability metrics
- X-Ray trace analysis

### SLO Dashboard
- SLO compliance tracking
- Error budget consumption
- Burn rate monitoring
- Trend analysis

## 🚨 Alerting Strategy

### Alert Severity Levels

1. **Critical (P1)**: Immediate response required
   - Alert latency > 30 seconds
   - Data ingestion error rate > 5%
   - System uptime < 99.5%

2. **High (P2)**: Response within 1 hour
   - Error budget 90% consumed
   - Technician assignment failures
   - API response time degradation

3. **Medium (P3)**: Response within 4 hours
   - Error budget 50% consumed
   - Device uptime issues
   - Performance degradation

### Notification Channels

- **PagerDuty**: Critical and high priority alerts
- **SNS/Email**: All alert types
- **SMS**: Critical alerts only
- **Slack**: Operational notifications (if configured)

## 🔧 Configuration

### Environment Variables

```bash
# Lambda Functions
PAGERDUTY_INTEGRATION_KEY=your_integration_key
AWS_REGION=us-east-1
LOG_LEVEL=INFO

# CloudWatch
CUSTOM_METRICS_NAMESPACE=AquaChain
DASHBOARD_REFRESH_INTERVAL=300
ALARM_EVALUATION_PERIODS=2

# X-Ray
XRAY_SAMPLING_RATE=0.1
XRAY_TRACE_ID_HEADER=X-Amzn-Trace-Id
```

### SNS Topics

- `aquachain-critical-system-alerts`: P1 incidents
- `aquachain-sla-breach-alerts`: SLA violations
- `aquachain-operational-alerts`: General notifications
- `aquachain-slo-alerts`: SLO and error budget alerts

## 📊 Metrics Reference

### Custom Metrics

#### AquaChain/DataIngestion
- `DeviceDataReceived`: Count of IoT messages received
- `ProcessingLatency`: Time to process sensor data
- `ValidationErrors`: Data validation failures
- `DuplicateReadings`: Duplicate message detection

#### AquaChain/Alerts
- `AlertLatency`: Time from event to notification
- `CriticalAlerts`: Count of critical water quality alerts
- `NotificationDeliveryRate`: Success rate of notifications
- `AlertVolumePerHour`: Alert frequency

#### AquaChain/ServiceRequests
- `AssignmentLatency`: Time to assign technician
- `TechnicianUtilization`: Technician workload
- `ServiceCompletionRate`: Successful service completion
- `CustomerSatisfactionScore`: Average customer rating

#### AquaChain/SystemHealth
- `DeviceUptime`: Percentage of devices online
- `APIResponseTime`: API latency metrics
- `ErrorRate`: System-wide error percentage
- `ThroughputPerSecond`: System throughput

#### AquaChain/SLO
- `{slo_name}_compliance`: SLO compliance percentage
- `{slo_name}_error_budget_remaining`: Error budget remaining
- `{slo_name}_burn_rate`: Error budget consumption rate
- `overall_slo_compliance`: System-wide SLO compliance

## 🔍 Troubleshooting

### Common Issues

1. **Missing Metrics**
   - Check Lambda function permissions
   - Verify CloudWatch namespace configuration
   - Ensure metric publishing code is deployed

2. **X-Ray Traces Not Appearing**
   - Verify X-Ray tracing is enabled on Lambda functions
   - Check sampling rule configuration
   - Ensure X-Ray SDK is properly imported

3. **PagerDuty Incidents Not Created**
   - Verify integration key configuration
   - Check SNS topic subscriptions
   - Review Lambda function logs

4. **Dashboard Not Loading**
   - Check CloudWatch permissions
   - Verify metric names and namespaces
   - Review dashboard JSON syntax

### Debugging Commands

```bash
# Check CloudWatch metrics
aws cloudwatch list-metrics --namespace AquaChain/SystemHealth

# View X-Ray traces
aws xray get-trace-summaries --time-range-type TimeRangeByStartTime --start-time 2025-10-20T00:00:00Z --end-time 2025-10-20T23:59:59Z

# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/aquachain-

# Test PagerDuty integration
curl -X POST https://events.pagerduty.com/v2/enqueue -H "Content-Type: application/json" -d '{"routing_key":"YOUR_KEY","event_action":"trigger","payload":{"summary":"Test"}}'
```

## 📚 Additional Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [AWS X-Ray Documentation](https://docs.aws.amazon.com/xray/)
- [PagerDuty API Documentation](https://developer.pagerduty.com/)
- [SLI/SLO Best Practices](https://sre.google/sre-book/service-level-objectives/)

## 🤝 Contributing

When adding new monitoring components:

1. Follow the established naming conventions
2. Add appropriate documentation
3. Include error handling and logging
4. Create corresponding dashboards and alerts
5. Update this README with new metrics and features

## 📝 License

This monitoring infrastructure is part of the AquaChain system and follows the same licensing terms.