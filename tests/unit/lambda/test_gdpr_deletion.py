"""
Unit tests for GDPR data deletion service
Target: 80% code coverage
"""

import pytest
import json
import sys
import os
import hashlib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'gdpr_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

from data_deletion_service import DataDeletionService
from errors import GDPRError


@pytest.fixture
def mock_aws_services():
    """Fixture providing mocked AWS services"""
    with patch('boto3.resource') as mock_dynamodb, \
         patch('boto3.client') as mock_client:
        
        # Mock DynamoDB resource
        mock_table = MagicMock()
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        # Mock clients (S3, Cognito, SNS)
        mock_s3 = MagicMock()
        mock_cognito = MagicMock()
        mock_sns = MagicMock()
        
        def get_client(service_name):
            if service_name == 's3':
                return mock_s3
            elif service_name == 'cognito-idp':
                return mock_cognito
            elif service_name == 'sns':
                return mock_sns
            return MagicMock()
        
        mock_client.side_effect = get_client
        
        yield {
            'dynamodb': mock_dynamodb,
            'table': mock_table,
            's3': mock_s3,
            'cognito': mock_cognito,
            'sns': mock_sns,
            'client': mock_client
        }


@pytest.fixture
def deletion_service(mock_aws_services):
    """Fixture providing DataDeletionService instance"""
    with patch.dict(os.environ, {
        'USERS_TABLE': 'test-users',
        'DEVICES_TABLE': 'test-devices',
        'READINGS_TABLE': 'test-readings',
        'ALERTS_TABLE': 'test-alerts',
        'AUDIT_LOGS_TABLE': 'test-audit-logs',
        'SERVICE_REQUESTS_TABLE': 'test-service-requests',
        'USER_CONSENTS_TABLE': 'test-user-consents',
        'USER_POOL_ID': 'us-east-1_test123',
        'COMPLIANCE_BUCKET': 'test-compliance-bucket',
        'NOTIFICATION_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789:test-topic'
    }):
        return DataDeletionService()


@pytest.fixture
def sample_devices():
    """Fixture providing sample device data"""
    return [
        {
            'device_id': 'device-1',
            'user_id': 'user-123',
            'name': 'Water Sensor 1'
        },
        {
            'device_id': 'device-2',
            'user_id': 'user-123',
            'name': 'Water Sensor 2'
        }
    ]


@pytest.fixture
def sample_readings():
    """Fixture providing sample sensor readings"""
    return [
        {
            'readingId': 'reading-1',
            'deviceId': 'device-1',
            'timestamp': '2025-10-25T12:00:00Z'
        },
        {
            'readingId': 'reading-2',
            'deviceId': 'device-1',
            'timestamp': '2025-10-25T13:00:00Z'
        }
    ]


@pytest.fixture
def sample_audit_logs():
    """Fixture providing sample audit logs"""
    return [
        {
            'log_id': 'log-1',
            'user_id': 'user-123',
            'timestamp': '2025-10-25T12:00:00Z',
            'action_type': 'LOGIN'
        },
        {
            'log_id': 'log-2',
            'user_id': 'user-123',
            'timestamp': '2025-10-25T13:00:00Z',
            'action_type': 'DATA_ACCESS'
        }
    ]


class TestDataDeletionService:
    """Test suite for DataDeletionService"""
    
    def test_initialization(self, deletion_service):
        """Test service initialization"""
        assert deletion_service is not None
        assert deletion_service.users_table_name == 'test-users'
        assert deletion_service.compliance_bucket == 'test-compliance-bucket'
        assert deletion_service.user_pool_id == 'us-east-1_test123'
    
    def test_delete_user_profile_success(self, deletion_service, mock_aws_services):
        """Test successful user profile deletion"""
        mock_aws_services['table'].delete_item.return_value = {
            'Attributes': {'userId': 'user-123'}
        }
        
        result = deletion_service._delete_user_profile('user-123')
        
        assert result == 1
        mock_aws_services['table'].delete_item.assert_called_once()
    
    def test_delete_user_profile_not_found(self, deletion_service, mock_aws_services):
        """Test user profile deletion when user not found"""
        mock_aws_services['table'].delete_item.return_value = {}
        
        result = deletion_service._delete_user_profile('user-999')
        
        assert result == 0
    
    def test_delete_user_profile_error(self, deletion_service, mock_aws_services):
        """Test user profile deletion with database error"""
        mock_aws_services['table'].delete_item.side_effect = Exception('Database error')
        
        result = deletion_service._delete_user_profile('user-123')
        
        assert result == 0
    
    def test_delete_user_devices_success(self, deletion_service, mock_aws_services, sample_devices):
        """Test successful device deletion"""
        mock_aws_services['table'].query.return_value = {
            'Items': sample_devices
        }
        mock_aws_services['table'].delete_item.return_value = {}
        
        result = deletion_service._delete_user_devices('user-123')
        
        assert result == 2
        assert mock_aws_services['table'].delete_item.call_count == 2
    
    def test_delete_user_devices_empty(self, deletion_service, mock_aws_services):
        """Test device deletion with no devices"""
        mock_aws_services['table'].query.return_value = {
            'Items': []
        }
        
        result = deletion_service._delete_user_devices('user-123')
        
        assert result == 0
    
    def test_delete_user_devices_partial_failure(self, deletion_service, mock_aws_services, sample_devices):
        """Test device deletion with partial failures"""
        mock_aws_services['table'].query.return_value = {
            'Items': sample_devices
        }
        # First delete succeeds, second fails
        mock_aws_services['table'].delete_item.side_effect = [
            {},
            Exception('Delete failed')
        ]
        
        result = deletion_service._delete_user_devices('user-123')
        
        assert result == 1
    
    def test_delete_sensor_readings_success(self, deletion_service, mock_aws_services, sample_devices, sample_readings):
        """Test successful sensor readings deletion"""
        # Mock device query
        devices_table = MagicMock()
        devices_table.query.return_value = {'Items': sample_devices}
        
        # Mock readings query
        readings_table = MagicMock()
        readings_table.query.return_value = {'Items': sample_readings}
        readings_table.delete_item.return_value = {}
        
        # Setup table routing
        def get_table(table_name):
            if 'devices' in table_name.lower():
                return devices_table
            elif 'readings' in table_name.lower():
                return readings_table
            return MagicMock()
        
        mock_aws_services['dynamodb'].return_value.Table.side_effect = get_table
        
        result = deletion_service._delete_sensor_readings('user-123')
        
        assert result >= 2
    
    def test_delete_sensor_readings_no_devices(self, deletion_service, mock_aws_services):
        """Test sensor readings deletion with no devices"""
        devices_table = MagicMock()
        devices_table.query.return_value = {'Items': []}
        
        mock_aws_services['dynamodb'].return_value.Table.return_value = devices_table
        
        result = deletion_service._delete_sensor_readings('user-123')
        
        assert result == 0
    
    def test_delete_sensor_readings_with_pagination(self, deletion_service, mock_aws_services, sample_devices, sample_readings):
        """Test sensor readings deletion with pagination"""
        devices_table = MagicMock()
        devices_table.query.return_value = {'Items': sample_devices}
        
        readings_table = MagicMock()
        # Mock paginated response
        readings_table.query.side_effect = [
            {
                'Items': sample_readings[:1],
                'LastEvaluatedKey': {'readingId': 'reading-1'}
            },
            {
                'Items': sample_readings[1:]
            }
        ]
        readings_table.delete_item.return_value = {}
        
        def get_table(table_name):
            if 'devices' in table_name.lower():
                return devices_table
            elif 'readings' in table_name.lower():
                return readings_table
            return MagicMock()
        
        mock_aws_services['dynamodb'].return_value.Table.side_effect = get_table
        
        result = deletion_service._delete_sensor_readings('user-123')
        
        assert result >= 2
    
    def test_delete_user_alerts_success(self, deletion_service, mock_aws_services, sample_devices):
        """Test successful alerts deletion"""
        sample_alerts = [
            {'alertId': 'alert-1', 'deviceId': 'device-1'},
            {'alertId': 'alert-2', 'deviceId': 'device-1'}
        ]
        
        devices_table = MagicMock()
        devices_table.query.return_value = {'Items': sample_devices}
        
        alerts_table = MagicMock()
        alerts_table.query.return_value = {'Items': sample_alerts}
        alerts_table.delete_item.return_value = {}
        
        def get_table(table_name):
            if 'devices' in table_name.lower():
                return devices_table
            elif 'alerts' in table_name.lower():
                return alerts_table
            return MagicMock()
        
        mock_aws_services['dynamodb'].return_value.Table.side_effect = get_table
        
        result = deletion_service._delete_user_alerts('user-123')
        
        assert result >= 2
    
    def test_delete_service_requests_success(self, deletion_service, mock_aws_services):
        """Test successful service requests deletion"""
        sample_requests = [
            {'requestId': 'req-1', 'consumerId': 'user-123'},
            {'requestId': 'req-2', 'consumerId': 'user-123'}
        ]
        
        mock_aws_services['table'].query.return_value = {
            'Items': sample_requests
        }
        mock_aws_services['table'].delete_item.return_value = {}
        
        result = deletion_service._delete_service_requests('user-123')
        
        assert result >= 2
    
    def test_delete_user_consents_success(self, deletion_service, mock_aws_services):
        """Test successful user consents deletion"""
        mock_aws_services['table'].delete_item.return_value = {
            'Attributes': {'user_id': 'user-123'}
        }
        
        result = deletion_service._delete_user_consents('user-123')
        
        assert result == 1
    
    def test_anonymize_audit_logs_success(self, deletion_service, mock_aws_services, sample_audit_logs):
        """Test successful audit logs anonymization"""
        mock_aws_services['table'].query.return_value = {
            'Items': sample_audit_logs
        }
        mock_aws_services['table'].update_item.return_value = {}
        
        result = deletion_service._anonymize_audit_logs('user-123')
        
        assert result == 2
        assert mock_aws_services['table'].update_item.call_count == 2
        
        # Verify anonymized ID format
        call_args = mock_aws_services['table'].update_item.call_args_list[0]
        anon_id = call_args[1]['ExpressionAttributeValues'][':anon_id']
        assert anon_id.startswith('DELETED_')
        assert len(anon_id) == 24  # DELETED_ + 16 hex chars
    
    def test_anonymize_audit_logs_with_pagination(self, deletion_service, mock_aws_services, sample_audit_logs):
        """Test audit logs anonymization with pagination"""
        mock_aws_services['table'].query.side_effect = [
            {
                'Items': sample_audit_logs[:1],
                'LastEvaluatedKey': {'log_id': 'log-1'}
            },
            {
                'Items': sample_audit_logs[1:]
            }
        ]
        mock_aws_services['table'].update_item.return_value = {}
        
        result = deletion_service._anonymize_audit_logs('user-123')
        
        assert result == 2
    
    def test_anonymize_audit_logs_generates_consistent_id(self, deletion_service, mock_aws_services):
        """Test that anonymization generates consistent ID for same user"""
        user_id = 'user-123'
        expected_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        expected_anon_id = f"DELETED_{expected_hash}"
        
        mock_aws_services['table'].query.return_value = {
            'Items': [{'log_id': 'log-1', 'timestamp': '2025-10-25T12:00:00Z'}]
        }
        mock_aws_services['table'].update_item.return_value = {}
        
        deletion_service._anonymize_audit_logs(user_id)
        
        call_args = mock_aws_services['table'].update_item.call_args
        anon_id = call_args[1]['ExpressionAttributeValues'][':anon_id']
        assert anon_id == expected_anon_id
    
    def test_delete_cognito_user_success(self, deletion_service, mock_aws_services):
        """Test successful Cognito user deletion"""
        mock_aws_services['cognito'].admin_delete_user.return_value = {}
        
        result = deletion_service._delete_cognito_user('user-123')
        
        assert result == 1
        mock_aws_services['cognito'].admin_delete_user.assert_called_once_with(
            UserPoolId='us-east-1_test123',
            Username='user-123'
        )
    
    def test_delete_cognito_user_not_found(self, deletion_service, mock_aws_services):
        """Test Cognito user deletion when user not found"""
        from botocore.exceptions import ClientError
        
        error_response = {'Error': {'Code': 'UserNotFoundException'}}
        mock_aws_services['cognito'].exceptions.UserNotFoundException = type('UserNotFoundException', (ClientError,), {})
        mock_aws_services['cognito'].admin_delete_user.side_effect = \
            mock_aws_services['cognito'].exceptions.UserNotFoundException(error_response, 'admin_delete_user')
        
        result = deletion_service._delete_cognito_user('user-999')
        
        assert result == 0
    
    def test_delete_cognito_user_no_pool_configured(self, mock_aws_services):
        """Test Cognito deletion when pool ID not configured"""
        with patch.dict(os.environ, {'USER_POOL_ID': ''}, clear=True):
            service = DataDeletionService()
            
            result = service._delete_cognito_user('user-123')
            
            assert result == 0
    
    def test_store_deletion_record_success(self, deletion_service, mock_aws_services):
        """Test successful deletion record storage"""
        deletion_summary = {
            'deletion_metadata': {
                'user_id': 'user-123',
                'request_id': 'req-123',
                'deletion_date': '2025-10-25T12:00:00Z'
            },
            'deleted_items': {'profile': 1, 'devices': 2}
        }
        
        mock_aws_services['s3'].put_object.return_value = {}
        
        # Should not raise exception
        deletion_service._store_deletion_record(deletion_summary)
        
        mock_aws_services['s3'].put_object.assert_called_once()
        call_args = mock_aws_services['s3'].put_object.call_args
        assert call_args[1]['Bucket'] == 'test-compliance-bucket'
        assert 'gdpr-deletions' in call_args[1]['Key']
    
    def test_store_deletion_record_no_bucket(self, mock_aws_services):
        """Test deletion record storage when bucket not configured"""
        with patch.dict(os.environ, {'COMPLIANCE_BUCKET': ''}, clear=True):
            service = DataDeletionService()
            
            deletion_summary = {
                'deletion_metadata': {
                    'user_id': 'user-123',
                    'request_id': 'req-123'
                }
            }
            
            # Should not raise exception
            service._store_deletion_record(deletion_summary)
    
    def test_notify_user_success(self, deletion_service, mock_aws_services):
        """Test successful user notification"""
        deletion_summary = {
            'deleted_items': {'profile': 1, 'devices': 2},
            'anonymized_items': {'audit_logs': 5}
        }
        
        mock_aws_services['sns'].publish.return_value = {}
        
        # Should not raise exception
        deletion_service._notify_user(
            user_id='user-123',
            user_email='test@example.com',
            deletion_summary=deletion_summary,
            request_id='req-123'
        )
        
        mock_aws_services['sns'].publish.assert_called_once()
    
    def test_notify_user_failure(self, deletion_service, mock_aws_services):
        """Test notification failure (should not fail deletion)"""
        deletion_summary = {
            'deleted_items': {},
            'anonymized_items': {}
        }
        
        mock_aws_services['sns'].publish.side_effect = Exception('SNS error')
        
        # Should not raise exception even if notification fails
        deletion_service._notify_user(
            user_id='user-123',
            user_email='test@example.com',
            deletion_summary=deletion_summary,
            request_id='req-123'
        )
    
    @patch('data_deletion_service.datetime')
    def test_delete_user_data_success(self, mock_datetime, deletion_service, mock_aws_services):
        """Test successful complete data deletion"""
        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-10-25T12:00:00Z'
        
        # Mock all deletion methods
        with patch.object(deletion_service, '_delete_user_profile', return_value=1), \
             patch.object(deletion_service, '_delete_user_devices', return_value=2), \
             patch.object(deletion_service, '_delete_sensor_readings', return_value=10), \
             patch.object(deletion_service, '_delete_user_alerts', return_value=3), \
             patch.object(deletion_service, '_delete_service_requests', return_value=1), \
             patch.object(deletion_service, '_delete_user_consents', return_value=1), \
             patch.object(deletion_service, '_anonymize_audit_logs', return_value=5), \
             patch.object(deletion_service, '_delete_cognito_user', return_value=1), \
             patch.object(deletion_service, '_store_deletion_record'), \
             patch.object(deletion_service, '_notify_user'):
            
            result = deletion_service.delete_user_data(
                user_id='user-123',
                request_id='req-123',
                user_email='test@example.com'
            )
            
            assert result['deletion_metadata']['user_id'] == 'user-123'
            assert result['deleted_items']['profile'] == 1
            assert result['deleted_items']['devices'] == 2
            assert result['deleted_items']['readings'] == 10
            assert result['deleted_items']['alerts'] == 3
            assert result['deleted_items']['service_requests'] == 1
            assert result['deleted_items']['consents'] == 1
            assert result['deleted_items']['cognito_account'] == 1
            assert result['anonymized_items']['audit_logs'] == 5
    
    def test_delete_user_data_partial_failure(self, deletion_service, mock_aws_services):
        """Test data deletion with partial failures"""
        with patch.object(deletion_service, '_delete_user_profile', return_value=1), \
             patch.object(deletion_service, '_delete_user_devices', side_effect=Exception('Device deletion failed')), \
             patch.object(deletion_service, '_delete_sensor_readings', return_value=0), \
             patch.object(deletion_service, '_delete_user_alerts', return_value=0), \
             patch.object(deletion_service, '_delete_service_requests', return_value=0), \
             patch.object(deletion_service, '_delete_user_consents', return_value=0), \
             patch.object(deletion_service, '_anonymize_audit_logs', return_value=0), \
             patch.object(deletion_service, '_delete_cognito_user', return_value=0), \
             patch.object(deletion_service, '_store_deletion_record'), \
             patch.object(deletion_service, '_notify_user'):
            
            with pytest.raises(GDPRError) as exc_info:
                deletion_service.delete_user_data(
                    user_id='user-123',
                    request_id='req-123'
                )
            
            assert 'Failed to delete user data' in str(exc_info.value)


class TestDeletionDataStructure:
    """Test suite for deletion summary structure validation"""
    
    def test_deletion_summary_structure(self, deletion_service, mock_aws_services):
        """Test that deletion summary contains all required sections"""
        with patch.object(deletion_service, '_delete_user_profile', return_value=1), \
             patch.object(deletion_service, '_delete_user_devices', return_value=2), \
             patch.object(deletion_service, '_delete_sensor_readings', return_value=10), \
             patch.object(deletion_service, '_delete_user_alerts', return_value=3), \
             patch.object(deletion_service, '_delete_service_requests', return_value=1), \
             patch.object(deletion_service, '_delete_user_consents', return_value=1), \
             patch.object(deletion_service, '_anonymize_audit_logs', return_value=5), \
             patch.object(deletion_service, '_delete_cognito_user', return_value=1), \
             patch.object(deletion_service, '_notify_user'):
            
            # Capture the deletion summary
            captured_summary = None
            
            def capture_summary(summary):
                nonlocal captured_summary
                captured_summary = summary
            
            with patch.object(deletion_service, '_store_deletion_record', side_effect=capture_summary):
                result = deletion_service.delete_user_data(
                    user_id='user-123',
                    request_id='req-123'
                )
                
                # Verify structure
                assert 'deletion_metadata' in result
                assert 'deleted_items' in result
                assert 'anonymized_items' in result
                assert 'errors' in result
                
                # Verify metadata
                assert 'deletion_date' in result['deletion_metadata']
                assert 'user_id' in result['deletion_metadata']
                assert 'request_id' in result['deletion_metadata']
                assert 'format_version' in result['deletion_metadata']
                
                # Verify deleted items
                assert 'profile' in result['deleted_items']
                assert 'devices' in result['deleted_items']
                assert 'readings' in result['deleted_items']
                assert 'alerts' in result['deleted_items']
                assert 'service_requests' in result['deleted_items']
                assert 'consents' in result['deleted_items']
                assert 'cognito_account' in result['deleted_items']
                
                # Verify anonymized items
                assert 'audit_logs' in result['anonymized_items']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
