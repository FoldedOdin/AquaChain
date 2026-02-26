"""
Test handler.py severity validation integration for Phase 3a
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from handler import _update_system_configuration


class TestHandlerSeverityValidation:
    """Test severity validation integration in handler"""
    
    @patch('handler.dynamodb')
    @patch('handler._log_config_change')
    @patch('handler._calculate_config_diff')
    def test_valid_severity_thresholds_accepted(self, mock_diff, mock_log, mock_dynamodb):
        """Test that valid severity thresholds pass validation"""
        # Setup
        mock_diff.return_value = {'alertThresholds': 'updated'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {}}
        
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        # Correct: warning_min < critical_min < critical_max < warning_max
                        'critical': {'min': 6.0, 'max': 9.0},  # Stricter (narrower range)
                        'warning': {'min': 5.5, 'max': 9.5}    # Less strict (wider range)
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['sms', 'email'],
                'warningAlertChannels': ['email']
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Configuration updated successfully'
        assert 'version' in body
    
    @patch('handler.dynamodb')
    def test_invalid_severity_relationship_rejected(self, mock_dynamodb):
        """Test that invalid severity relationships are rejected"""
        # Setup - Invalid: critical_min > critical_max (impossible range)
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 9.0, 'max': 6.0},  # Invalid: min > max
                        'warning': {'min': 5.5, 'max': 9.5}
                    }
                }
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'validationErrors' in body
        assert len(body['validationErrors']) > 0
    
    @patch('handler.dynamodb')
    def test_missing_critical_channels_rejected(self, mock_dynamodb):
        """Test that missing critical alert channels are rejected"""
        # Setup
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': [],  # Invalid: no channels
                'warningAlertChannels': ['email']
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'validationErrors' in body
        assert any('critical alert channel' in err.lower() for err in body['validationErrors'])
    
    @patch('handler.dynamodb')
    def test_sms_in_warning_channels_rejected(self, mock_dynamodb):
        """Test that SMS in warning channels is rejected"""
        # Setup
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['sms', 'email'],
                'warningAlertChannels': ['sms', 'email']  # Invalid: SMS not allowed for warnings
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'validationErrors' in body
        assert any('sms' in err.lower() and 'warning' in err.lower() for err in body['validationErrors'])
    
    @patch('handler.dynamodb')
    @patch('handler._log_config_change')
    @patch('handler._calculate_config_diff')
    def test_legacy_format_normalized(self, mock_diff, mock_log, mock_dynamodb):
        """Test that legacy threshold format is automatically normalized"""
        # Setup
        mock_diff.return_value = {'alertThresholds': 'updated'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {}}
        
        # Legacy format (no severity levels)
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}  # Legacy format
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email']
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 200
        
        # Verify that put_item was called with normalized config
        put_call_args = mock_table.put_item.call_args
        saved_config = put_call_args[1]['Item']
        
        # Check that pH now has severity levels
        assert 'critical' in saved_config['alertThresholds']['global']['pH']
        assert 'warning' in saved_config['alertThresholds']['global']['pH']
    
    @patch('handler.dynamodb')
    def test_multiple_validation_errors_collected(self, mock_dynamodb):
        """Test that multiple validation errors are collected and returned together"""
        # Setup - multiple issues
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 9.0, 'max': 6.0},  # Invalid: min > max
                        'warning': {'min': 5.5, 'max': 9.5}
                    },
                    'turbidity': {
                        'critical': {'max': 5.0},
                        'warning': {'max': 10.0}  # Invalid: warning > critical (should be opposite)
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': [],  # Invalid: empty
                'warningAlertChannels': ['sms']  # Invalid: SMS in warnings
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        # Execute
        response = _update_system_configuration(config, query_params)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'validationErrors' in body
        # Should have multiple errors (don't fail fast)
        assert len(body['validationErrors']) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
