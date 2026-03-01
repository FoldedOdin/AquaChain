"""
Unit Tests for Severity Validation Logic (Phase 3a)

Tests cover:
- validate_severity_thresholds() function
- validate_notification_channels() function
- normalize_threshold_format() function
- Edge cases and backward compatibility
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_validation import (
    validate_severity_thresholds,
    validate_notification_channels,
    normalize_threshold_format
)


class TestValidateSeverityThresholds:
    """Test suite for validate_severity_thresholds function"""
    
    def test_valid_ph_thresholds(self):
        """Test valid pH severity thresholds"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},  # More strict (narrower range)
                'warning': {'min': 5.5, 'max': 9.5}    # Less strict (wider range)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_all_parameters(self):
        """Test valid severity thresholds for all parameters"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},  # More strict (narrower range)
                'warning': {'min': 5.5, 'max': 9.5}    # Less strict (wider range)
            },
            'turbidity': {
                'critical': {'max': 10.0},
                'warning': {'max': 15.0}  # Warning is less strict (higher)
            },
            'tds': {
                'critical': {'max': 1000},
                'warning': {'max': 1500}  # Warning is less strict (higher)
            },
            'temperature': {
                'critical': {'min': 10, 'max': 35},  # More strict (narrower range)
                'warning': {'min': 5, 'max': 40}     # Less strict (wider range)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_ph_warning_min_greater_than_critical_min(self):
        """Test pH validation fails when warning_min >= critical_min"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},
                'warning': {'min': 6.5, 'max': 8.5}  # warning_min > critical_min (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'pH thresholds must satisfy' in errors[0]
        assert '6.5' in errors[0]  # warning_min
        assert '6.0' in errors[0]  # critical_min
    
    def test_invalid_ph_equal_values(self):
        """Test pH validation fails when values are equal"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},
                'warning': {'min': 6.0, 'max': 9.0}  # Equal values (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'pH thresholds must satisfy' in errors[0]
    
    def test_invalid_ph_reversed_order(self):
        """Test pH validation fails when thresholds are in reversed order"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},
                'warning': {'min': 5.0, 'max': 10.0}  # Correct order
            }
        }
        
        # This should be valid (warning is less strict)
        is_valid, errors = validate_severity_thresholds(thresholds)
        assert is_valid is True
        
        # Now test invalid reversed order
        thresholds_invalid = {
            'pH': {
                'critical': {'min': 5.0, 'max': 10.0},
                'warning': {'min': 6.0, 'max': 9.0}  # Reversed (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds_invalid)
        
        assert is_valid is False
        assert len(errors) == 1
    
    def test_invalid_ph_out_of_range(self):
        """Test pH validation fails when values are out of valid range (0-14)"""
        thresholds = {
            'pH': {
                'critical': {'min': -1.0, 'max': 15.0},  # Out of range
                'warning': {'min': 0.0, 'max': 14.0}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must be between 0 and 14' in error for error in errors)
    
    def test_invalid_ph_missing_values(self):
        """Test pH validation fails when required values are missing"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0},  # Missing max
                'warning': {'min': 6.5, 'max': 8.5}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must include all min/max values' in error for error in errors)
    
    def test_valid_turbidity_thresholds(self):
        """Test valid turbidity severity thresholds"""
        thresholds = {
            'turbidity': {
                'critical': {'max': 10.0},
                'warning': {'max': 15.0}  # Warning is less strict (higher value)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_turbidity_critical_greater_than_warning(self):
        """Test turbidity validation fails when critical_max >= warning_max"""
        thresholds = {
            'turbidity': {
                'critical': {'max': 10.0},
                'warning': {'max': 15.0}  # Valid: warning > critical
            }
        }
        
        # This should be valid
        is_valid, errors = validate_severity_thresholds(thresholds)
        assert is_valid is True
        
        # Now test invalid case (critical >= warning)
        thresholds_invalid = {
            'turbidity': {
                'critical': {'max': 10.0},
                'warning': {'max': 10.0}  # Equal (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds_invalid)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'Turbidity critical max' in errors[0]
        assert 'must be less than' in errors[0]
    
    def test_invalid_turbidity_out_of_range(self):
        """Test turbidity validation fails when values are out of range (0-100)"""
        thresholds = {
            'turbidity': {
                'critical': {'max': 150.0},  # Out of range
                'warning': {'max': 200.0}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must be between 0 and 100' in error for error in errors)
    
    def test_invalid_turbidity_missing_values(self):
        """Test turbidity validation fails when max value is missing"""
        thresholds = {
            'turbidity': {
                'critical': {},  # Missing max
                'warning': {'max': 5.0}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must include max values' in error for error in errors)
    
    def test_valid_tds_thresholds(self):
        """Test valid TDS severity thresholds"""
        thresholds = {
            'tds': {
                'critical': {'max': 1000},
                'warning': {'max': 1500}  # Warning is less strict (higher value)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_tds_critical_greater_than_warning(self):
        """Test TDS validation fails when critical_max >= warning_max"""
        thresholds = {
            'tds': {
                'critical': {'max': 1000},
                'warning': {'max': 1000}  # Equal (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'TDS critical max' in errors[0]
        assert 'must be less than' in errors[0]
    
    def test_invalid_tds_out_of_range(self):
        """Test TDS validation fails when values are out of range (0-5000)"""
        thresholds = {
            'tds': {
                'critical': {'max': 6000},  # Out of range
                'warning': {'max': 7000}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must be between 0 and 5000' in error for error in errors)
    
    def test_valid_temperature_thresholds(self):
        """Test valid temperature severity thresholds"""
        thresholds = {
            'temperature': {
                'critical': {'min': 10, 'max': 35},  # More strict (narrower range)
                'warning': {'min': 5, 'max': 40}     # Less strict (wider range)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_temperature_relationships(self):
        """Test temperature validation fails when relationships are violated"""
        thresholds = {
            'temperature': {
                'critical': {'min': 10, 'max': 35},
                'warning': {'min': 5, 'max': 40}  # Correct order
            }
        }
        
        # This should be valid
        is_valid, errors = validate_severity_thresholds(thresholds)
        assert is_valid is True
        
        # Now test invalid case
        thresholds_invalid = {
            'temperature': {
                'critical': {'min': 5, 'max': 40},
                'warning': {'min': 10, 'max': 35}  # Reversed (invalid)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds_invalid)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'Temperature thresholds must satisfy' in errors[0]
    
    def test_invalid_temperature_out_of_range(self):
        """Test temperature validation fails when values are out of range (-10 to 100)"""
        thresholds = {
            'temperature': {
                'critical': {'min': -20, 'max': 110},  # Out of range
                'warning': {'min': -15, 'max': 105}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert any('must be between -10 and 100' in error for error in errors)
    
    def test_empty_thresholds(self):
        """Test validation passes with empty thresholds (backward compatibility)"""
        thresholds = {}
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_partial_parameters(self):
        """Test validation works with only some parameters defined"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},  # More strict
                'warning': {'min': 5.5, 'max': 9.5}    # Less strict
            }
            # Other parameters not defined
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are collected"""
        thresholds = {
            'pH': {
                'critical': {'min': 6.0, 'max': 9.0},
                'warning': {'min': 6.5, 'max': 8.5}  # Invalid relationship
            },
            'turbidity': {
                'critical': {'max': 10.0},
                'warning': {'max': 10.0}  # Invalid (equal)
            },
            'tds': {
                'critical': {'max': 1000},
                'warning': {'max': 1500}  # Valid
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is False
        assert len(errors) == 2  # pH and turbidity errors
        assert any('pH' in error for error in errors)
        assert any('Turbidity' in error for error in errors)


class TestValidateNotificationChannels:
    """Test suite for validate_notification_channels function"""
    
    def test_valid_notification_channels(self):
        """Test valid notification channel configuration"""
        notification_settings = {
            'criticalAlertChannels': ['sms', 'email', 'push'],
            'warningAlertChannels': ['email', 'push']
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_minimal_critical_channels(self):
        """Test valid configuration with minimal critical channels"""
        notification_settings = {
            'criticalAlertChannels': ['email'],  # At least one
            'warningAlertChannels': ['push']
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_no_critical_channels(self):
        """Test validation fails when no critical channels are enabled"""
        notification_settings = {
            'criticalAlertChannels': [],  # Empty
            'warningAlertChannels': ['email', 'push']
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'At least one critical alert channel must be enabled' in errors[0]
    
    def test_invalid_missing_critical_channels(self):
        """Test validation fails when criticalAlertChannels key is missing"""
        notification_settings = {
            'warningAlertChannels': ['email', 'push']
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'At least one critical alert channel must be enabled' in errors[0]
    
    def test_invalid_sms_in_warning_channels(self):
        """Test validation fails when SMS is in warning channels"""
        notification_settings = {
            'criticalAlertChannels': ['sms', 'email'],
            'warningAlertChannels': ['sms', 'email']  # SMS not allowed
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert 'SMS notifications are not allowed for warning alerts' in errors[0]
    
    def test_invalid_channel_name_critical(self):
        """Test validation fails with invalid critical channel name"""
        notification_settings = {
            'criticalAlertChannels': ['sms', 'email', 'telegram'],  # Invalid channel
            'warningAlertChannels': ['email']
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert any('Invalid critical alert channel: telegram' in error for error in errors)
    
    def test_invalid_channel_name_warning(self):
        """Test validation fails with invalid warning channel name"""
        notification_settings = {
            'criticalAlertChannels': ['email'],
            'warningAlertChannels': ['email', 'slack']  # Invalid channel
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert any('Invalid warning alert channel: slack' in error for error in errors)
    
    def test_valid_empty_warning_channels(self):
        """Test validation passes with empty warning channels (backward compatibility)"""
        notification_settings = {
            'criticalAlertChannels': ['email'],
            'warningAlertChannels': []  # Empty is OK
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are collected"""
        notification_settings = {
            'criticalAlertChannels': [],  # Error 1: empty
            'warningAlertChannels': ['sms', 'email']  # Error 2: SMS not allowed
        }
        
        is_valid, errors = validate_notification_channels(notification_settings)
        
        assert is_valid is False
        assert len(errors) == 2
        assert any('At least one critical alert channel' in error for error in errors)
        assert any('SMS notifications are not allowed' in error for error in errors)


class TestNormalizeThresholdFormat:
    """Test suite for normalize_threshold_format function"""
    
    def test_migrate_legacy_ph_format(self):
        """Test migration of legacy pH format to severity format"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5,
                        'max': 8.5
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical thresholds (from legacy)
        assert 'critical' in result['alertThresholds']['global']['pH']
        assert result['alertThresholds']['global']['pH']['critical']['min'] == 6.5
        assert result['alertThresholds']['global']['pH']['critical']['max'] == 8.5
        
        # Check warning thresholds (auto-generated)
        assert 'warning' in result['alertThresholds']['global']['pH']
        assert result['alertThresholds']['global']['pH']['warning']['min'] == 7.0  # 6.5 + 0.5
        assert result['alertThresholds']['global']['pH']['warning']['max'] == 8.0  # 8.5 - 0.5
        
        # Check legacy fields are removed
        assert 'min' not in result['alertThresholds']['global']['pH']
        assert 'max' not in result['alertThresholds']['global']['pH']
    
    def test_migrate_legacy_temperature_format(self):
        """Test migration of legacy temperature format to severity format"""
        config = {
            'alertThresholds': {
                'global': {
                    'temperature': {
                        'min': 10,
                        'max': 35
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical thresholds
        assert result['alertThresholds']['global']['temperature']['critical']['min'] == 10
        assert result['alertThresholds']['global']['temperature']['critical']['max'] == 35
        
        # Check warning thresholds
        assert result['alertThresholds']['global']['temperature']['warning']['min'] == 10.5
        assert result['alertThresholds']['global']['temperature']['warning']['max'] == 34.5
    
    def test_migrate_legacy_turbidity_format(self):
        """Test migration of legacy turbidity format to severity format"""
        config = {
            'alertThresholds': {
                'global': {
                    'turbidity': {
                        'max': 10.0
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical threshold
        assert result['alertThresholds']['global']['turbidity']['critical']['max'] == 10.0
        
        # Check warning threshold (80% of critical)
        assert result['alertThresholds']['global']['turbidity']['warning']['max'] == 8.0
        
        # Check legacy field is removed
        assert 'max' not in result['alertThresholds']['global']['turbidity']
    
    def test_migrate_legacy_tds_format(self):
        """Test migration of legacy TDS format to severity format"""
        config = {
            'alertThresholds': {
                'global': {
                    'tds': {
                        'max': 1000
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical threshold
        assert result['alertThresholds']['global']['tds']['critical']['max'] == 1000
        
        # Check warning threshold (80% of critical)
        assert result['alertThresholds']['global']['tds']['warning']['max'] == 800
    
    def test_migrate_all_legacy_parameters(self):
        """Test migration of all parameters at once"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5},
                    'temperature': {'min': 10, 'max': 35},
                    'turbidity': {'max': 10.0},
                    'tds': {'max': 1000}
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Verify all parameters were migrated
        assert 'critical' in result['alertThresholds']['global']['pH']
        assert 'warning' in result['alertThresholds']['global']['pH']
        assert 'critical' in result['alertThresholds']['global']['temperature']
        assert 'warning' in result['alertThresholds']['global']['temperature']
        assert 'critical' in result['alertThresholds']['global']['turbidity']
        assert 'warning' in result['alertThresholds']['global']['turbidity']
        assert 'critical' in result['alertThresholds']['global']['tds']
        assert 'warning' in result['alertThresholds']['global']['tds']
    
    def test_idempotent_migration(self):
        """Test that migration is idempotent (running twice produces same result)"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5,
                        'max': 8.5
                    }
                }
            }
        }
        
        # First migration
        result1 = normalize_threshold_format(config)
        
        # Second migration (should not change anything)
        result2 = normalize_threshold_format(result1)
        
        # Results should be identical
        assert result1 == result2
        assert result2['alertThresholds']['global']['pH']['critical']['min'] == 6.5
        assert result2['alertThresholds']['global']['pH']['warning']['min'] == 7.0
    
    def test_no_migration_for_severity_format(self):
        """Test that configs with severity format are not modified"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 5.5, 'max': 9.5},
                        'warning': {'min': 6.0, 'max': 9.0}
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should be unchanged
        assert result == config
        assert result['alertThresholds']['global']['pH']['critical']['min'] == 5.5
        assert result['alertThresholds']['global']['pH']['warning']['min'] == 6.0
    
    def test_mixed_legacy_and_severity_formats(self):
        """Test migration with mixed legacy and severity formats"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5,
                        'max': 8.5
                    },
                    'turbidity': {
                        'critical': {'max': 10.0},
                        'warning': {'max': 5.0}
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # pH should be migrated
        assert 'critical' in result['alertThresholds']['global']['pH']
        assert 'warning' in result['alertThresholds']['global']['pH']
        
        # Turbidity should remain unchanged
        assert result['alertThresholds']['global']['turbidity']['critical']['max'] == 10.0
        assert result['alertThresholds']['global']['turbidity']['warning']['max'] == 5.0
    
    def test_no_migration_without_alert_thresholds(self):
        """Test that configs without alertThresholds are not modified"""
        config = {
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should be unchanged
        assert result == config
    
    def test_no_migration_without_global_section(self):
        """Test that configs without global section are not modified"""
        config = {
            'alertThresholds': {
                'someOtherSection': {}
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should be unchanged
        assert result == config
    
    def test_partial_legacy_format_not_migrated(self):
        """Test that partial legacy formats (only min or only max) are not migrated"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5
                        # Missing max - should not be migrated
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should be unchanged (not migrated)
        assert result == config
        assert 'critical' not in result['alertThresholds']['global']['pH']
    
    def test_preserve_other_config_sections(self):
        """Test that other configuration sections are preserved during migration"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}
                }
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email']
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check migration happened
        assert 'critical' in result['alertThresholds']['global']['pH']
        
        # Check other sections preserved
        assert result['systemLimits']['maxDevicesPerUser'] == 10
        assert result['notificationSettings']['criticalAlertChannels'] == ['email']


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    
    def test_boundary_ph_values(self):
        """Test pH validation with boundary values (0 and 14)"""
        thresholds = {
            'pH': {
                'critical': {'min': 0.5, 'max': 13.5},  # More strict
                'warning': {'min': 0.0, 'max': 14.0}    # Less strict (at boundaries)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_boundary_temperature_values(self):
        """Test temperature validation with boundary values (-10 and 100)"""
        thresholds = {
            'temperature': {
                'critical': {'min': -5, 'max': 95},  # More strict
                'warning': {'min': -10, 'max': 100}  # Less strict (at boundaries)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_float_precision_in_migration(self):
        """Test that float precision is maintained during migration"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.75, 'max': 8.25}
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check precision is maintained
        assert result['alertThresholds']['global']['pH']['critical']['min'] == 6.75
        assert result['alertThresholds']['global']['pH']['critical']['max'] == 8.25
        assert result['alertThresholds']['global']['pH']['warning']['min'] == 7.25
        assert result['alertThresholds']['global']['pH']['warning']['max'] == 7.75
    
    def test_zero_values(self):
        """Test handling of zero values in thresholds"""
        thresholds = {
            'turbidity': {
                'critical': {'max': 0.0},
                'warning': {'max': 0.0}
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        # Should fail because critical >= warning
        assert is_valid is False
    
    def test_very_large_tds_values(self):
        """Test TDS validation with maximum allowed values"""
        thresholds = {
            'tds': {
                'critical': {'max': 4000},
                'warning': {'max': 5000}  # Warning is less strict (higher)
            }
        }
        
        is_valid, errors = validate_severity_thresholds(thresholds)
        
        assert is_valid is True
        assert len(errors) == 0
