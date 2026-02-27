"""
Unit Tests for ML Configuration Validation Logic (Phase 3b)

Tests cover:
- validate_ml_settings() function
- get_ml_settings() function with defaults
- Edge cases and boundary conditions
- Type validation
- Range validation

Test Coverage:
- Valid ML settings
- Invalid confidence threshold (< 0, > 1)
- Invalid retraining frequency (< 1, > 365)
- Invalid model version (empty string)
- Default values applied correctly
- Type validation for all fields
- Boundary value testing
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_validation import (
    validate_ml_settings,
    get_ml_settings,
    DEFAULT_ML_SETTINGS
)


class TestValidateMLSettings:
    """Test suite for validate_ml_settings function"""
    
    def test_valid_ml_settings_all_fields(self):
        """Test validation passes with all valid ML settings"""
        ml_settings = {
            'anomalyDetectionEnabled': True,
            'modelVersion': 'v1.2.3',
            'confidenceThreshold': 0.85,
            'retrainingFrequencyDays': 30,
            'driftDetectionEnabled': True
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_ml_settings_minimal(self):
        """Test validation passes with minimal valid settings"""
        ml_settings = {
            'confidenceThreshold': 0.75,
            'retrainingFrequencyDays': 7
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_confidence_threshold_boundaries(self):
        """Test confidence threshold at valid boundaries (0.0 and 1.0)"""
        # Test lower boundary
        ml_settings = {'confidenceThreshold': 0.0}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test upper boundary
        ml_settings = {'confidenceThreshold': 1.0}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_retraining_frequency_boundaries(self):
        """Test retraining frequency at valid boundaries (1 and 365)"""
        # Test lower boundary
        ml_settings = {'retrainingFrequencyDays': 1}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test upper boundary
        ml_settings = {'retrainingFrequencyDays': 365}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_confidence_threshold_below_zero(self):
        """Test validation fails when confidence threshold is below 0"""
        ml_settings = {
            'confidenceThreshold': -0.1
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'confidence threshold' in errors[0].lower()
        assert 'must be between 0.0 and 1.0' in errors[0]
        assert '-0.1' in errors[0]
    
    def test_invalid_confidence_threshold_above_one(self):
        """Test validation fails when confidence threshold is above 1"""
        ml_settings = {
            'confidenceThreshold': 1.5
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'confidence threshold' in errors[0].lower()
        assert 'must be between 0.0 and 1.0' in errors[0]
        assert '1.5' in errors[0]
    
    def test_invalid_confidence_threshold_type_string(self):
        """Test validation fails when confidence threshold is a string"""
        ml_settings = {
            'confidenceThreshold': '0.85'
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'confidence threshold must be a number' in errors[0].lower()
        assert 'str' in errors[0]
    
    def test_invalid_confidence_threshold_type_none(self):
        """Test validation fails when confidence threshold is None"""
        ml_settings = {
            'confidenceThreshold': None
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'confidence threshold must be a number' in errors[0].lower()
    
    def test_invalid_retraining_frequency_below_one(self):
        """Test validation fails when retraining frequency is below 1"""
        ml_settings = {
            'retrainingFrequencyDays': 0
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'retraining frequency' in errors[0].lower()
        assert 'between 1 and 365' in errors[0]
    
    def test_retraining_frequency_invalid_type_string(self):
        """Test retraining frequency with invalid type (string) fails validation"""
        ml_settings = {'retrainingFrequencyDays': 'invalid'}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'must be an integer' in errors[0].lower()
    
    def test_retraining_frequency_invalid_type_float(self):
        """Test retraining frequency with float is converted to int"""
        ml_settings = {'retrainingFrequencyDays': 30.5}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        # Float values are converted to int, so 30.5 becomes 30 which is valid
        assert is_valid is True
        assert len(errors) == 0
    
    def test_model_version_valid_string(self):
        """Test model version with valid string passes validation"""
        ml_settings = {'modelVersion': 'v1.2.3'}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_model_version_empty_string(self):
        """Test model version with empty string fails validation"""
        ml_settings = {'modelVersion': ''}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'model version' in errors[0].lower()
        assert 'non-empty string' in errors[0].lower()
    
    def test_model_version_whitespace_only(self):
        """Test model version with whitespace only fails validation"""
        ml_settings = {'modelVersion': '   '}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'model version' in errors[0].lower()
        assert 'empty or whitespace' in errors[0].lower()
    
    def test_model_version_invalid_type_number(self):
        """Test model version with number type fails validation"""
        ml_settings = {'modelVersion': 123}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'model version' in errors[0].lower()
        assert 'non-empty string' in errors[0].lower()
    
    def test_model_version_invalid_type_none(self):
        """Test model version with None fails validation"""
        ml_settings = {'modelVersion': None}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'model version' in errors[0].lower()
        assert 'non-empty string' in errors[0].lower()
    
    def test_multiple_validation_errors(self):
        """Test multiple validation errors are collected"""
        ml_settings = {
            'confidenceThreshold': 1.5,
            'retrainingFrequencyDays': 0,
            'modelVersion': ''
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 3
        
        # Check all three errors are present
        error_text = ' '.join(errors).lower()
        assert 'confidence threshold' in error_text
        assert 'retraining frequency' in error_text
        assert 'model version' in error_text
    
    def test_valid_with_additional_fields(self):
        """Test validation passes with additional fields (forward compatibility)"""
        ml_settings = {
            'confidenceThreshold': 0.85,
            'retrainingFrequencyDays': 30,
            'modelVersion': 'v1.2',
            'anomalyDetectionEnabled': True,
            'driftDetectionEnabled': True,
            'lastDriftScore': 0.023
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_confidence_threshold_integer_value(self):
        """Test confidence threshold with integer value (0 or 1) is accepted"""
        # Test with 0
        ml_settings = {'confidenceThreshold': 0}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test with 1
        ml_settings = {'confidenceThreshold': 1}
        is_valid, errors = validate_ml_settings(ml_settings)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_typical_production_values(self):
        """Test with typical production ML settings"""
        ml_settings = {
            'confidenceThreshold': 0.85,
            'retrainingFrequencyDays': 30,
            'modelVersion': 'v1.2',
            'anomalyDetectionEnabled': True,
            'driftDetectionEnabled': True
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0


class TestBooleanFieldValidation:
    """Test suite for boolean field validation in ML settings"""
    
    def test_anomaly_detection_enabled_valid_true(self):
        """Test anomalyDetectionEnabled with valid boolean True"""
        ml_settings = {'anomalyDetectionEnabled': True}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_anomaly_detection_enabled_valid_false(self):
        """Test anomalyDetectionEnabled with valid boolean False"""
        ml_settings = {'anomalyDetectionEnabled': False}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_anomaly_detection_enabled_invalid_string(self):
        """Test anomalyDetectionEnabled with invalid string type"""
        ml_settings = {'anomalyDetectionEnabled': 'true'}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'anomalydetectionenabled' in errors[0].lower()
        assert 'must be a boolean' in errors[0].lower()
    
    def test_anomaly_detection_enabled_invalid_number(self):
        """Test anomalyDetectionEnabled with invalid number type"""
        ml_settings = {'anomalyDetectionEnabled': 1}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'anomalydetectionenabled' in errors[0].lower()
        assert 'must be a boolean' in errors[0].lower()

    
    def test_drift_detection_enabled_valid_true(self):
        """Test driftDetectionEnabled with valid boolean True"""
        ml_settings = {'driftDetectionEnabled': True}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_drift_detection_enabled_valid_false(self):
        """Test driftDetectionEnabled with valid boolean False"""
        ml_settings = {'driftDetectionEnabled': False}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_drift_detection_enabled_invalid_string(self):
        """Test driftDetectionEnabled with invalid string type"""
        ml_settings = {'driftDetectionEnabled': 'false'}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'driftdetectionenabled' in errors[0].lower()
        assert 'must be a boolean' in errors[0].lower()
    
    def test_drift_detection_enabled_invalid_number(self):
        """Test driftDetectionEnabled with invalid number type"""
        ml_settings = {'driftDetectionEnabled': 0}
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'driftdetectionenabled' in errors[0].lower()
        assert 'must be a boolean' in errors[0].lower()

    
    def test_both_boolean_fields_invalid(self):
        """Test both boolean fields with invalid types"""
        ml_settings = {
            'anomalyDetectionEnabled': 'yes',
            'driftDetectionEnabled': 1
        }
        
        is_valid, errors = validate_ml_settings(ml_settings)
        
        assert is_valid is False
        assert len(errors) == 2
        
        error_text = ' '.join(errors).lower()
        assert 'anomalydetectionenabled' in error_text
        assert 'driftdetectionenabled' in error_text


class TestDefaultMLSettings:
    """Test suite for default ML settings functionality"""
    
    def test_get_ml_settings_with_existing_settings(self):
        """Test get_ml_settings returns existing ML settings when present"""
        config = {
            'mlSettings': {
                'confidenceThreshold': 0.90,
                'retrainingFrequencyDays': 60,
                'modelVersion': 'v2.0',
                'anomalyDetectionEnabled': False,
                'driftDetectionEnabled': True
            }
        }
        
        ml_settings = get_ml_settings(config)
        
        assert ml_settings['confidenceThreshold'] == 0.90
        assert ml_settings['retrainingFrequencyDays'] == 60
        assert ml_settings['modelVersion'] == 'v2.0'
        assert ml_settings['anomalyDetectionEnabled'] is False
        assert ml_settings['driftDetectionEnabled'] is True

    
    def test_get_ml_settings_with_missing_settings(self):
        """Test get_ml_settings returns defaults when ML settings not present"""
        config = {
            'alertThresholds': {},
            'notificationSettings': {}
        }
        
        ml_settings = get_ml_settings(config)
        
        # Should return default values
        assert ml_settings['confidenceThreshold'] == 0.85
        assert ml_settings['retrainingFrequencyDays'] == 30
        assert ml_settings['modelVersion'] == 'latest'
        assert ml_settings['anomalyDetectionEnabled'] is True
        assert ml_settings['driftDetectionEnabled'] is True
    
    def test_get_ml_settings_with_empty_config(self):
        """Test get_ml_settings returns defaults with empty config"""
        config = {}
        
        ml_settings = get_ml_settings(config)
        
        # Should return default values
        assert ml_settings['confidenceThreshold'] == 0.85
        assert ml_settings['retrainingFrequencyDays'] == 30
        assert ml_settings['modelVersion'] == 'latest'
        assert ml_settings['anomalyDetectionEnabled'] is True
        assert ml_settings['driftDetectionEnabled'] is True
    
    def test_default_ml_settings_constant(self):
        """Test DEFAULT_ML_SETTINGS constant has correct values"""
        assert DEFAULT_ML_SETTINGS['confidenceThreshold'] == 0.85
        assert DEFAULT_ML_SETTINGS['retrainingFrequencyDays'] == 30
        assert DEFAULT_ML_SETTINGS['modelVersion'] == 'latest'
        assert DEFAULT_ML_SETTINGS['anomalyDetectionEnabled'] is True
        assert DEFAULT_ML_SETTINGS['driftDetectionEnabled'] is True

    
    def test_get_ml_settings_does_not_mutate_defaults(self):
        """Test get_ml_settings returns a copy and doesn't mutate DEFAULT_ML_SETTINGS"""
        config = {}
        
        ml_settings = get_ml_settings(config)
        ml_settings['confidenceThreshold'] = 0.99
        ml_settings['newField'] = 'test'
        
        # DEFAULT_ML_SETTINGS should remain unchanged
        assert DEFAULT_ML_SETTINGS['confidenceThreshold'] == 0.85
        assert 'newField' not in DEFAULT_ML_SETTINGS
    
    def test_get_ml_settings_partial_settings(self):
        """Test get_ml_settings with partial ML settings merges with defaults"""
        config = {
            'mlSettings': {
                'confidenceThreshold': 0.95
                # Other fields missing - should be filled with defaults
            }
        }
        
        ml_settings = get_ml_settings(config)
        
        # Should merge provided values with defaults
        assert ml_settings['confidenceThreshold'] == 0.95  # From config
        assert ml_settings['retrainingFrequencyDays'] == 30  # From defaults
        assert ml_settings['modelVersion'] == 'latest'  # From defaults
        assert ml_settings['anomalyDetectionEnabled'] is True  # From defaults
        assert ml_settings['driftDetectionEnabled'] is True  # From defaults
