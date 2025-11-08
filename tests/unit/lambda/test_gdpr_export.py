"""
Unit tests for GDPR data export service
Target: 80% code coverage
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'gdpr_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

from data_export_service import DataExportService
from errors import GDPRError, DatabaseError


@pytest.fixture
def mock_aws_services():
    """Fixture providing mocked AWS services"""
    with patch('boto3.resource') as mock_dynamodb, \
         patch('boto3.client') as mock_client:
        
        # Mock DynamoDB resource
        mock_table = MagicMock()
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        
        yield {
            'dynamodb': mock_dynamodb,
            'table': mock_table,
            's3': mock_s3,
            'client': mock_client
        }


@pytest.fixture
def export_service(mock_aws_services):
    """Fixture providing DataExportService instance"""
    with patch.dict(os.environ, {
        'USERS_TABLE': 'test-users',
        'DEVICES_TABLE': 'test-devices',
        'READINGS_TABLE': 'test-readings',
        'ALERTS_TABLE': 'test-alerts',
        'AUDIT_LOGS_TABLE': 'test-audit-logs',
        'SERVICE_REQUESTS_TABLE': 'test-service-requests',
        'EXPORT_BUCKET': 'test-export-bucket',
        'NOTIFICATION_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789:test-topic'
    }):
        return DataExportService()


@pytest.fixture
def sample_user_data():
    """Fixture providing sample user data"""
    return {
        'userId': 'user-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'role': 'consumer',
        'created_at': '2025-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_devices():
    """Fixture providing sample device data"""
    return [
        {
            'device_id': 'device-1',
            'user_id': 'user-123',
            'name': 'Water Sensor 1',
            'status': 'active',
            'created_at': '2025-01-01T00:00:00Z'
        },
        {
            'device_id': 'device-2',
            'user_id': 'user-123',
            'name': 'Water Sensor 2',
            'status': 'active',
            'created_at': '2025-01-02T00:00:00Z'
        }
    ]


@pytest.fixture
def sample_readings():
    """Fixture providing sample sensor readings"""
    return [
        {
            'deviceId': 'device-1',
            'timestamp': '2025-10-25T12:00:00Z',
            'readings': {
                'pH': Decimal('7.2'),
                'turbidity': Decimal('5.0'),
                'temperature': Decimal('25.0')
            }
        },
        {
            'deviceId': 'device-1',
            'timestamp': '2025-10-25T13:00:00Z',
            'readings': {
                'pH': Decimal('7.3'),
                'turbidity': Decimal('4.8'),
                'temperature': Decimal('25.5')
            }
        }
    ]


class TestDataExportService:
    """Test suite for DataExportService"""
    
    def test_initialization(self, export_service):
        """Test service initialization"""
        assert export_service is not None
        assert export_service.users_table_name == 'test-users'
        assert export_service.export_bucket == 'test-export-bucket'
    
    def test_get_user_profile_success(self, export_service, mock_aws_services, sample_user_data):
        """Test successful user profile retrieval"""
        mock_aws_services['table'].get_item.return_value = {
            'Item': sample_user_data
        }
        
        result = export_service._get_user_profile('user-123')
        
        assert result == sample_user_data
        mock_aws_services['table'].get_item.assert_called_once()
    
    def test_get_user_profile_not_found(self, export_service, mock_aws_services):
        """Test user profile retrieval when user not found"""
        mock_aws_services['table'].get_item.return_value = {}
        
        result = export_service._get_user_profile('user-999')
        
        assert result == {}
    
    def test_get_user_profile_error(self, export_service, mock_aws_services):
        """Test user profile retrieval with database error"""
        mock_aws_services['table'].get_item.side_effect = Exception('Database error')
        
        result = export_service._get_user_profile('user-123')
        
        assert 'error' in result
        assert 'Failed to retrieve profile' in result['error']
    
    def test_get_user_devices_success(self, export_service, mock_aws_services, sample_devices):
        """Test successful device retrieval"""
        mock_aws_services['table'].query.return_value = {
            'Items': sample_devices
        }
        
        result = export_service._get_user_devices('user-123')
        
        assert len(result) == 2
        assert result[0]['device_id'] == 'device-1'
        mock_aws_services['table'].query.assert_called_once()
    
    def test_get_user_devices_empty(self, export_service, mock_aws_services):
        """Test device retrieval with no devices"""
        mock_aws_services['table'].query.return_value = {
            'Items': []
        }
        
        result = export_service._get_user_devices('user-123')
        
        assert result == []
    
    def test_get_sensor_readings_success(self, export_service, mock_aws_services, sample_devices, sample_readings):
        """Test successful sensor readings retrieval"""
        # Mock device query
        with patch.object(export_service, '_get_user_devices', return_value=sample_devices):
            # Mock readings query
            mock_aws_services['table'].query.return_value = {
                'Items': sample_readings
            }
            
            result = export_service._get_sensor_readings('user-123')
            
            assert len(result) >= 2
    
    def test_get_sensor_readings_with_pagination(self, export_service, mock_aws_services, sample_devices, sample_readings):
        """Test sensor readings retrieval with pagination"""
        with patch.object(export_service, '_get_user_devices', return_value=sample_devices):
            # Mock paginated response
            mock_aws_services['table'].query.side_effect = [
                {
                    'Items': sample_readings[:1],
                    'LastEvaluatedKey': {'deviceId': 'device-1', 'timestamp': '2025-10-25T12:00:00Z'}
                },
                {
                    'Items': sample_readings[1:]
                }
            ]
            
            result = export_service._get_sensor_readings('user-123')
            
            assert len(result) >= 2
    
    def test_get_sensor_readings_no_devices(self, export_service, mock_aws_services):
        """Test sensor readings retrieval with no devices"""
        with patch.object(export_service, '_get_user_devices', return_value=[]):
            result = export_service._get_sensor_readings('user-123')
            
            assert result == []
    
    def test_get_user_alerts_success(self, export_service, mock_aws_services, sample_devices):
        """Test successful alerts retrieval"""
        sample_alerts = [
            {
                'alertId': 'alert-1',
                'deviceId': 'device-1',
                'alertLevel': 'warning',
                'message': 'pH level high'
            }
        ]
        
        with patch.object(export_service, '_get_user_devices', return_value=sample_devices):
            mock_aws_services['table'].query.return_value = {
                'Items': sample_alerts
            }
            
            result = export_service._get_user_alerts('user-123')
            
            assert len(result) >= 1
    
    def test_get_service_requests_success(self, export_service, mock_aws_services):
        """Test successful service requests retrieval"""
        sample_requests = [
            {
                'requestId': 'req-1',
                'consumerId': 'user-123',
                'status': 'pending'
            }
        ]
        
        mock_aws_services['table'].query.return_value = {
            'Items': sample_requests
        }
        
        result = export_service._get_service_requests('user-123')
        
        assert len(result) >= 1
    
    def test_get_audit_logs_success(self, export_service, mock_aws_services):
        """Test successful audit logs retrieval"""
        sample_logs = [
            {
                'log_id': 'log-1',
                'user_id': 'user-123',
                'action_type': 'LOGIN',
                'timestamp': '2025-10-25T12:00:00Z'
            }
        ]
        
        mock_aws_services['table'].query.return_value = {
            'Items': sample_logs
        }
        
        result = export_service._get_audit_logs('user-123')
        
        assert len(result) == 1
    
    def test_get_audit_logs_table_not_exists(self, export_service, mock_aws_services):
        """Test audit logs retrieval when table doesn't exist"""
        mock_aws_services['table'].query.side_effect = Exception('Table not found')
        
        result = export_service._get_audit_logs('user-123')
        
        assert result == []
    
    @patch('data_export_service.datetime')
    def test_export_user_data_success(self, mock_datetime, export_service, mock_aws_services, sample_user_data):
        """Test successful complete data export"""
        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2025-10-25T12:00:00Z'
        
        # Mock all data retrieval methods
        with patch.object(export_service, '_get_user_profile', return_value=sample_user_data), \
             patch.object(export_service, '_get_user_devices', return_value=[]), \
             patch.object(export_service, '_get_sensor_readings', return_value=[]), \
             patch.object(export_service, '_get_user_alerts', return_value=[]), \
             patch.object(export_service, '_get_service_requests', return_value=[]), \
             patch.object(export_service, '_get_audit_logs', return_value=[]), \
             patch.object(export_service, '_notify_user'):
            
            # Mock S3 operations
            mock_aws_services['s3'].put_object.return_value = {}
            mock_aws_services['s3'].generate_presigned_url.return_value = 'https://s3.amazonaws.com/export.json'
            
            result = export_service.export_user_data(
                user_id='user-123',
                request_id='req-123',
                user_email='test@example.com'
            )
            
            assert result == 'https://s3.amazonaws.com/export.json'
            mock_aws_services['s3'].put_object.assert_called_once()
            mock_aws_services['s3'].generate_presigned_url.assert_called_once()
    
    def test_export_user_data_no_bucket_configured(self, mock_aws_services):
        """Test export failure when bucket not configured"""
        with patch.dict(os.environ, {'EXPORT_BUCKET': ''}, clear=True):
            service = DataExportService()
            
            with pytest.raises(GDPRError) as exc_info:
                service.export_user_data(
                    user_id='user-123',
                    request_id='req-123'
                )
            
            assert 'Export bucket not configured' in str(exc_info.value)
    
    def test_export_user_data_s3_error(self, export_service, mock_aws_services, sample_user_data):
        """Test export failure due to S3 error"""
        with patch.object(export_service, '_get_user_profile', return_value=sample_user_data), \
             patch.object(export_service, '_get_user_devices', return_value=[]), \
             patch.object(export_service, '_get_sensor_readings', return_value=[]), \
             patch.object(export_service, '_get_user_alerts', return_value=[]), \
             patch.object(export_service, '_get_service_requests', return_value=[]), \
             patch.object(export_service, '_get_audit_logs', return_value=[]):
            
            # Mock S3 error
            mock_aws_services['s3'].put_object.side_effect = Exception('S3 error')
            
            with pytest.raises(GDPRError) as exc_info:
                export_service.export_user_data(
                    user_id='user-123',
                    request_id='req-123'
                )
            
            assert 'Failed to export user data' in str(exc_info.value)
    
    def test_notify_user_success(self, export_service, mock_aws_services):
        """Test successful user notification"""
        mock_aws_services['s3'].publish = MagicMock()
        
        # Should not raise exception
        export_service._notify_user(
            user_id='user-123',
            user_email='test@example.com',
            download_url='https://example.com/export.json',
            request_id='req-123'
        )
    
    def test_notify_user_failure(self, export_service, mock_aws_services):
        """Test notification failure (should not fail export)"""
        mock_aws_services['s3'].publish = MagicMock(side_effect=Exception('SNS error'))
        
        # Should not raise exception even if notification fails
        export_service._notify_user(
            user_id='user-123',
            user_email='test@example.com',
            download_url='https://example.com/export.json',
            request_id='req-123'
        )


class TestExportDataStructure:
    """Test suite for export data structure validation"""
    
    def test_export_contains_all_sections(self, export_service, mock_aws_services, sample_user_data):
        """Test that export contains all required data sections"""
        with patch.object(export_service, '_get_user_profile', return_value=sample_user_data), \
             patch.object(export_service, '_get_user_devices', return_value=[]), \
             patch.object(export_service, '_get_sensor_readings', return_value=[]), \
             patch.object(export_service, '_get_user_alerts', return_value=[]), \
             patch.object(export_service, '_get_service_requests', return_value=[]), \
             patch.object(export_service, '_get_audit_logs', return_value=[]), \
             patch.object(export_service, '_notify_user'):
            
            # Capture the export data
            def capture_export(Bucket, Key, Body, **kwargs):
                export_data = json.loads(Body)
                
                # Verify structure
                assert 'export_metadata' in export_data
                assert 'profile' in export_data
                assert 'devices' in export_data
                assert 'sensor_readings' in export_data
                assert 'alerts' in export_data
                assert 'service_requests' in export_data
                assert 'audit_logs' in export_data
                
                # Verify metadata
                assert 'export_date' in export_data['export_metadata']
                assert 'user_id' in export_data['export_metadata']
                assert 'request_id' in export_data['export_metadata']
                assert 'format_version' in export_data['export_metadata']
            
            mock_aws_services['s3'].put_object.side_effect = capture_export
            mock_aws_services['s3'].generate_presigned_url.return_value = 'https://example.com/export.json'
            
            export_service.export_user_data(
                user_id='user-123',
                request_id='req-123'
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
