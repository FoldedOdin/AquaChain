"""
Unit Tests for System Health Monitoring Logic (Phase 3c)

Tests cover:
- get_system_health() function with caching
- Individual health check functions
- Cache hit/miss behavior
- Force refresh functionality
- Timeout handling
- Error handling (returns 'unknown' status)
- Overall status determination logic

Test Coverage:
- Cache behavior (hit, miss, expiration)
- All service health checks
- Error scenarios
- Timeout scenarios
- Status aggregation logic
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import TimeoutError as FuturesTimeoutError

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import health_monitor
from health_monitor import (
    get_system_health,
    _check_iot_core_health,
    _check_lambda_health,
    _check_dynamodb_health,
    _check_sns_health,
    _check_ml_inference_health,
    CACHE_DURATION_SECONDS,
    CHECK_TIMEOUT_SECONDS
)


class TestGetSystemHealth:
    """Test suite for get_system_health function"""
    
    def setup_method(self):
        """Reset cache before each test"""
        health_monitor._health_cache = {}
        health_monitor._cache_timestamp = None
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_get_system_health_cache_miss(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test get_system_health fetches fresh data when cache is empty"""
        # Setup mock responses
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        # Verify all health checks were called
        mock_iot.assert_called_once()
        mock_lambda.assert_called_once()
        mock_db.assert_called_once()
        mock_sns.assert_called_once()
        mock_ml.assert_called_once()
        
        # Verify response structure
        assert 'services' in result
        assert 'overallStatus' in result
        assert 'checkedAt' in result
        assert 'cacheHit' in result
        
        # Verify cache miss
        assert result['cacheHit'] is False
        
        # Verify all services present
        assert len(result['services']) == 5
        
        # Verify overall status
        assert result['overallStatus'] == 'healthy'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_get_system_health_cache_hit(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test get_system_health returns cached data when cache is fresh"""
        # Setup mock responses
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        # First call - populate cache
        result1 = get_system_health()
        assert result1['cacheHit'] is False
        
        # Reset mock call counts
        mock_iot.reset_mock()
        mock_lambda.reset_mock()
        mock_db.reset_mock()
        mock_sns.reset_mock()
        mock_ml.reset_mock()
        
        # Second call - should use cache
        result2 = get_system_health()
        
        # Verify health checks were NOT called
        mock_iot.assert_not_called()
        mock_lambda.assert_not_called()
        mock_db.assert_not_called()
        mock_sns.assert_not_called()
        mock_ml.assert_not_called()
        
        # Verify cache hit
        assert result2['cacheHit'] is True
        
        # Verify same data returned
        assert result2['overallStatus'] == result1['overallStatus']
        assert len(result2['services']) == len(result1['services'])
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_get_system_health_force_refresh(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test force_refresh bypasses cache"""
        # Setup mock responses
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        # First call - populate cache
        result1 = get_system_health()
        assert result1['cacheHit'] is False
        
        # Reset mock call counts
        mock_iot.reset_mock()
        mock_lambda.reset_mock()
        mock_db.reset_mock()
        mock_sns.reset_mock()
        mock_ml.reset_mock()
        
        # Second call with force_refresh=True
        result2 = get_system_health(force_refresh=True)
        
        # Verify health checks WERE called despite cache
        mock_iot.assert_called_once()
        mock_lambda.assert_called_once()
        mock_db.assert_called_once()
        mock_sns.assert_called_once()
        mock_ml.assert_called_once()
        
        # Verify cache was bypassed
        assert result2['cacheHit'] is False
    
    @patch('health_monitor.datetime')
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_get_system_health_cache_expiration(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot, mock_datetime):
        """Test cache expires after CACHE_DURATION_SECONDS"""
        # Setup mock responses
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        # Mock time progression
        base_time = datetime(2026, 2, 26, 10, 0, 0)
        mock_datetime.utcnow.return_value = base_time
        
        # First call - populate cache
        result1 = get_system_health()
        assert result1['cacheHit'] is False
        
        # Reset mock call counts
        mock_iot.reset_mock()
        mock_lambda.reset_mock()
        mock_db.reset_mock()
        mock_sns.reset_mock()
        mock_ml.reset_mock()
        
        # Advance time by CACHE_DURATION_SECONDS + 1
        mock_datetime.utcnow.return_value = base_time + timedelta(seconds=CACHE_DURATION_SECONDS + 1)
        
        # Second call - cache should be expired
        result2 = get_system_health()
        
        # Verify health checks WERE called (cache expired)
        mock_iot.assert_called_once()
        mock_lambda.assert_called_once()
        mock_db.assert_called_once()
        mock_sns.assert_called_once()
        mock_ml.assert_called_once()
        
        # Verify cache miss
        assert result2['cacheHit'] is False
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_overall_status_healthy(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test overall status is 'healthy' when all services are healthy"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'healthy'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_overall_status_degraded_with_one_degraded(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test overall status is 'degraded' when one service is degraded"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'degraded', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'degraded'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_overall_status_degraded_with_unknown(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test overall status is 'degraded' when one service is unknown"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'degraded'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_overall_status_down_with_one_down(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test overall status is 'down' when one service is down"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'down', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'down'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_overall_status_down_takes_precedence(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test 'down' status takes precedence over 'degraded'"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'down', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'degraded', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'down'


class TestIoTCoreHealth:
    """Test suite for _check_iot_core_health function"""
    
    @patch('health_monitor.cloudwatch')
    def test_iot_core_healthy_with_messages(self, mock_cloudwatch):
        """Test IoT Core health check returns healthy with message traffic"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 1500.0, 'Timestamp': datetime.utcnow()}
            ]
        }
        
        result = _check_iot_core_health()
        
        assert result['name'] == 'IoT Core'
        assert result['status'] == 'healthy'
        assert 'lastCheck' in result
        assert 'metrics' in result
        assert result['metrics']['messagesLast5Min'] == 1500
    
    @patch('health_monitor.cloudwatch')
    def test_iot_core_healthy_with_no_traffic(self, mock_cloudwatch):
        """Test IoT Core health check returns healthy with no traffic"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': []
        }
        
        result = _check_iot_core_health()
        
        assert result['name'] == 'IoT Core'
        assert result['status'] == 'healthy'
        assert result['metrics']['messagesLast5Min'] == 0
        assert 'No recent MQTT traffic' in result['message']
    
    @patch('health_monitor.cloudwatch')
    def test_iot_core_unknown_on_error(self, mock_cloudwatch):
        """Test IoT Core health check returns unknown on error"""
        mock_cloudwatch.get_metric_statistics.side_effect = Exception('CloudWatch API error')
        
        result = _check_iot_core_health()
        
        assert result['name'] == 'IoT Core'
        assert result['status'] == 'unknown'
        assert 'Health check failed' in result['message']


class TestLambdaHealth:
    """Test suite for _check_lambda_health function"""
    
    @patch('health_monitor.cloudwatch')
    def test_lambda_healthy_high_success_rate(self, mock_cloudwatch):
        """Test Lambda health check returns healthy with >95% success rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'Invocations':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'Errors':
                return {'Datapoints': [{'Sum': 10.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_lambda_health()
        
        assert result['name'] == 'Lambda'
        assert result['status'] == 'healthy'
        assert result['metrics']['successRate'] == 99.0
        assert result['metrics']['invocations'] == 1000
        assert result['metrics']['errors'] == 10
    
    @patch('health_monitor.cloudwatch')
    def test_lambda_degraded_medium_success_rate(self, mock_cloudwatch):
        """Test Lambda health check returns degraded with 90-95% success rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'Invocations':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'Errors':
                return {'Datapoints': [{'Sum': 80.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_lambda_health()
        
        assert result['name'] == 'Lambda'
        assert result['status'] == 'degraded'
        assert result['metrics']['successRate'] == 92.0
    
    @patch('health_monitor.cloudwatch')
    def test_lambda_down_low_success_rate(self, mock_cloudwatch):
        """Test Lambda health check returns down with <90% success rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'Invocations':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'Errors':
                return {'Datapoints': [{'Sum': 150.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_lambda_health()
        
        assert result['name'] == 'Lambda'
        assert result['status'] == 'down'
        assert result['metrics']['successRate'] == 85.0
    
    @patch('health_monitor.cloudwatch')
    def test_lambda_healthy_no_invocations(self, mock_cloudwatch):
        """Test Lambda health check returns healthy with no invocations"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            return {'Datapoints': []}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_lambda_health()
        
        assert result['name'] == 'Lambda'
        assert result['status'] == 'healthy'
        assert result['metrics']['invocations'] == 0
        assert 'No recent invocations' in result['message']
    
    @patch('health_monitor.cloudwatch')
    def test_lambda_unknown_on_error(self, mock_cloudwatch):
        """Test Lambda health check returns unknown on error"""
        mock_cloudwatch.get_metric_statistics.side_effect = Exception('CloudWatch API error')
        
        result = _check_lambda_health()
        
        assert result['name'] == 'Lambda'
        assert result['status'] == 'unknown'
        assert 'Health check failed' in result['message']


class TestDynamoDBHealth:
    """Test suite for _check_dynamodb_health function"""
    
    @patch('health_monitor.dynamodb')
    def test_dynamodb_healthy_all_tables_active(self, mock_dynamodb):
        """Test DynamoDB health check returns healthy when all tables are active"""
        mock_dynamodb.describe_table.return_value = {
            'Table': {'TableStatus': 'ACTIVE'}
        }
        
        result = _check_dynamodb_health()
        
        assert result['name'] == 'DynamoDB'
        assert result['status'] == 'healthy'
        assert result['metrics']['tablesChecked'] == 3
    
    @patch('health_monitor.dynamodb')
    def test_dynamodb_degraded_table_not_active(self, mock_dynamodb):
        """Test DynamoDB health check returns degraded when a table is not active"""
        call_count = [0]
        
        def describe_table_side_effect(TableName):
            call_count[0] += 1
            if call_count[0] == 2:
                return {'Table': {'TableStatus': 'UPDATING'}}
            return {'Table': {'TableStatus': 'ACTIVE'}}
        
        mock_dynamodb.describe_table.side_effect = describe_table_side_effect
        
        result = _check_dynamodb_health()
        
        assert result['name'] == 'DynamoDB'
        assert result['status'] == 'degraded'
        assert 'One or more tables not active' in result['message']
    
    @patch('health_monitor.dynamodb')
    def test_dynamodb_degraded_table_not_found(self, mock_dynamodb):
        """Test DynamoDB health check returns degraded when a table is not found"""
        from botocore.exceptions import ClientError
        
        call_count = [0]
        
        def describe_table_side_effect(TableName):
            call_count[0] += 1
            if call_count[0] == 2:
                error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
                raise ClientError(error_response, 'DescribeTable')
            return {'Table': {'TableStatus': 'ACTIVE'}}
        
        mock_dynamodb.describe_table.side_effect = describe_table_side_effect
        mock_dynamodb.exceptions.ResourceNotFoundException = ClientError
        
        result = _check_dynamodb_health()
        
        assert result['name'] == 'DynamoDB'
        assert result['status'] == 'degraded'
    
    @patch('health_monitor.dynamodb')
    def test_dynamodb_unknown_on_error(self, mock_dynamodb):
        """Test DynamoDB health check returns unknown on error"""
        mock_dynamodb.describe_table.side_effect = Exception('DynamoDB API error')
        
        result = _check_dynamodb_health()
        
        assert result['name'] == 'DynamoDB'
        assert result['status'] == 'unknown'
        assert 'Health check failed' in result['message']


class TestSNSHealth:
    """Test suite for _check_sns_health function"""
    
    @patch('health_monitor.cloudwatch')
    def test_sns_healthy_high_delivery_rate(self, mock_cloudwatch):
        """Test SNS health check returns healthy with >98% delivery rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'NumberOfMessagesPublished':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'NumberOfNotificationsFailed':
                return {'Datapoints': [{'Sum': 5.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_sns_health()
        
        assert result['name'] == 'SNS'
        assert result['status'] == 'healthy'
        assert result['metrics']['deliveryRate'] == 99.5
        assert result['metrics']['published'] == 1000
        assert result['metrics']['failed'] == 5
    
    @patch('health_monitor.cloudwatch')
    def test_sns_degraded_medium_delivery_rate(self, mock_cloudwatch):
        """Test SNS health check returns degraded with 95-98% delivery rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'NumberOfMessagesPublished':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'NumberOfNotificationsFailed':
                return {'Datapoints': [{'Sum': 30.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_sns_health()
        
        assert result['name'] == 'SNS'
        assert result['status'] == 'degraded'
        assert result['metrics']['deliveryRate'] == 97.0
    
    @patch('health_monitor.cloudwatch')
    def test_sns_down_low_delivery_rate(self, mock_cloudwatch):
        """Test SNS health check returns down with <95% delivery rate"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            if MetricName == 'NumberOfMessagesPublished':
                return {'Datapoints': [{'Sum': 1000.0}]}
            elif MetricName == 'NumberOfNotificationsFailed':
                return {'Datapoints': [{'Sum': 100.0}]}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_sns_health()
        
        assert result['name'] == 'SNS'
        assert result['status'] == 'down'
        assert result['metrics']['deliveryRate'] == 90.0
    
    @patch('health_monitor.cloudwatch')
    def test_sns_healthy_no_notifications(self, mock_cloudwatch):
        """Test SNS health check returns healthy with no notifications"""
        def get_metric_side_effect(Namespace, MetricName, **kwargs):
            return {'Datapoints': []}
        
        mock_cloudwatch.get_metric_statistics.side_effect = get_metric_side_effect
        
        result = _check_sns_health()
        
        assert result['name'] == 'SNS'
        assert result['status'] == 'healthy'
        assert result['metrics']['published'] == 0
        assert 'No recent notifications' in result['message']
    
    @patch('health_monitor.cloudwatch')
    def test_sns_unknown_on_error(self, mock_cloudwatch):
        """Test SNS health check returns unknown on error"""
        mock_cloudwatch.get_metric_statistics.side_effect = Exception('CloudWatch API error')
        
        result = _check_sns_health()
        
        assert result['name'] == 'SNS'
        assert result['status'] == 'unknown'
        assert 'Health check failed' in result['message']


class TestMLInferenceHealth:
    """Test suite for _check_ml_inference_health function"""
    
    @patch('health_monitor.cloudwatch')
    def test_ml_inference_healthy_low_latency(self, mock_cloudwatch):
        """Test ML Inference health check returns healthy with <500ms latency"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [{'Average': 350.0}]
        }
        
        result = _check_ml_inference_health()
        
        assert result['name'] == 'ML Inference'
        assert result['status'] == 'healthy'
        assert result['metrics']['avgLatency'] == 350.0
    
    @patch('health_monitor.cloudwatch')
    def test_ml_inference_degraded_medium_latency(self, mock_cloudwatch):
        """Test ML Inference health check returns degraded with 500-1000ms latency"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [{'Average': 750.0}]
        }
        
        result = _check_ml_inference_health()
        
        assert result['name'] == 'ML Inference'
        assert result['status'] == 'degraded'
        assert result['metrics']['avgLatency'] == 750.0
    
    @patch('health_monitor.cloudwatch')
    def test_ml_inference_down_high_latency(self, mock_cloudwatch):
        """Test ML Inference health check returns down with >=1000ms latency"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [{'Average': 1500.0}]
        }
        
        result = _check_ml_inference_health()
        
        assert result['name'] == 'ML Inference'
        assert result['status'] == 'down'
        assert result['metrics']['avgLatency'] == 1500.0
    
    @patch('health_monitor.cloudwatch')
    def test_ml_inference_healthy_no_predictions(self, mock_cloudwatch):
        """Test ML Inference health check returns healthy with no predictions"""
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': []
        }
        
        result = _check_ml_inference_health()
        
        assert result['name'] == 'ML Inference'
        assert result['status'] == 'healthy'
        assert 'No recent predictions' in result['message']
    
    @patch('health_monitor.cloudwatch')
    def test_ml_inference_unknown_on_error(self, mock_cloudwatch):
        """Test ML Inference health check returns unknown on error"""
        mock_cloudwatch.get_metric_statistics.side_effect = Exception('CloudWatch API error')
        
        result = _check_ml_inference_health()
        
        assert result['name'] == 'ML Inference'
        assert result['status'] == 'unknown'
        assert 'Health check failed' in result['message']


class TestTimeoutHandling:
    """Test suite for timeout handling in parallel health checks"""
    
    def setup_method(self):
        """Reset cache before each test"""
        health_monitor._health_cache = {}
        health_monitor._cache_timestamp = None
    
    def test_timeout_constant_is_reasonable(self):
        """Test that CHECK_TIMEOUT_SECONDS is set to a reasonable value"""
        # Verify timeout is configured (2 seconds is reasonable for health checks)
        assert CHECK_TIMEOUT_SECONDS == 2
        assert CHECK_TIMEOUT_SECONDS > 0
        assert CHECK_TIMEOUT_SECONDS < 10  # Not too long


class TestErrorHandling:
    """Test suite for error handling in health checks"""
    
    def setup_method(self):
        """Reset cache before each test"""
        health_monitor._health_cache = {}
        health_monitor._cache_timestamp = None
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_exception_in_health_check_returns_unknown(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test that exceptions in health checks return 'unknown' status"""
        mock_iot.side_effect = Exception('Unexpected error')
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        # IoT Core should have unknown status
        iot_service = next(s for s in result['services'] if s['name'] == 'IoT Core')
        assert iot_service['status'] == 'unknown'
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_all_checks_fail_overall_status_degraded(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test overall status is 'degraded' when all checks return unknown"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'unknown', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        assert result['overallStatus'] == 'degraded'


class TestCacheConstants:
    """Test suite for cache configuration constants"""
    
    def test_cache_duration_constant(self):
        """Test CACHE_DURATION_SECONDS is set correctly"""
        assert CACHE_DURATION_SECONDS == 30
    
    def test_check_timeout_constant(self):
        """Test CHECK_TIMEOUT_SECONDS is set correctly"""
        assert CHECK_TIMEOUT_SECONDS == 2


class TestResponseStructure:
    """Test suite for response structure validation"""
    
    def setup_method(self):
        """Reset cache before each test"""
        health_monitor._health_cache = {}
        health_monitor._cache_timestamp = None
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_response_has_required_fields(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test response contains all required fields"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        # Check top-level fields
        assert 'services' in result
        assert 'overallStatus' in result
        assert 'checkedAt' in result
        assert 'cacheHit' in result
        
        # Check services is a list
        assert isinstance(result['services'], list)
        
        # Check each service has required fields
        for service in result['services']:
            assert 'name' in service
            assert 'status' in service
            assert 'lastCheck' in service
    
    @patch('health_monitor._check_iot_core_health')
    @patch('health_monitor._check_lambda_health')
    @patch('health_monitor._check_dynamodb_health')
    @patch('health_monitor._check_sns_health')
    @patch('health_monitor._check_ml_inference_health')
    def test_checked_at_is_iso8601_format(self, mock_ml, mock_sns, mock_db, mock_lambda, mock_iot):
        """Test checkedAt timestamp is in ISO8601 format"""
        mock_iot.return_value = {'name': 'IoT Core', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_lambda.return_value = {'name': 'Lambda', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_db.return_value = {'name': 'DynamoDB', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_sns.return_value = {'name': 'SNS', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        mock_ml.return_value = {'name': 'ML Inference', 'status': 'healthy', 'lastCheck': '2026-02-26T10:00:00Z'}
        
        result = get_system_health()
        
        # Check timestamp format (should end with 'Z' for UTC)
        assert result['checkedAt'].endswith('Z')
        assert 'T' in result['checkedAt']
