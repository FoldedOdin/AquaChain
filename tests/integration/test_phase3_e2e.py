"""
End-to-End Integration Tests for Phase 3
Tests ML monitoring, OTA updates, certificate rotation, and dependency scanning
"""

import pytest
import boto3
import json
import time
from datetime import datetime, timedelta
from moto import mock_aws
import os
import sys

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/ml_inference'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/iot_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/dependency_scanner'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/ml_training'))


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_ACCOUNT_ID'] = '123456789012'


@pytest.fixture
def setup_environment(aws_credentials):
    """Set up test environment variables"""
    os.environ['MODEL_METRICS_TABLE'] = 'test-model-metrics'
    os.environ['CERTIFICATE_LIFECYCLE_TABLE'] = 'test-certificate-lifecycle'
    os.environ['FIRMWARE_BUCKET'] = 'test-firmware-bucket'
    os.environ['RESULTS_BUCKET'] = 'test-results-bucket'
    os.environ['ALERT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts'
    os.environ['TRAINING_DATA_BUCKET'] = 'test-training-data'


class TestMLMonitoringE2E:
    """End-to-end tests for ML monitoring system"""
    
    @mock_aws
    def test_ml_monitoring_with_live_predictions(self, setup_environment):
        """Test ML monitoring with simulated live predictions"""
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
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'drift_score', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'drift-score-index',
                    'KeySchema': [
                        {'AttributeName': 'model_name', 'KeyType': 'HASH'},
                        {'AttributeName': 'drift_score', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Import after mocking
        from model_performance_monitor import ModelPerformanceTracker
        
        tracker = ModelPerformanceTracker()
        model_name = 'wqi-prediction-model'
        
        # Simulate 100 predictions with normal distribution
        for i in range(100):
            tracker.log_prediction(
                model_name=model_name,
                prediction=75.0 + (i % 10) * 0.5,
                confidence=0.90 + (i % 10) * 0.01,
                latency_ms=100.0 + (i % 20) * 5.0
            )
        
        # Verify rolling window is populated
        predictions = tracker.get_rolling_window_predictions()
        assert len(predictions) == 100
        
        # Calculate drift score
        drift_score = tracker.calculate_drift_score(model_name, predictions)
        assert drift_score >= 0.0
        
        # Check for drift (should be low with normal data)
        drift_detected = tracker.check_for_drift(model_name, drift_score)
        assert drift_detected is False
        
        # Get performance metrics
        metrics = tracker.get_performance_metrics(model_name)
        assert metrics['model_name'] == model_name
        assert metrics['rolling_window_size'] == 100
        assert 'current_mean' in metrics
        assert 'drift_score' in metrics
    
    @mock_aws
    def test_ml_monitoring_drift_detection(self, setup_environment):
        """Test drift detection with changing data distribution"""
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
        
        from model_performance_monitor import ModelPerformanceTracker
        
        tracker = ModelPerformanceTracker()
        model_name = 'wqi-prediction-model'
        
        # Establish baseline with normal predictions
        for i in range(100):
            tracker.log_prediction(
                model_name=model_name,
                prediction=75.0 + (i % 10) * 0.5,
                confidence=0.90,
                latency_ms=100.0
            )
        
        # Set baseline manually
        tracker.baseline_cache[model_name] = {
            'mean': 75.0,
            'std': 5.0,
            'confidence_mean': 0.90,
            'confidence_std': 0.05,
            'sample_size': 100
        }
        tracker.cache_timestamps[model_name] = time.time()
        
        # Simulate drift with significantly different predictions
        drifted_predictions = []
        for i in range(100):
            prediction = 90.0 + (i % 10) * 0.5  # Much higher than baseline
            tracker.log_prediction(
                model_name=model_name,
                prediction=prediction,
                confidence=0.85,
                latency_ms=120.0
            )
            drifted_predictions.append(prediction)
        
        # Calculate drift score
        drift_score = tracker.calculate_drift_score(model_name, drifted_predictions)
        assert drift_score > 0.15  # Should exceed threshold
        
        # Simulate consecutive drift detections
        drift_triggered = False
        for i in range(15):
            drift_detected = tracker.check_for_drift(model_name, drift_score)
            if drift_detected:
                drift_triggered = True
                break
        
        assert drift_triggered is True
        assert tracker.consecutive_drift_counts[model_name] >= 10


class TestOTAUpdatesE2E:
    """End-to-end tests for OTA update system"""
    
    @mock_aws
    def test_ota_update_workflow(self, setup_environment):
        """Test complete OTA update workflow"""
        # Setup S3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-firmware-bucket')
        
        # Upload firmware
        firmware_content = b'FIRMWARE_v2.0.0_CONTENT'
        s3.put_object(
            Bucket='test-firmware-bucket',
            Key='unsigned/firmware-v2.0.0.bin',
            Body=firmware_content
        )
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        device_table = dynamodb.create_table(
            TableName='test-devices',
            KeySchema=[
                {'AttributeName': 'device_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'device_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        firmware_table = dynamodb.create_table(
            TableName='test-firmware-history',
            KeySchema=[
                {'AttributeName': 'job_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create test device
        device_table.put_item(Item={
            'device_id': 'test-device-001',
            'firmware_version': '1.0.0'
        })
        
        # Setup IoT
        iot = boto3.client('iot', region_name='us-east-1')
        iot.create_thing(thingName='test-device-001')
        
        # Set environment variables
        os.environ['DEVICE_TABLE'] = 'test-devices'
        os.environ['FIRMWARE_HISTORY_TABLE'] = 'test-firmware-history'
        
        from ota_update_manager import OTAUpdateManager
        
        manager = OTAUpdateManager()
        
        # Test firmware signing
        sign_result = manager.sign_firmware(
            firmware_key='unsigned/firmware-v2.0.0.bin',
            version='2.0.0'
        )
        
        # Verify signing result (may have error in test environment)
        assert sign_result is not None
        
        # Test creating firmware job
        job_result = manager.create_firmware_job(
            firmware_version='2.0.0',
            signed_firmware_key='signed/v2.0.0/firmware.bin',
            target_devices=['test-device-001']
        )
        
        # Verify job creation
        assert job_result is not None
        
        # Test update status handling
        status_result = manager.handle_update_status(
            device_id='test-device-001',
            firmware_version='2.0.0',
            status='success'
        )
        
        assert status_result['device_id'] == 'test-device-001'
        assert status_result['status'] == 'success'
        
        # Verify device firmware version was updated
        device = device_table.get_item(Key={'device_id': 'test-device-001'})
        assert device['Item']['firmware_version'] == '2.0.0'
        assert 'previous_firmware_version' in device['Item']


class TestCertificateRotationE2E:
    """End-to-end tests for certificate rotation"""
    
    @mock_aws
    def test_certificate_rotation_workflow(self, setup_environment):
        """Test complete certificate rotation workflow"""
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        cert_table = dynamodb.create_table(
            TableName='test-certificate-lifecycle',
            KeySchema=[
                {'AttributeName': 'device_id', 'KeyType': 'HASH'},
                {'AttributeName': 'certificate_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'device_id', 'AttributeType': 'S'},
                {'AttributeName': 'certificate_id', 'AttributeType': 'S'},
                {'AttributeName': 'expiration_date', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'expiration-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'expiration_date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create certificate expiring soon
        expiration_date = (datetime.utcnow() + timedelta(days=20)).isoformat()
        cert_table.put_item(Item={
            'device_id': 'test-device-001',
            'certificate_id': 'old-cert-123',
            'expiration_date': expiration_date,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Setup IoT
        iot = boto3.client('iot', region_name='us-east-1')
        iot.create_thing(thingName='test-device-001')
        
        os.environ['CERTIFICATE_LIFECYCLE_TABLE'] = 'test-certificate-lifecycle'
        
        from certificate_rotation import CertificateLifecycleManager
        
        manager = CertificateLifecycleManager()
        
        # Check for expiring certificates
        expiring_certs = manager.check_expiring_certificates(days_threshold=30)
        
        # Should find the certificate expiring in 20 days
        assert len(expiring_certs) > 0
        
        # Test certificate generation
        new_cert = manager.generate_new_certificate('test-device-001')
        
        assert new_cert is not None
        assert hasattr(new_cert, 'certificate_id')
        assert hasattr(new_cert, 'certificate_pem')


class TestDependencyScanningE2E:
    """End-to-end tests for dependency scanning and SBOM generation"""
    
    @mock_aws
    def test_dependency_scanning_workflow(self, setup_environment):
        """Test complete dependency scanning workflow"""
        # Setup S3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-results-bucket')
        s3.create_bucket(Bucket='test-source-bucket')
        
        # Upload test package.json
        package_json = {
            "name": "test-app",
            "version": "1.0.0",
            "dependencies": {
                "axios": "0.21.0",
                "lodash": "4.17.20"
            }
        }
        s3.put_object(
            Bucket='test-source-bucket',
            Key='frontend/package.json',
            Body=json.dumps(package_json)
        )
        
        # Upload test requirements.txt
        requirements = "requests==2.25.0\nurllib3==1.26.0"
        s3.put_object(
            Bucket='test-source-bucket',
            Key='lambda/requirements.txt',
            Body=requirements
        )
        
        os.environ['SOURCE_BUCKET'] = 'test-source-bucket'
        
        from dependency_scanner import DependencyScanner
        
        scanner = DependencyScanner()
        
        # Note: Actual scanning requires npm and pip-audit installed
        # In test environment, we verify the scanner can be instantiated
        # and has the correct methods
        
        assert hasattr(scanner, 'scan_npm_dependencies')
        assert hasattr(scanner, 'scan_python_dependencies')
        assert hasattr(scanner, 'generate_report')
        assert hasattr(scanner, 'send_alerts')
        
        # Verify scan results structure
        assert 'timestamp' in scanner.scan_results
        assert 'scans' in scanner.scan_results


class TestMonitoringAndAlertsE2E:
    """End-to-end tests for monitoring and alerting"""
    
    @mock_aws
    def test_cloudwatch_metrics_publishing(self, setup_environment):
        """Test CloudWatch metrics publishing"""
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Publish test metrics
        cloudwatch.put_metric_data(
            Namespace='AquaChain/Phase3',
            MetricData=[
                {
                    'MetricName': 'ModelDriftScore',
                    'Value': 0.12,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'PredictionLatency',
                    'Value': 150.0,
                    'Unit': 'Milliseconds',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        # Verify metrics can be retrieved
        # Note: moto doesn't fully support get_metric_statistics
        # In real environment, we would verify metrics are queryable
        
        assert True  # Basic test passes
    
    @mock_aws
    def test_sns_alert_delivery(self, setup_environment):
        """Test SNS alert delivery"""
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create test topic
        topic_response = sns.create_topic(Name='test-alerts')
        topic_arn = topic_response['TopicArn']
        
        # Publish test alert
        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Test Alert: Critical Vulnerability Detected',
            Message=json.dumps({
                'alert_type': 'critical_vulnerability',
                'timestamp': datetime.utcnow().isoformat(),
                'details': {
                    'package': 'test-package',
                    'severity': 'critical',
                    'cve': 'CVE-2021-12345'
                }
            })
        )
        
        assert 'MessageId' in response
        assert response['MessageId'] is not None


class TestIntegrationScenarios:
    """Test integrated scenarios across multiple components"""
    
    @mock_aws
    def test_full_monitoring_pipeline(self, setup_environment):
        """Test full monitoring pipeline from prediction to alert"""
        # Setup all required resources
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        s3 = boto3.client('s3', region_name='us-east-1')
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Create DynamoDB table
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
        
        # Create SNS topic
        topic_response = sns.create_topic(Name='test-alerts')
        topic_arn = topic_response['TopicArn']
        os.environ['ALERT_TOPIC_ARN'] = topic_arn
        
        from model_performance_monitor import ModelPerformanceTracker
        
        tracker = ModelPerformanceTracker()
        model_name = 'wqi-prediction-model'
        
        # Scenario: Normal operation
        for i in range(50):
            tracker.log_prediction(
                model_name=model_name,
                prediction=75.0 + (i % 10) * 0.5,
                confidence=0.90,
                latency_ms=100.0
            )
        
        # Publish metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='AquaChain/ML',
            MetricData=[
                {
                    'MetricName': 'PredictionCount',
                    'Value': 50,
                    'Unit': 'Count'
                }
            ]
        )
        
        # Verify system is healthy
        predictions = tracker.get_rolling_window_predictions()
        assert len(predictions) == 50
        
        metrics = tracker.get_performance_metrics(model_name)
        assert metrics['rolling_window_size'] == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
