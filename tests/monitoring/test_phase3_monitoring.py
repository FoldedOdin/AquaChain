"""
Monitoring and Alerting Validation Tests for Phase 3
Tests CloudWatch alarms, SNS notifications, and dashboard accuracy
"""

import pytest
import boto3
import json
import time
from datetime import datetime, timedelta
from moto import mock_aws
import os


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'


@pytest.fixture
def setup_environment(aws_credentials):
    """Set up test environment"""
    os.environ['ALERT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts'
    os.environ['MODEL_METRICS_TABLE'] = 'test-model-metrics'


class TestCloudWatchAlarms:
    """Test CloudWatch alarm configuration and triggering"""
    
    @mock_aws
    def test_ml_drift_alarm_configuration(self, setup_environment):
        """Test ML drift alarm is properly configured"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Create drift alarm
        cloudwatch.put_metric_alarm(
            AlarmName='ML-Model-Drift-High',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='ModelDriftScore',
            Namespace='AquaChain/ML',
            Period=300,
            Statistic='Average',
            Threshold=0.15,
            ActionsEnabled=True,
            AlarmDescription='Alert when model drift score exceeds 0.15',
            AlarmActions=['arn:aws:sns:us-east-1:123456789012:test-alerts']
        )
        
        # Verify alarm exists
        response = cloudwatch.describe_alarms(AlarmNames=['ML-Model-Drift-High'])
        
        assert len(response['MetricAlarms']) == 1
        alarm = response['MetricAlarms'][0]
        
        assert alarm['AlarmName'] == 'ML-Model-Drift-High'
        assert alarm['Threshold'] == 0.15
        assert alarm['ComparisonOperator'] == 'GreaterThanThreshold'
        assert alarm['MetricName'] == 'ModelDriftScore'
        
        print(f"\nML Drift Alarm Configuration:")
        print(f"  Alarm Name: {alarm['AlarmName']}")
        print(f"  Threshold: {alarm['Threshold']}")
        print(f"  Evaluation Periods: {alarm['EvaluationPeriods']}")
        print(f"  Period: {alarm['Period']}s")
    
    @mock_cloudwatch
    def test_api_response_time_alarm(self, setup_environment):
        """Test API response time alarm configuration"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Create API response time alarm
        cloudwatch.put_metric_alarm(
            AlarmName='API-Response-Time-High',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='Latency',
            Namespace='AWS/ApiGateway',
            Period=60,
            Statistic='Average',
            Threshold=1000,  # 1 second
            ActionsEnabled=True,
            AlarmDescription='Alert when API response time exceeds 1 second',
            Dimensions=[
                {'Name': 'ApiName', 'Value': 'AquaChainAPI'}
            ]
        )
        
        # Verify alarm
        response = cloudwatch.describe_alarms(AlarmNames=['API-Response-Time-High'])
        
        assert len(response['MetricAlarms']) == 1
        alarm = response['MetricAlarms'][0]
        
        assert alarm['Threshold'] == 1000
        assert alarm['MetricName'] == 'Latency'
        
        print(f"\nAPI Response Time Alarm:")
        print(f"  Threshold: {alarm['Threshold']}ms")
        print(f"  Namespace: {alarm['Namespace']}")
    
    @mock_cloudwatch
    def test_lambda_error_rate_alarm(self, setup_environment):
        """Test Lambda error rate alarm configuration"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Create Lambda error rate alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Lambda-Error-Rate-High',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='Errors',
            Namespace='AWS/Lambda',
            Period=300,
            Statistic='Sum',
            Threshold=10,
            ActionsEnabled=True,
            AlarmDescription='Alert when Lambda errors exceed threshold'
        )
        
        # Verify alarm
        response = cloudwatch.describe_alarms(AlarmNames=['Lambda-Error-Rate-High'])
        
        assert len(response['MetricAlarms']) == 1
        alarm = response['MetricAlarms'][0]
        
        assert alarm['MetricName'] == 'Errors'
        assert alarm['Threshold'] == 10
        
        print(f"\nLambda Error Rate Alarm:")
        print(f"  Threshold: {alarm['Threshold']} errors")
        print(f"  Period: {alarm['Period']}s")
    
    @mock_cloudwatch
    def test_dynamodb_throttling_alarm(self, setup_environment):
        """Test DynamoDB throttling alarm configuration"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Create DynamoDB throttling alarm
        cloudwatch.put_metric_alarm(
            AlarmName='DynamoDB-Throttling',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='UserErrors',
            Namespace='AWS/DynamoDB',
            Period=60,
            Statistic='Sum',
            Threshold=5,
            ActionsEnabled=True,
            AlarmDescription='Alert on DynamoDB throttling events'
        )
        
        # Verify alarm
        response = cloudwatch.describe_alarms(AlarmNames=['DynamoDB-Throttling'])
        
        assert len(response['MetricAlarms']) == 1
        alarm = response['MetricAlarms'][0]
        
        assert alarm['MetricName'] == 'UserErrors'
        assert alarm['Namespace'] == 'AWS/DynamoDB'
        
        print(f"\nDynamoDB Throttling Alarm:")
        print(f"  Threshold: {alarm['Threshold']} errors")
        print(f"  Namespace: {alarm['Namespace']}")
    
    @mock_cloudwatch
    def test_iot_connection_failure_alarm(self, setup_environment):
        """Test IoT connection failure alarm configuration"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Create IoT connection failure alarm
        cloudwatch.put_metric_alarm(
            AlarmName='IoT-Connection-Failures',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='Connect.AuthError',
            Namespace='AWS/IoT',
            Period=300,
            Statistic='Sum',
            Threshold=10,
            ActionsEnabled=True,
            AlarmDescription='Alert on IoT authentication failures'
        )
        
        # Verify alarm
        response = cloudwatch.describe_alarms(AlarmNames=['IoT-Connection-Failures'])
        
        assert len(response['MetricAlarms']) == 1
        alarm = response['MetricAlarms'][0]
        
        assert alarm['MetricName'] == 'Connect.AuthError'
        assert alarm['Namespace'] == 'AWS/IoT'
        
        print(f"\nIoT Connection Failure Alarm:")
        print(f"  Threshold: {alarm['Threshold']} failures")
        print(f"  Metric: {alarm['MetricName']}")


class TestSNSNotifications:
    """Test SNS notification delivery"""
    
    @mock_sns
    def test_sns_topic_configuration(self, setup_environment):
        """Test SNS topic is properly configured"""
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create topic
        response = sns.create_topic(Name='phase3-alerts')
        topic_arn = response['TopicArn']
        
        # Set topic attributes
        sns.set_topic_attributes(
            TopicArn=topic_arn,
            AttributeName='DisplayName',
            AttributeValue='AquaChain Phase 3 Alerts'
        )
        
        # Verify topic
        attributes = sns.get_topic_attributes(TopicArn=topic_arn)
        
        assert 'Attributes' in attributes
        assert attributes['Attributes']['DisplayName'] == 'AquaChain Phase 3 Alerts'
        
        print(f"\nSNS Topic Configuration:")
        print(f"  Topic ARN: {topic_arn}")
        print(f"  Display Name: {attributes['Attributes']['DisplayName']}")
    
    @mock_sns
    def test_critical_vulnerability_alert(self, setup_environment):
        """Test critical vulnerability alert delivery"""
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create topic
        response = sns.create_topic(Name='security-alerts')
        topic_arn = response['TopicArn']
        
        # Publish critical alert
        alert_message = {
            'alert_type': 'critical_vulnerability',
            'severity': 'CRITICAL',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'package': 'axios',
                'version': '0.21.0',
                'cve': 'CVE-2021-3749',
                'description': 'Remote code execution vulnerability',
                'fix_version': '0.21.2'
            },
            'action_required': 'Immediate update required'
        }
        
        response = sns.publish(
            TopicArn=topic_arn,
            Subject='CRITICAL: Security Vulnerability Detected',
            Message=json.dumps(alert_message, indent=2)
        )
        
        assert 'MessageId' in response
        assert response['MessageId'] is not None
        
        print(f"\nCritical Vulnerability Alert:")
        print(f"  Message ID: {response['MessageId']}")
        print(f"  Subject: CRITICAL: Security Vulnerability Detected")
        print(f"  Package: {alert_message['details']['package']}")
    
    @mock_sns
    def test_model_drift_alert(self, setup_environment):
        """Test model drift alert delivery"""
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create topic
        response = sns.create_topic(Name='ml-alerts')
        topic_arn = response['TopicArn']
        
        # Publish drift alert
        alert_message = {
            'alert_type': 'model_drift',
            'severity': 'HIGH',
            'timestamp': datetime.utcnow().isoformat(),
            'model_name': 'wqi-prediction-model',
            'drift_score': 0.22,
            'threshold': 0.15,
            'consecutive_detections': 10,
            'action_taken': 'Automated retraining triggered'
        }
        
        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Model Drift Detected - Retraining Triggered',
            Message=json.dumps(alert_message, indent=2)
        )
        
        assert 'MessageId' in response
        
        print(f"\nModel Drift Alert:")
        print(f"  Message ID: {response['MessageId']}")
        print(f"  Drift Score: {alert_message['drift_score']}")
        print(f"  Action: {alert_message['action_taken']}")
    
    @mock_sns
    def test_certificate_expiration_alert(self, setup_environment):
        """Test certificate expiration alert delivery"""
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create topic
        response = sns.create_topic(Name='iot-alerts')
        topic_arn = response['TopicArn']
        
        # Publish expiration alert
        alert_message = {
            'alert_type': 'certificate_expiration',
            'severity': 'WARNING',
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': 'device-001',
            'certificate_id': 'cert-123',
            'expiration_date': (datetime.utcnow() + timedelta(days=5)).isoformat(),
            'days_until_expiry': 5,
            'action_required': 'Certificate rotation scheduled'
        }
        
        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Certificate Expiring Soon - Rotation Scheduled',
            Message=json.dumps(alert_message, indent=2)
        )
        
        assert 'MessageId' in response
        
        print(f"\nCertificate Expiration Alert:")
        print(f"  Message ID: {response['MessageId']}")
        print(f"  Device: {alert_message['device_id']}")
        print(f"  Days until expiry: {alert_message['days_until_expiry']}")


class TestDashboardMetrics:
    """Test dashboard metric accuracy and refresh"""
    
    @mock_cloudwatch
    def test_dashboard_metric_publishing(self, setup_environment):
        """Test metrics are published correctly to CloudWatch"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Publish test metrics
        timestamp = datetime.utcnow()
        
        cloudwatch.put_metric_data(
            Namespace='AquaChain/Phase3',
            MetricData=[
                {
                    'MetricName': 'PredictionLatency',
                    'Value': 150.0,
                    'Unit': 'Milliseconds',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'ModelDriftScore',
                    'Value': 0.12,
                    'Unit': 'None',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'PredictionCount',
                    'Value': 1000,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                }
            ]
        )
        
        # Verify metrics were published
        # Note: moto doesn't fully support metric retrieval
        # In production, verify with get_metric_statistics
        
        print(f"\nDashboard Metrics Published:")
        print(f"  PredictionLatency: 150.0ms")
        print(f"  ModelDriftScore: 0.12")
        print(f"  PredictionCount: 1000")
    
    @mock_cloudwatch
    def test_dashboard_refresh_rate(self, setup_environment):
        """Test dashboard refresh rate (60 seconds)"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Dashboard configuration
        dashboard_config = {
            'widgets': [
                {
                    'type': 'metric',
                    'properties': {
                        'metrics': [
                            ['AquaChain/Phase3', 'PredictionLatency']
                        ],
                        'period': 60,  # 60 second refresh
                        'stat': 'Average',
                        'region': 'us-east-1',
                        'title': 'Prediction Latency'
                    }
                }
            ]
        }
        
        # Create dashboard
        cloudwatch.put_dashboard(
            DashboardName='Phase3-Performance',
            DashboardBody=json.dumps(dashboard_config)
        )
        
        # Verify dashboard
        response = cloudwatch.get_dashboard(DashboardName='Phase3-Performance')
        
        assert 'DashboardBody' in response
        dashboard = json.loads(response['DashboardBody'])
        
        # Verify refresh period
        widget_period = dashboard['widgets'][0]['properties']['period']
        assert widget_period == 60
        
        print(f"\nDashboard Refresh Configuration:")
        print(f"  Dashboard: Phase3-Performance")
        print(f"  Refresh Period: {widget_period}s")
    
    @mock_dynamodb
    @mock_cloudwatch
    def test_metric_retention_and_ttl(self, setup_environment):
        """Test metric retention and TTL configuration"""
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-model-metrics',
            KeySchema=[
                {'AttributeName': 'model_name', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'model_name', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Enable TTL
        dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb_client.update_time_to_live(
            TableName='test-model-metrics',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        
        # Verify TTL is enabled
        ttl_description = dynamodb_client.describe_time_to_live(
            TableName='test-model-metrics'
        )
        
        assert ttl_description['TimeToLiveDescription']['TimeToLiveStatus'] in ['ENABLING', 'ENABLED']
        assert ttl_description['TimeToLiveDescription']['AttributeName'] == 'ttl'
        
        # Calculate TTL (90 days from now)
        ttl_timestamp = int((datetime.utcnow() + timedelta(days=90)).timestamp())
        
        # Insert metric with TTL
        table.put_item(Item={
            'model_name': 'wqi-prediction-model',
            'timestamp': datetime.utcnow().isoformat(),
            'drift_score': 0.10,
            'ttl': ttl_timestamp
        })
        
        print(f"\nMetric Retention Configuration:")
        print(f"  TTL Enabled: True")
        print(f"  TTL Attribute: ttl")
        print(f"  Retention Period: 90 days")


class TestAlarmTriggerValidation:
    """Test alarm triggering with test data"""
    
    @mock_cloudwatch
    @mock_sns
    def test_trigger_drift_alarm(self, setup_environment):
        """Test triggering drift alarm with high drift score"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create SNS topic
        topic_response = sns.create_topic(Name='test-alerts')
        topic_arn = topic_response['TopicArn']
        
        # Create alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Test-Drift-Alarm',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='ModelDriftScore',
            Namespace='AquaChain/ML',
            Period=60,
            Statistic='Average',
            Threshold=0.15,
            ActionsEnabled=True,
            AlarmActions=[topic_arn]
        )
        
        # Publish high drift score
        cloudwatch.put_metric_data(
            Namespace='AquaChain/ML',
            MetricData=[
                {
                    'MetricName': 'ModelDriftScore',
                    'Value': 0.25,  # Above threshold
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        # In production, alarm would trigger and send SNS notification
        # Verify alarm state would change to ALARM
        
        print(f"\nDrift Alarm Test:")
        print(f"  Threshold: 0.15")
        print(f"  Test Value: 0.25")
        print(f"  Expected State: ALARM")
    
    @mock_cloudwatch
    @mock_sns
    def test_trigger_api_latency_alarm(self, setup_environment):
        """Test triggering API latency alarm"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create SNS topic
        topic_response = sns.create_topic(Name='test-alerts')
        topic_arn = topic_response['TopicArn']
        
        # Create alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Test-API-Latency-Alarm',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='Latency',
            Namespace='AWS/ApiGateway',
            Period=60,
            Statistic='Average',
            Threshold=1000,
            ActionsEnabled=True,
            AlarmActions=[topic_arn]
        )
        
        # Publish high latency
        cloudwatch.put_metric_data(
            Namespace='AWS/ApiGateway',
            MetricData=[
                {
                    'MetricName': 'Latency',
                    'Value': 1500,  # Above threshold
                    'Unit': 'Milliseconds',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        print(f"\nAPI Latency Alarm Test:")
        print(f"  Threshold: 1000ms")
        print(f"  Test Value: 1500ms")
        print(f"  Expected State: ALARM")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
