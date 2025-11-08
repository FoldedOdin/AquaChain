"""
Integration tests for GDPR data deletion workflow
Tests the complete end-to-end deletion process
"""

import pytest
import json
import sys
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'gdpr_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from data_deletion_service import DataDeletionService
from deletion_handler import handler, process_scheduled_deletions, cancel_deletion_request


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'USERS_TABLE': 'test-users',
        'DEVICES_TABLE': 'test-devices',
        'READINGS_TABLE': 'test-readings',
        'ALERTS_TABLE': 'test-alerts',
        'AUDIT_LOGS_TABLE': 'test-audit-logs',
        'SERVICE_REQUESTS_TABLE': 'test-service-requests',
        'USER_CONSENTS_TABLE': 'test-user-consents',
        'GDPR_REQUESTS_TABLE': 'test-gdpr-requests',
        'USER_POOL_ID': 'us-east-1_test123',
        'COMPLIANCE_BUCKET': 'test-compliance-bucket',
        'NOTIFICATION_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789:test-topic'
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
def mock_clients():
    """Fixture providing mocked AWS clients"""
    with patch('boto3.client') as mock_client:
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
            's3': mock_s3,
            'cognito': mock_cognito,
            'sns': mock_sns
        }


@pytest.fixture
def sample_user_data():
    """Fixture providing complete user data"""
    return {
        'user_id': 'user-123',
        'email': 'test@example.com',
        'devices': [
            {'device_id': 'device-1', 'name': 'Sensor 1'},
            {'device_id': 'device-2', 'name': 'Sensor 2'}
        ],
        'readings': [
            {'readingId': 'reading-1', 'deviceId': 'device-1', 'timestamp': '2025-10-25T12:00:00Z'},
            {'readingId': 'reading-2', 'deviceId': 'device-1', 'timestamp': '2025-10-25T13:00:00Z'}
        ],
        'alerts': [
            {'alertId': 'alert-1', 'deviceId': 'device-1'}
        ],
        'audit_logs': [
            {'log_id': 'log-1', 'user_id': 'user-123', 'timestamp': '2025-10-25T12:00:00Z'}
        ]
    }


class TestDeletionRequestWorkflow:
    """Test suite for deletion request workflow"""
    
    def test_create_deletion_request_pending(self, mock_aws_environment, mock_dynamodb, mock_clients):
        """Test creating a deletion request with 30-day waiting period"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'user_id': 'user-123',
                'email': 'test@example.com',
                'immediate': False
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB operations
        mock_dynamodb.put_item.return_value = {}
        
        # Execute handler
        response = handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 202
        body = json.loads(response['body'])
        assert body['status'] == 'pending'
        assert 'request_id' in body
        assert body['days_until_deletion'] == 30
        assert 'scheduled_deletion_date' in body
        
        # Verify GDPR request was created
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]['Item']
        assert item['request_type'] == 'deletion'
        assert item['status'] == 'pending'
        assert item['user_id'] == 'user-123'
    
    def test_create_deletion_request_immediate(self, mock_aws_environment, mock_dynamodb, mock_clients, sample_user_data):
        """Test creating an immediate deletion request"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'user_id': 'user-123',
                'email': 'test@example.com',
                'immediate': True
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB operations
        mock_dynamodb.put_item.return_value = {}
        mock_dynamodb.update_item.return_value = {}
        mock_dynamodb.query.return_value = {'Items': []}
        mock_dynamodb.delete_item.return_value = {}
        
        # Mock S3 operations
        mock_clients['s3'].put_object.return_value = {}
        
        # Mock Cognito operations
        mock_clients['cognito'].admin_delete_user.return_value = {}
        
        # Execute handler
        response = handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'completed'
        assert 'deletion_summary' in body
        
        # Verify deletion was performed
        mock_clients['cognito'].admin_delete_user.assert_called_once()
    
    def test_create_deletion_request_unauthorized(self, mock_aws_environment, mock_dynamodb):
        """Test creating deletion request for another user (should fail)"""
        # Mock API Gateway event with mismatched user IDs
        event = {
            'body': json.dumps({
                'user_id': 'user-123',
                'email': 'test@example.com'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-456'  # Different user
                    }
                }
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Execute handler
        response = handler(event, context)
        
        # Verify unauthorized response
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'UNAUTHORIZED_DELETION' in body['error']
    
    def test_cancel_deletion_request_success(self, mock_aws_environment, mock_dynamodb):
        """Test cancelling a pending deletion request"""
        # Mock existing deletion request
        existing_request = {
            'request_id': 'req-123',
            'user_id': 'user-123',
            'status': 'pending',
            'created_at': '2025-10-25T12:00:00Z',
            'scheduled_deletion_date': '2025-11-24T12:00:00Z'
        }
        
        # Mock API Gateway event
        event = {
            'pathParameters': {
                'request_id': 'req-123'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        context = MagicMock()
        
        # Mock DynamoDB operations
        mock_dynamodb.query.return_value = {
            'Items': [existing_request]
        }
        mock_dynamodb.update_item.return_value = {}
        
        # Execute handler
        response = cancel_deletion_request(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'cancelled'
        
        # Verify update was called
        mock_dynamodb.update_item.assert_called_once()
        call_args = mock_dynamodb.update_item.call_args
        assert call_args[1]['ExpressionAttributeValues'][':status'] == 'cancelled'
    
    def test_cancel_deletion_request_invalid_status(self, mock_aws_environment, mock_dynamodb):
        """Test cancelling a deletion request that's already processing"""
        # Mock existing deletion request with processing status
        existing_request = {
            'request_id': 'req-123',
            'user_id': 'user-123',
            'status': 'processing',
            'created_at': '2025-10-25T12:00:00Z'
        }
        
        # Mock API Gateway event
        event = {
            'pathParameters': {
                'request_id': 'req-123'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        context = MagicMock()
        
        # Mock DynamoDB operations
        mock_dynamodb.query.return_value = {
            'Items': [existing_request]
        }
        
        # Execute handler
        response = cancel_deletion_request(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'INVALID_STATUS' in body['error']


class TestScheduledDeletionProcessing:
    """Test suite for scheduled deletion processing"""
    
    def test_process_scheduled_deletions_success(self, mock_aws_environment, mock_dynamodb, mock_clients):
        """Test processing scheduled deletions that are due"""
        # Mock pending deletion requests
        current_date = datetime.utcnow()
        past_date = (current_date - timedelta(days=1)).isoformat()
        
        pending_requests = [
            {
                'request_id': 'req-1',
                'user_id': 'user-1',
                'user_email': 'user1@example.com',
                'status': 'pending',
                'created_at': past_date,
                'scheduled_deletion_date': past_date
            },
            {
                'request_id': 'req-2',
                'user_id': 'user-2',
                'user_email': 'user2@example.com',
                'status': 'pending',
                'created_at': past_date,
                'scheduled_deletion_date': past_date
            }
        ]
        
        # Mock EventBridge event
        event = {
            'source': 'aws.events',
            'detail-type': 'Scheduled Event'
        }
        
        context = MagicMock()
        
        # Mock DynamoDB operations
        mock_dynamodb.query.return_value = {
            'Items': pending_requests
        }
        mock_dynamodb.update_item.return_value = {}
        mock_dynamodb.delete_item.return_value = {}
        
        # Mock S3 operations
        mock_clients['s3'].put_object.return_value = {}
        
        # Mock Cognito operations
        mock_clients['cognito'].admin_delete_user.return_value = {}
        
        # Execute handler
        result = process_scheduled_deletions(event, context)
        
        # Verify results
        assert result['processed_count'] == 2
        assert result['failed_count'] == 0
        assert len(result['processed']) == 2
        
        # Verify Cognito deletions were called
        assert mock_clients['cognito'].admin_delete_user.call_count == 2
    
    def test_process_scheduled_deletions_partial_failure(self, mock_aws_environment, mock_dynamodb, mock_clients):
        """Test processing scheduled deletions with some failures"""
        # Mock pending deletion requests
        current_date = datetime.utcnow()
        past_date = (current_date - timedelta(days=1)).isoformat()
        
        pending_requests = [
            {
                'request_id': 'req-1',
                'user_id': 'user-1',
                'user_email': 'user1@example.com',
                'status': 'pending',
                'created_at': past_date,
                'scheduled_deletion_date': past_date
            },
            {
                'request_id': 'req-2',
                'user_id': 'user-2',
                'user_email': 'user2@example.com',
                'status': 'pending',
                'created_at': past_date,
                'scheduled_deletion_date': past_date
            }
        ]
        
        # Mock EventBridge event
        event = {
            'source': 'aws.events',
            'detail-type': 'Scheduled Event'
        }
        
        context = MagicMock()
        
        # Mock DynamoDB operations
        mock_dynamodb.query.return_value = {
            'Items': pending_requests
        }
        mock_dynamodb.update_item.return_value = {}
        mock_dynamodb.delete_item.return_value = {}
        
        # Mock S3 operations
        mock_clients['s3'].put_object.return_value = {}
        
        # Mock Cognito operations - first succeeds, second fails
        mock_clients['cognito'].admin_delete_user.side_effect = [
            {},
            Exception('Cognito error')
        ]
        
        # Execute handler
        result = process_scheduled_deletions(event, context)
        
        # Verify results
        assert result['processed_count'] == 1
        assert result['failed_count'] == 1
        assert len(result['processed']) == 1
        assert len(result['failed']) == 1
    
    def test_process_scheduled_deletions_no_pending(self, mock_aws_environment, mock_dynamodb):
        """Test processing when no deletions are due"""
        # Mock EventBridge event
        event = {
            'source': 'aws.events',
            'detail-type': 'Scheduled Event'
        }
        
        context = MagicMock()
        
        # Mock DynamoDB operations - no pending requests
        mock_dynamodb.query.return_value = {
            'Items': []
        }
        
        # Execute handler
        result = process_scheduled_deletions(event, context)
        
        # Verify results
        assert result['processed_count'] == 0
        assert result['failed_count'] == 0


class TestCompleteDeletionWorkflow:
    """Test suite for complete end-to-end deletion workflow"""
    
    def test_complete_deletion_workflow(self, mock_aws_environment, mock_dynamodb, mock_clients, sample_user_data):
        """Test complete deletion workflow from request to completion"""
        user_id = sample_user_data['user_id']
        user_email = sample_user_data['email']
        
        # Setup mocks for complete user data
        devices_table = MagicMock()
        devices_table.query.return_value = {'Items': sample_user_data['devices']}
        devices_table.delete_item.return_value = {}
        
        readings_table = MagicMock()
        readings_table.query.return_value = {'Items': sample_user_data['readings']}
        readings_table.delete_item.return_value = {}
        
        alerts_table = MagicMock()
        alerts_table.query.return_value = {'Items': sample_user_data['alerts']}
        alerts_table.delete_item.return_value = {}
        
        audit_table = MagicMock()
        audit_table.query.return_value = {'Items': sample_user_data['audit_logs']}
        audit_table.update_item.return_value = {}
        
        users_table = MagicMock()
        users_table.delete_item.return_value = {'Attributes': {'userId': user_id}}
        
        # Setup table routing
        def get_table(table_name):
            if 'devices' in table_name.lower():
                return devices_table
            elif 'readings' in table_name.lower():
                return readings_table
            elif 'alerts' in table_name.lower():
                return alerts_table
            elif 'audit' in table_name.lower():
                return audit_table
            elif 'users' in table_name.lower():
                return users_table
            return MagicMock()
        
        with patch('boto3.resource') as mock_resource:
            mock_resource.return_value.Table.side_effect = get_table
            
            # Mock S3 operations
            mock_clients['s3'].put_object.return_value = {}
            
            # Mock Cognito operations
            mock_clients['cognito'].admin_delete_user.return_value = {}
            
            # Mock SNS operations
            mock_clients['sns'].publish.return_value = {}
            
            # Create deletion service and execute
            service = DataDeletionService()
            result = service.delete_user_data(
                user_id=user_id,
                request_id='req-123',
                user_email=user_email
            )
            
            # Verify deletion summary
            assert result['deletion_metadata']['user_id'] == user_id
            assert result['deleted_items']['profile'] == 1
            assert result['deleted_items']['devices'] == 2
            assert result['deleted_items']['readings'] >= 2
            assert result['deleted_items']['alerts'] >= 1
            assert result['deleted_items']['cognito_account'] == 1
            assert result['anonymized_items']['audit_logs'] >= 1
            
            # Verify Cognito deletion
            mock_clients['cognito'].admin_delete_user.assert_called_once_with(
                UserPoolId='us-east-1_test123',
                Username=user_id
            )
            
            # Verify compliance record stored
            assert mock_clients['s3'].put_object.called
            
            # Verify notification sent
            assert mock_clients['sns'].publish.called
    
    def test_verify_audit_log_anonymization(self, mock_aws_environment, mock_dynamodb, mock_clients):
        """Test that audit logs are properly anonymized"""
        user_id = 'user-123'
        
        # Mock audit logs
        audit_logs = [
            {
                'log_id': 'log-1',
                'user_id': user_id,
                'timestamp': '2025-10-25T12:00:00Z',
                'action_type': 'LOGIN'
            },
            {
                'log_id': 'log-2',
                'user_id': user_id,
                'timestamp': '2025-10-25T13:00:00Z',
                'action_type': 'DATA_ACCESS'
            }
        ]
        
        audit_table = MagicMock()
        audit_table.query.return_value = {'Items': audit_logs}
        
        anonymized_ids = []
        
        def capture_anonymization(*args, **kwargs):
            anon_id = kwargs['ExpressionAttributeValues'][':anon_id']
            anonymized_ids.append(anon_id)
            return {}
        
        audit_table.update_item.side_effect = capture_anonymization
        
        with patch('boto3.resource') as mock_resource:
            mock_resource.return_value.Table.return_value = audit_table
            
            # Create deletion service and anonymize
            service = DataDeletionService()
            count = service._anonymize_audit_logs(user_id)
            
            # Verify anonymization
            assert count == 2
            assert len(anonymized_ids) == 2
            
            # Verify all logs got same anonymized ID
            assert anonymized_ids[0] == anonymized_ids[1]
            
            # Verify anonymized ID format
            assert anonymized_ids[0].startswith('DELETED_')
            assert len(anonymized_ids[0]) == 24  # DELETED_ + 16 hex chars


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
