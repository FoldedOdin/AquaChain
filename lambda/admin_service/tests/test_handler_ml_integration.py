"""
Integration tests for ML settings validation in handler
Tests that the handler properly integrates ML validation
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock AWS services before importing handler
sys.modules['boto3'] = MagicMock()

from handler import _update_system_configuration


class TestHandlerMLIntegration:
    """Test suite for ML settings validation integration in handler"""
    
    @patch('handler.dynamodb')
    @patch('handler._calculate_config_diff')
    @patch('handler._log_config_change')
    def test_valid_ml_settings_accepted(self, mock_log, mock_diff, mock_dynamodb):
        """Test that valid ML settings pass validation and are saved"""
        # Setup mocks
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {}}
        mock_diff.return_value = {'mlSettings': 'updated'}
        
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'confidenceThreshold': 0.85,
                'retrainingFrequencyDays': 30,
                'modelVersion': 'v1.2',
                'anomalyDetectionEnabled': True,
                'driftDetectionEnabled': True
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Configuration updated successfully'
        
        # Verify config was saved with ML settings
        saved_config = mock_table.put_item.call_args[1]['Item']
        assert 'mlSettings' in saved_config
        assert saved_config['mlSettings']['confidenceThreshold'] == 0.85
    
    @patch('handler.dynamodb')
    def test_invalid_ml_confidence_threshold_rejected(self, mock_dynamodb):
        """Test that invalid ML confidence threshold is rejected"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'confidenceThreshold': 1.5  # Invalid: > 1.0
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Configuration validation failed'
        assert len(body['validationErrors']) > 0
        assert any('confidence threshold' in err.lower() for err in body['validationErrors'])
    
    @patch('handler.dynamodb')
    def test_invalid_ml_retraining_frequency_rejected(self, mock_dynamodb):
        """Test that invalid ML retraining frequency is rejected"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'retrainingFrequencyDays': 400  # Invalid: > 365
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Configuration validation failed'
        assert len(body['validationErrors']) > 0
        assert any('retraining frequency' in err.lower() for err in body['validationErrors'])
    
    @patch('handler.dynamodb')
    def test_invalid_ml_model_version_rejected(self, mock_dynamodb):
        """Test that invalid ML model version is rejected"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'modelVersion': ''  # Invalid: empty string
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Configuration validation failed'
        assert len(body['validationErrors']) > 0
        assert any('model version' in err.lower() for err in body['validationErrors'])
    
    @patch('handler.dynamodb')
    @patch('handler._calculate_config_diff')
    @patch('handler._log_config_change')
    def test_default_ml_settings_applied_when_missing(self, mock_log, mock_diff, mock_dynamodb):
        """Test that default ML settings are applied when not provided"""
        # Setup mocks
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {}}
        mock_diff.return_value = {'mlSettings': 'added'}
        
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            }
            # No mlSettings provided
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 200
        
        # Verify default ML settings were applied
        saved_config = mock_table.put_item.call_args[1]['Item']
        assert 'mlSettings' in saved_config
        assert saved_config['mlSettings']['anomalyDetectionEnabled'] is True
        assert saved_config['mlSettings']['confidenceThreshold'] == 0.85
        assert saved_config['mlSettings']['retrainingFrequencyDays'] == 30
        assert saved_config['mlSettings']['driftDetectionEnabled'] is True
    
    @patch('handler.dynamodb')
    def test_multiple_validation_errors_collected(self, mock_dynamodb):
        """Test that multiple ML validation errors are collected and returned"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'confidenceThreshold': 1.5,  # Invalid
                'retrainingFrequencyDays': 0,  # Invalid
                'modelVersion': ''  # Invalid
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Configuration validation failed'
        
        # Should have all three errors
        assert len(body['validationErrors']) >= 3
        error_text = ' '.join(body['validationErrors']).lower()
        assert 'confidence threshold' in error_text
        assert 'retraining frequency' in error_text
        assert 'model version' in error_text
    
    @patch('handler.dynamodb')
    @patch('handler._calculate_config_diff')
    @patch('handler._log_config_change')
    def test_ml_settings_included_in_audit_log(self, mock_log, mock_diff, mock_dynamodb):
        """Test that ML settings changes are included in audit log"""
        # Setup mocks
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {}}
        mock_diff.return_value = {'mlSettings': {'confidenceThreshold': 'changed from 0.85 to 0.90'}}
        
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'confidenceThreshold': 0.90
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 200
        
        # Verify audit log was called with ML changes
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert 'changes' in call_kwargs
        assert 'mlSettings' in call_kwargs['changes']
    
    @patch('handler.dynamodb')
    @patch('handler._calculate_config_diff')
    @patch('handler._log_config_change')
    def test_ml_settings_included_in_version_history(self, mock_log, mock_diff, mock_dynamodb):
        """Test that ML settings are included in version history"""
        # Setup mocks
        mock_config_table = MagicMock()
        mock_history_table = MagicMock()
        
        def table_selector(table_name):
            if 'History' in table_name:
                return mock_history_table
            return mock_config_table
        
        mock_dynamodb.Table.side_effect = table_selector
        mock_config_table.get_item.return_value = {'Item': {}}
        mock_diff.return_value = {'mlSettings': 'updated'}
        
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'critical': {'min': 6.5, 'max': 8.5}, 'warning': {'min': 6.0, 'max': 9.0}}
                }
            },
            'mlSettings': {
                'confidenceThreshold': 0.90
            }
        }
        
        query_params = {'adminId': 'test_admin', 'ipAddress': '127.0.0.1'}
        
        response = _update_system_configuration(config, query_params)
        
        assert response['statusCode'] == 200
        
        # Verify history entry includes ML settings
        history_entry = mock_history_table.put_item.call_args[1]['Item']
        assert 'fullConfig' in history_entry
        assert 'mlSettings' in history_entry['fullConfig']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
