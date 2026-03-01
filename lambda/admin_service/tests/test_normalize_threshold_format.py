"""
Unit tests for normalize_threshold_format function
Tests backward compatibility migration from legacy to severity format
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_validation import normalize_threshold_format


class TestNormalizeThresholdFormat:
    """Test suite for threshold format normalization"""
    
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
        
        # Check critical thresholds match legacy values
        assert result['alertThresholds']['global']['pH']['critical']['min'] == 6.5
        assert result['alertThresholds']['global']['pH']['critical']['max'] == 8.5
        
        # Check warning thresholds are auto-generated correctly
        assert result['alertThresholds']['global']['pH']['warning']['min'] == 7.0
        assert result['alertThresholds']['global']['pH']['warning']['max'] == 8.0
    
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
        
        # Check critical thresholds match legacy values
        assert result['alertThresholds']['global']['temperature']['critical']['min'] == 10
        assert result['alertThresholds']['global']['temperature']['critical']['max'] == 35
        
        # Check warning thresholds are auto-generated correctly
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
        
        # Check critical threshold matches legacy value
        assert result['alertThresholds']['global']['turbidity']['critical']['max'] == 10.0
        
        # Check warning threshold is 80% of critical
        assert result['alertThresholds']['global']['turbidity']['warning']['max'] == 8.0
    
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
        
        # Check critical threshold matches legacy value
        assert result['alertThresholds']['global']['tds']['critical']['max'] == 1000
        
        # Check warning threshold is 80% of critical
        assert result['alertThresholds']['global']['tds']['warning']['max'] == 800
    
    def test_migrate_all_parameters_together(self):
        """Test migration of all parameters in a single config"""
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
    
    def test_idempotent_already_migrated_config(self):
        """Test that already migrated configs are not modified (idempotent)"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.5, 'max': 8.5},
                        'warning': {'min': 7.0, 'max': 8.0}
                    }
                }
            }
        }
        
        # Store original values
        original_critical_min = config['alertThresholds']['global']['pH']['critical']['min']
        original_warning_max = config['alertThresholds']['global']['pH']['warning']['max']
        
        result = normalize_threshold_format(config)
        
        # Verify values unchanged
        assert result['alertThresholds']['global']['pH']['critical']['min'] == original_critical_min
        assert result['alertThresholds']['global']['pH']['warning']['max'] == original_warning_max
    
    def test_idempotent_run_twice(self):
        """Test that running migration twice produces same result"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}
                }
            }
        }
        
        # First migration
        result1 = normalize_threshold_format(config)
        
        # Second migration on already migrated config
        result2 = normalize_threshold_format(result1)
        
        # Results should be identical
        assert result1['alertThresholds']['global']['pH'] == result2['alertThresholds']['global']['pH']
    
    def test_mixed_legacy_and_severity_format(self):
        """Test config with some parameters in legacy format and some in severity format"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.5, 'max': 8.5},
                        'warning': {'min': 7.0, 'max': 8.0}
                    },
                    'temperature': {
                        'min': 10,
                        'max': 35
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # pH should remain unchanged (already in severity format)
        assert result['alertThresholds']['global']['pH']['critical']['min'] == 6.5
        assert result['alertThresholds']['global']['pH']['warning']['min'] == 7.0
        
        # Temperature should be migrated
        assert result['alertThresholds']['global']['temperature']['critical']['min'] == 10
        assert result['alertThresholds']['global']['temperature']['warning']['min'] == 10.5
    
    def test_missing_alert_thresholds(self):
        """Test config without alertThresholds section"""
        config = {
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should return config unchanged
        assert result == config
    
    def test_missing_global_section(self):
        """Test config with alertThresholds but no global section"""
        config = {
            'alertThresholds': {
                'someOtherSection': {}
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should return config unchanged
        assert result == config
    
    def test_empty_thresholds(self):
        """Test config with empty thresholds"""
        config = {
            'alertThresholds': {
                'global': {}
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should return config unchanged
        assert result == config
    
    def test_partial_legacy_format_ph_only_min(self):
        """Test pH with only min (not a complete legacy format)"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5
                        # Missing 'max', so not a complete legacy format
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should not migrate (incomplete legacy format)
        assert 'critical' not in result['alertThresholds']['global']['pH']
        assert result['alertThresholds']['global']['pH']['min'] == 6.5
    
    def test_partial_legacy_format_temperature_only_max(self):
        """Test temperature with only max (not a complete legacy format)"""
        config = {
            'alertThresholds': {
                'global': {
                    'temperature': {
                        'max': 35
                        # Missing 'min', so not a complete legacy format
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Should not migrate (incomplete legacy format)
        assert 'critical' not in result['alertThresholds']['global']['temperature']
        assert result['alertThresholds']['global']['temperature']['max'] == 35
    
    def test_preserves_other_config_sections(self):
        """Test that other config sections are preserved during migration"""
        config = {
            'alertThresholds': {
                'global': {
                    'pH': {'min': 6.5, 'max': 8.5}
                }
            },
            'systemLimits': {
                'maxDevicesPerUser': 10,
                'dataRetentionDays': 365
            },
            'notificationSettings': {
                'criticalAlertChannels': ['sms', 'email']
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Verify other sections are preserved
        assert result['systemLimits']['maxDevicesPerUser'] == 10
        assert result['systemLimits']['dataRetentionDays'] == 365
        assert result['notificationSettings']['criticalAlertChannels'] == ['sms', 'email']
    
    def test_float_precision_turbidity(self):
        """Test that float precision is maintained for turbidity"""
        config = {
            'alertThresholds': {
                'global': {
                    'turbidity': {
                        'max': 12.5
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical threshold
        assert result['alertThresholds']['global']['turbidity']['critical']['max'] == 12.5
        
        # Check warning threshold (80% of 12.5 = 10.0)
        assert result['alertThresholds']['global']['turbidity']['warning']['max'] == 10.0
    
    def test_integer_values_tds(self):
        """Test that integer values work correctly for TDS"""
        config = {
            'alertThresholds': {
                'global': {
                    'tds': {
                        'max': 1500
                    }
                }
            }
        }
        
        result = normalize_threshold_format(config)
        
        # Check critical threshold
        assert result['alertThresholds']['global']['tds']['critical']['max'] == 1500
        
        # Check warning threshold (80% of 1500 = 1200)
        assert result['alertThresholds']['global']['tds']['warning']['max'] == 1200
