"""
Integration tests for audit logging workflow
Tests the complete end-to-end audit logging process
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
from botocore.exceptions import ClientError

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from audit_logger import AuditLogger


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'AUDIT_LOGS_TABLE': 'test-audit-logs',
        'AUDIT_LOG_STREAM': 'test-audit-stream'
    }):
        yield


@pytest.fixture
def mock_dynamodb():
    """Fixture providing mocked DynamoDB"""
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_firehose():
    """Fixture providing mocked Kinesis Firehose"""
    with patch('boto3.client') as mock_client:
        mock_firehose_client = MagicMock()
        
        def get_client(service_name):
            if service_name == 'firehose':
                return mock_firehose_client
            return MagicMock()
        
        mock_client.side_effect = get_client
        yield mock_firehose_client


@pytest.fixture
def sample_request_context():
    """Fixture providing sample request context"""
    return {
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'request_id': 'req-123',
        'source': 'api'
    }


class TestAuditLogCreation:
    """Test suite for audit log creation"""
    
    def test_log_authentication_event_success(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging successful authentication event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log authentication event
        log_entry = logger.log_authentication_event(
            event_type='LOGIN',
            user_id='user-123',
            success=True,
            request_context=sample_request_context,
            details={'method': 'password'}
        )
        
        # Verify log entry structure
        assert log_entry['action_type'] == 'AUTH_LOGIN'
        assert log_entry['user_id'] == 'user-123'
        assert log_entry['resource_type'] == 'USER'
        assert log_entry['resource_id'] == 'user-123'
        assert log_entry['details']['success'] is True
        assert log_entry['details']['method'] == 'password'
        assert 'log_id' in log_entry
        assert 'timestamp' in log_entry
        assert 'ttl' in log_entry
        
        # Verify DynamoDB was called
        mock_dynamodb.put_item.assert_called_once()
        
        # Verify Firehose was called
        mock_firehose.put_record.assert_called_once()
    
    def test_log_authentication_event_failure(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging failed authentication event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log failed authentication
        log_entry = logger.log_authentication_event(
            event_type='LOGIN',
            user_id='user-123',
            success=False,
            request_context=sample_request_context,
            details={'reason': 'invalid_password'}
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'AUTH_LOGIN'
        assert log_entry['details']['success'] is False
        assert log_entry['details']['reason'] == 'invalid_password'
    
    def test_log_data_access_event(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging data access event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log data access
        log_entry = logger.log_data_access(
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            operation='GET',
            request_context=sample_request_context,
            details={'fields': ['name', 'status', 'location']}
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'READ'
        assert log_entry['user_id'] == 'user-123'
        assert log_entry['resource_type'] == 'DEVICE'
        assert log_entry['resource_id'] == 'device-456'
        assert log_entry['details']['operation'] == 'GET'
        assert log_entry['details']['fields'] == ['name', 'status', 'location']
    
    def test_log_data_modification_create(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging data creation event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log data creation
        new_values = {
            'device_id': 'device-789',
            'name': 'New Sensor',
            'status': 'active'
        }
        
        log_entry = logger.log_data_modification(
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-789',
            modification_type='CREATE',
            previous_values=None,
            new_values=new_values,
            request_context=sample_request_context
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'CREATE'
        assert log_entry['details']['modification_type'] == 'CREATE'
        assert log_entry['details']['new_values'] == new_values
        assert log_entry['details']['previous_values'] is None
        assert log_entry['details']['changed_fields'] == ['device_id', 'name', 'status']
    
    def test_log_data_modification_update(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging data update event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log data update
        previous_values = {'status': 'active', 'name': 'Old Name'}
        new_values = {'status': 'inactive', 'name': 'New Name'}
        
        log_entry = logger.log_data_modification(
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            modification_type='UPDATE',
            previous_values=previous_values,
            new_values=new_values,
            request_context=sample_request_context
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'UPDATE'
        assert log_entry['details']['modification_type'] == 'UPDATE'
        assert log_entry['details']['previous_values'] == previous_values
        assert log_entry['details']['new_values'] == new_values
    
    def test_log_data_modification_delete(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging data deletion event"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log data deletion
        previous_values = {
            'device_id': 'device-456',
            'name': 'Deleted Sensor',
            'status': 'active'
        }
        
        log_entry = logger.log_data_modification(
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            modification_type='DELETE',
            previous_values=previous_values,
            new_values={},
            request_context=sample_request_context
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'DELETE'
        assert log_entry['details']['modification_type'] == 'DELETE'
        assert log_entry['details']['previous_values'] == previous_values
    
    def test_log_administrative_action(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test logging administrative action"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log admin action
        log_entry = logger.log_administrative_action(
            user_id='admin-123',
            action='USER_ROLE_CHANGE',
            target_resource_type='USER',
            target_resource_id='user-456',
            request_context=sample_request_context,
            details={
                'previous_role': 'consumer',
                'new_role': 'technician'
            }
        )
        
        # Verify log entry
        assert log_entry['action_type'] == 'ADMIN_USER_ROLE_CHANGE'
        assert log_entry['user_id'] == 'admin-123'
        assert log_entry['resource_type'] == 'USER'
        assert log_entry['resource_id'] == 'user-456'
        assert log_entry['details']['administrative_action'] == 'USER_ROLE_CHANGE'


class TestAuditLogImmutability:
    """Test suite for audit log immutability"""
    
    def test_audit_log_has_ttl(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that audit logs have 7-year TTL"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log an action
        log_entry = logger.log_action(
            action_type='READ',
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            details={},
            request_context=sample_request_context
        )
        
        # Verify TTL is set
        assert 'ttl' in log_entry
        
        # Calculate expected TTL (7 years = 2555 days)
        now = datetime.utcnow()
        expected_ttl = now + timedelta(days=2555)
        actual_ttl = datetime.fromtimestamp(log_entry['ttl'])
        
        # Allow 1 minute tolerance
        time_diff = abs((actual_ttl - expected_ttl).total_seconds())
        assert time_diff < 60
    
    def test_audit_log_streams_to_firehose(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that audit logs are streamed to Firehose for S3 archival"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Log an action
        log_entry = logger.log_action(
            action_type='UPDATE',
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            details={'field': 'status'},
            request_context=sample_request_context
        )
        
        # Verify Firehose was called
        mock_firehose.put_record.assert_called_once()
        
        # Verify the record format
        call_args = mock_firehose.put_record.call_args
        assert call_args[1]['DeliveryStreamName'] == 'test-audit-stream'
        
        # Verify record data is JSON with newline
        record_data = call_args[1]['Record']['Data'].decode('utf-8')
        assert record_data.endswith('\n')
        
        # Verify JSON is valid
        parsed_data = json.loads(record_data.strip())
        assert parsed_data['log_id'] == log_entry['log_id']
    
    def test_audit_log_continues_on_firehose_failure(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that audit logging continues even if Firehose fails"""
        logger = AuditLogger()
        
        # Mock DynamoDB success, Firehose failure
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'PutRecord'
        )
        
        # Log an action - should not raise exception
        log_entry = logger.log_action(
            action_type='READ',
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            details={},
            request_context=sample_request_context
        )
        
        # Verify log entry was created
        assert log_entry is not None
        assert 'log_id' in log_entry
        
        # Verify DynamoDB was still called
        mock_dynamodb.put_item.assert_called_once()


class TestAuditLogRetention:
    """Test suite for audit log retention"""
    
    def test_audit_log_retention_period(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that audit logs are configured for 7-year retention"""
        logger = AuditLogger()
        
        # Verify TTL days is set to 2555 (7 years)
        assert logger.ttl_days == 2555
    
    def test_multiple_audit_logs_all_have_ttl(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that all audit logs have TTL set"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Create multiple log entries
        log_entries = []
        for i in range(5):
            log_entry = logger.log_action(
                action_type='READ',
                user_id=f'user-{i}',
                resource_type='DEVICE',
                resource_id=f'device-{i}',
                details={},
                request_context=sample_request_context
            )
            log_entries.append(log_entry)
        
        # Verify all have TTL
        for log_entry in log_entries:
            assert 'ttl' in log_entry
            assert isinstance(log_entry['ttl'], int)
            assert log_entry['ttl'] > 0


class TestAuditLogQuerying:
    """Test suite for audit log querying"""
    
    def test_query_logs_by_user(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test querying audit logs by user ID"""
        logger = AuditLogger()
        
        # Mock query response
        mock_logs = [
            {
                'log_id': 'log-1',
                'user_id': 'user-123',
                'action_type': 'READ',
                'timestamp': '2025-10-25T12:00:00Z'
            },
            {
                'log_id': 'log-2',
                'user_id': 'user-123',
                'action_type': 'UPDATE',
                'timestamp': '2025-10-25T13:00:00Z'
            }
        ]
        
        mock_dynamodb.query.return_value = {
            'Items': mock_logs,
            'Count': 2
        }
        
        # Query logs
        result = logger.query_logs_by_user('user-123')
        
        # Verify results
        assert result['count'] == 2
        assert len(result['items']) == 2
        assert result['items'][0]['user_id'] == 'user-123'
        
        # Verify query was called with correct parameters
        mock_dynamodb.query.assert_called_once()
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['IndexName'] == 'user_id-timestamp-index'
    
    def test_query_logs_by_resource_type(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test querying audit logs by resource type"""
        logger = AuditLogger()
        
        # Mock query response
        mock_logs = [
            {
                'log_id': 'log-1',
                'resource_type': 'DEVICE',
                'action_type': 'CREATE',
                'timestamp': '2025-10-25T12:00:00Z'
            },
            {
                'log_id': 'log-2',
                'resource_type': 'DEVICE',
                'action_type': 'UPDATE',
                'timestamp': '2025-10-25T13:00:00Z'
            }
        ]
        
        mock_dynamodb.query.return_value = {
            'Items': mock_logs,
            'Count': 2
        }
        
        # Query logs
        result = logger.query_logs_by_resource('DEVICE')
        
        # Verify results
        assert result['count'] == 2
        assert len(result['items']) == 2
        
        # Verify query was called with correct index
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['IndexName'] == 'resource_type-timestamp-index'
    
    def test_query_logs_by_action_type(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test querying audit logs by action type"""
        logger = AuditLogger()
        
        # Mock query response
        mock_logs = [
            {
                'log_id': 'log-1',
                'action_type': 'DELETE',
                'timestamp': '2025-10-25T12:00:00Z'
            },
            {
                'log_id': 'log-2',
                'action_type': 'DELETE',
                'timestamp': '2025-10-25T13:00:00Z'
            }
        ]
        
        mock_dynamodb.query.return_value = {
            'Items': mock_logs,
            'Count': 2
        }
        
        # Query logs
        result = logger.query_logs_by_action_type('DELETE')
        
        # Verify results
        assert result['count'] == 2
        
        # Verify query was called with correct index
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['IndexName'] == 'action_type-timestamp-index'
    
    def test_query_logs_with_time_range(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test querying audit logs with time range filter"""
        logger = AuditLogger()
        
        # Mock query response
        mock_dynamodb.query.return_value = {
            'Items': [],
            'Count': 0
        }
        
        # Query with time range
        start_time = '2025-10-25T00:00:00Z'
        end_time = '2025-10-25T23:59:59Z'
        
        result = logger.query_logs_by_user(
            'user-123',
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify query was called with time range
        call_args = mock_dynamodb.query.call_args
        assert 'KeyConditionExpression' in call_args[1]


class TestCompleteAuditWorkflow:
    """Test suite for complete end-to-end audit workflow"""
    
    def test_complete_user_session_audit_trail(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test complete audit trail for a user session"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        user_id = 'user-123'
        
        # Step 1: User logs in
        login_log = logger.log_authentication_event(
            event_type='LOGIN',
            user_id=user_id,
            success=True,
            request_context=sample_request_context
        )
        
        assert login_log['action_type'] == 'AUTH_LOGIN'
        
        # Step 2: User accesses device data
        access_log = logger.log_data_access(
            user_id=user_id,
            resource_type='DEVICE',
            resource_id='device-456',
            operation='GET',
            request_context=sample_request_context
        )
        
        assert access_log['action_type'] == 'READ'
        
        # Step 3: User updates device
        update_log = logger.log_data_modification(
            user_id=user_id,
            resource_type='DEVICE',
            resource_id='device-456',
            modification_type='UPDATE',
            previous_values={'status': 'active'},
            new_values={'status': 'inactive'},
            request_context=sample_request_context
        )
        
        assert update_log['action_type'] == 'UPDATE'
        
        # Step 4: User logs out
        logout_log = logger.log_authentication_event(
            event_type='LOGOUT',
            user_id=user_id,
            success=True,
            request_context=sample_request_context
        )
        
        assert logout_log['action_type'] == 'AUTH_LOGOUT'
        
        # Verify all logs were created
        assert mock_dynamodb.put_item.call_count == 4
        assert mock_firehose.put_record.call_count == 4
    
    def test_audit_trail_captures_request_context(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test that audit trail captures complete request context"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Create request context with all fields
        request_context = {
            'ip_address': '203.0.113.42',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'request_id': 'unique-req-id-789',
            'source': 'mobile-app'
        }
        
        # Log an action
        log_entry = logger.log_action(
            action_type='CREATE',
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-new',
            details={'device_type': 'sensor'},
            request_context=request_context
        )
        
        # Verify all context fields are captured
        assert log_entry['request_context']['ip_address'] == '203.0.113.42'
        assert log_entry['request_context']['user_agent'] == 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        assert log_entry['request_context']['request_id'] == 'unique-req-id-789'
        assert log_entry['request_context']['source'] == 'mobile-app'
    
    def test_audit_trail_handles_missing_context_fields(self, mock_aws_environment, mock_dynamodb, mock_firehose):
        """Test that audit trail handles missing context fields gracefully"""
        logger = AuditLogger()
        
        # Mock DynamoDB and Firehose
        mock_dynamodb.put_item.return_value = {}
        mock_firehose.put_record.return_value = {}
        
        # Create minimal request context
        request_context = {}
        
        # Log an action
        log_entry = logger.log_action(
            action_type='READ',
            user_id='user-123',
            resource_type='DEVICE',
            resource_id='device-456',
            details={},
            request_context=request_context
        )
        
        # Verify defaults are used
        assert log_entry['request_context']['ip_address'] == 'unknown'
        assert log_entry['request_context']['user_agent'] == 'unknown'
        assert log_entry['request_context']['request_id'] == 'unknown'
        assert log_entry['request_context']['source'] == 'api'


class TestAuditLogErrorHandling:
    """Test suite for audit log error handling"""
    
    def test_audit_log_raises_on_dynamodb_failure(self, mock_aws_environment, mock_dynamodb, mock_firehose, sample_request_context):
        """Test that audit logging raises exception on DynamoDB failure"""
        logger = AuditLogger()
        
        # Mock DynamoDB failure
        mock_dynamodb.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'PutItem'
        )
        
        # Attempt to log - should raise exception
        with pytest.raises(ClientError):
            logger.log_action(
                action_type='READ',
                user_id='user-123',
                resource_type='DEVICE',
                resource_id='device-456',
                details={},
                request_context=sample_request_context
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
