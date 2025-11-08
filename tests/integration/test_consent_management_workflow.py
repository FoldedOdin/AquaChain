"""
Integration tests for consent management workflow
Tests the complete end-to-end consent management process
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'gdpr_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from consent_service import ConsentService
from consent_handler import (
    update_consent_handler,
    get_consents_handler,
    check_consent_handler,
    get_consent_history_handler,
    bulk_update_consents_handler
)


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'USER_CONSENTS_TABLE': 'test-user-consents',
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
def sample_consent_record():
    """Fixture providing sample consent record"""
    return {
        'user_id': 'user-123',
        'consents': {
            'data_processing': {
                'granted': True,
                'timestamp': '2025-10-25T12:00:00Z',
                'version': '1.0'
            },
            'marketing': {
                'granted': False,
                'timestamp': '2025-10-25T12:00:00Z',
                'version': '1.0'
            },
            'analytics': {
                'granted': True,
                'timestamp': '2025-10-25T12:00:00Z',
                'version': '1.0'
            },
            'third_party_sharing': {
                'granted': False,
                'timestamp': '2025-10-25T12:00:00Z',
                'version': '1.0'
            }
        },
        'consent_history': [
            {
                'consent_type': 'data_processing',
                'action': 'granted',
                'timestamp': '2025-10-25T12:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'request_id': 'req-123'
            }
        ],
        'updated_at': '2025-10-25T12:00:00Z',
        'created_at': '2025-10-25T12:00:00Z'
    }


class TestConsentUpdateWorkflow:
    """Test suite for consent update workflow"""
    
    def test_update_single_consent_grant(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test granting a single consent"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'consent_type': 'marketing',
                'granted': True
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'identity': {
                    'sourceIp': '192.168.1.1',
                    'userAgent': 'Mozilla/5.0'
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB update
        updated_record = sample_consent_record.copy()
        updated_record['consents']['marketing']['granted'] = True
        mock_dynamodb.update_item.return_value = {'Attributes': updated_record}
        
        # Execute handler
        response = update_consent_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Consent updated successfully'
        assert 'consent' in body
        
        # Verify DynamoDB was called
        mock_dynamodb.update_item.assert_called_once()
        call_args = mock_dynamodb.update_item.call_args
        assert call_args[1]['Key'] == {'user_id': 'user-123'}
    
    def test_update_single_consent_revoke(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test revoking a single consent"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'consent_type': 'data_processing',
                'granted': False
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'identity': {
                    'sourceIp': '192.168.1.1',
                    'userAgent': 'Mozilla/5.0'
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB update
        updated_record = sample_consent_record.copy()
        updated_record['consents']['data_processing']['granted'] = False
        mock_dynamodb.update_item.return_value = {'Attributes': updated_record}
        
        # Execute handler
        response = update_consent_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Consent updated successfully'
    
    def test_update_consent_invalid_type(self, mock_aws_environment, mock_dynamodb):
        """Test updating consent with invalid type"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'consent_type': 'invalid_type',
                'granted': True
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'identity': {
                    'sourceIp': '192.168.1.1',
                    'userAgent': 'Mozilla/5.0'
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB to raise ValueError
        mock_dynamodb.update_item.side_effect = ValueError("Invalid consent type")
        
        # Execute handler
        response = update_consent_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_bulk_update_consents(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test bulk updating multiple consents"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'consents': {
                    'data_processing': True,
                    'marketing': True,
                    'analytics': False,
                    'third_party_sharing': False
                }
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'identity': {
                    'sourceIp': '192.168.1.1',
                    'userAgent': 'Mozilla/5.0'
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB operations
        mock_dynamodb.update_item.return_value = {'Attributes': sample_consent_record}
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = bulk_update_consents_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Consents updated successfully'
        assert 'consents' in body
        
        # Verify multiple updates were made
        assert mock_dynamodb.update_item.call_count == 4


class TestConsentRetrievalWorkflow:
    """Test suite for consent retrieval workflow"""
    
    def test_get_all_consents(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test retrieving all user consents"""
        # Mock API Gateway event
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = get_consents_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'user-123'
        assert 'consents' in body
        assert len(body['consents']) == 4
    
    def test_get_all_consents_no_record(self, mock_aws_environment, mock_dynamodb):
        """Test retrieving consents when no record exists"""
        # Mock API Gateway event
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-456'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get - no item
        mock_dynamodb.get_item.return_value = {}
        
        # Execute handler
        response = get_consents_handler(event, context)
        
        # Verify response with defaults
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'user-456'
        assert 'consents' in body
        # All consents should default to False
        for consent_type, consent_data in body['consents'].items():
            assert consent_data['granted'] is False
    
    def test_check_specific_consent_granted(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test checking a specific consent that is granted"""
        # Mock API Gateway event
        event = {
            'queryStringParameters': {
                'consent_type': 'data_processing'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = check_consent_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['consent_type'] == 'data_processing'
        assert body['granted'] is True
    
    def test_check_specific_consent_revoked(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test checking a specific consent that is revoked"""
        # Mock API Gateway event
        event = {
            'queryStringParameters': {
                'consent_type': 'marketing'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = check_consent_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['consent_type'] == 'marketing'
        assert body['granted'] is False


class TestConsentHistoryWorkflow:
    """Test suite for consent history tracking"""
    
    def test_get_consent_history_all(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test retrieving complete consent history"""
        # Add more history entries
        sample_consent_record['consent_history'].extend([
            {
                'consent_type': 'marketing',
                'action': 'granted',
                'timestamp': '2025-10-25T13:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'request_id': 'req-124'
            },
            {
                'consent_type': 'marketing',
                'action': 'revoked',
                'timestamp': '2025-10-25T14:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'request_id': 'req-125'
            }
        ])
        
        # Mock API Gateway event
        event = {
            'queryStringParameters': {},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = get_consent_history_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'history' in body
        assert body['count'] == 3
        assert len(body['history']) == 3
    
    def test_get_consent_history_filtered(self, mock_aws_environment, mock_dynamodb, sample_consent_record):
        """Test retrieving consent history filtered by type"""
        # Add more history entries
        sample_consent_record['consent_history'].extend([
            {
                'consent_type': 'marketing',
                'action': 'granted',
                'timestamp': '2025-10-25T13:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'request_id': 'req-124'
            },
            {
                'consent_type': 'analytics',
                'action': 'granted',
                'timestamp': '2025-10-25T14:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'request_id': 'req-125'
            }
        ])
        
        # Mock API Gateway event
        event = {
            'queryStringParameters': {
                'consent_type': 'marketing'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'requestId': 'req-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock DynamoDB get
        mock_dynamodb.get_item.return_value = {'Item': sample_consent_record}
        
        # Execute handler
        response = get_consent_history_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'history' in body
        # Should only return marketing consent history
        assert body['count'] == 1
        assert body['history'][0]['consent_type'] == 'marketing'
    
    def test_consent_history_tracks_metadata(self, mock_aws_environment, mock_dynamodb):
        """Test that consent history tracks IP, user agent, and request ID"""
        # Mock API Gateway event
        event = {
            'body': json.dumps({
                'consent_type': 'analytics',
                'granted': True
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                },
                'identity': {
                    'sourceIp': '203.0.113.42',
                    'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                },
                'requestId': 'req-unique-123'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-unique-123'
        
        # Capture the update call
        update_calls = []
        
        def capture_update(*args, **kwargs):
            update_calls.append(kwargs)
            return {'Attributes': {'user_id': 'user-123', 'consents': {}}}
        
        mock_dynamodb.update_item.side_effect = capture_update
        
        # Execute handler
        response = update_consent_handler(event, context)
        
        # Verify metadata was captured
        assert len(update_calls) == 1
        update_call = update_calls[0]
        history_entry = update_call['ExpressionAttributeValues'][':history_entry'][0]
        
        assert history_entry['ip_address'] == '203.0.113.42'
        assert history_entry['user_agent'] == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        assert history_entry['request_id'] == 'req-unique-123'


class TestConsentEnforcementWorkflow:
    """Test suite for consent enforcement in data processing"""
    
    def test_consent_enforcement_data_processing(self, mock_aws_environment, mock_dynamodb):
        """Test that data processing checks consent"""
        from consent_service import ConsentService
        
        service = ConsentService()
        
        # Mock consent check - granted
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'user_id': 'user-123',
                'consents': {
                    'data_processing': {
                        'granted': True,
                        'timestamp': '2025-10-25T12:00:00Z',
                        'version': '1.0'
                    }
                }
            }
        }
        
        # Check consent
        has_consent = service.check_consent('user-123', 'data_processing')
        assert has_consent is True
    
    def test_consent_enforcement_marketing(self, mock_aws_environment, mock_dynamodb):
        """Test that marketing checks consent"""
        from consent_service import ConsentService
        
        service = ConsentService()
        
        # Mock consent check - revoked
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'user_id': 'user-123',
                'consents': {
                    'marketing': {
                        'granted': False,
                        'timestamp': '2025-10-25T12:00:00Z',
                        'version': '1.0'
                    }
                }
            }
        }
        
        # Check consent
        has_consent = service.check_consent('user-123', 'marketing')
        assert has_consent is False
    
    def test_consent_enforcement_no_record_defaults_false(self, mock_aws_environment, mock_dynamodb):
        """Test that missing consent record defaults to False (deny)"""
        from consent_service import ConsentService
        
        service = ConsentService()
        
        # Mock no consent record
        mock_dynamodb.get_item.return_value = {}
        
        # Check consent - should default to False
        has_consent = service.check_consent('user-456', 'data_processing')
        assert has_consent is False


class TestCompleteConsentWorkflow:
    """Test suite for complete end-to-end consent workflow"""
    
    def test_complete_consent_lifecycle(self, mock_aws_environment, mock_dynamodb):
        """Test complete consent lifecycle from initialization to revocation"""
        from consent_service import ConsentService
        
        service = ConsentService()
        user_id = 'user-789'
        
        # Step 1: Initialize consents for new user
        mock_dynamodb.put_item.return_value = {}
        
        initial_consents = service.initialize_consents(user_id)
        
        assert initial_consents['user_id'] == user_id
        assert all(
            not consent['granted']
            for consent in initial_consents['consents'].values()
        )
        
        # Step 2: Grant data processing consent
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'user_id': user_id,
                'consents': {
                    'data_processing': {
                        'granted': True,
                        'timestamp': '2025-10-25T12:00:00Z',
                        'version': '1.0'
                    }
                }
            }
        }
        
        metadata = {
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
            'request_id': 'req-1'
        }
        
        updated = service.update_consent(user_id, 'data_processing', True, metadata)
        assert updated['consents']['data_processing']['granted'] is True
        
        # Step 3: Check consent
        mock_dynamodb.get_item.return_value = {
            'Item': updated
        }
        
        has_consent = service.check_consent(user_id, 'data_processing')
        assert has_consent is True
        
        # Step 4: Revoke consent
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'user_id': user_id,
                'consents': {
                    'data_processing': {
                        'granted': False,
                        'timestamp': '2025-10-25T13:00:00Z',
                        'version': '1.0'
                    }
                }
            }
        }
        
        revoked = service.update_consent(user_id, 'data_processing', False, metadata)
        assert revoked['consents']['data_processing']['granted'] is False
        
        # Step 5: Verify consent is now False
        mock_dynamodb.get_item.return_value = {
            'Item': revoked
        }
        
        has_consent = service.check_consent(user_id, 'data_processing')
        assert has_consent is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
