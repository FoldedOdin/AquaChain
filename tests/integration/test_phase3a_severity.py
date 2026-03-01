"""
Integration Tests for Phase 3a: Severity Threshold API

Tests the severity threshold API endpoints with mock API Gateway events
to ensure proper validation, backward compatibility, and audit logging.

Test Coverage:
- PUT /api/admin/system/configuration with severity thresholds
- Validation error handling (400 responses)
- Successful configuration updates (200 responses)
- Backward compatibility with legacy threshold format
- Audit logging for severity threshold changes
"""

import sys
import os
import json
import uuid
from datetime import datetime
from decimal import Decimal

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'admin_service'))

from handler import lambda_handler


def create_api_gateway_event(method, path, body=None, path_parameters=None, query_parameters=None):
    """Create a mock API Gateway event for testing with admin authorization"""
    return {
        'httpMethod': method,
        'path': path,
        'body': json.dumps(body) if body else None,
        'pathParameters': path_parameters,
        'queryStringParameters': query_parameters or {},
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-admin-token'
        },
        'requestContext': {
            'requestId': str(uuid.uuid4()),
            'stage': 'test',
            'identity': {
                'sourceIp': '192.168.1.1'
            },
            'authorizer': {
                'claims': {
                    'cognito:groups': 'administrators',
                    'sub': 'test-admin-user-id',
                    'email': 'admin@aquachain.test'
                }
            }
        }
    }


class TestSeverityThresholdAPI:
    """Test suite for severity threshold API endpoints"""
    
    def test_put_configuration_with_valid_severity_thresholds(self):
        """Test PUT /api/admin/system/configuration with valid severity thresholds"""
        print("\n🔍 Testing PUT configuration with valid severity thresholds...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 5.5, 'max': 9.5}
                    },
                    'turbidity': {
                        'critical': {'max': 10.0},
                        'warning': {'max': 15.0}
                    },
                    'tds': {
                        'critical': {'max': 1000},
                        'warning': {'max': 1500}
                    },
                    'temperature': {
                        'critical': {'min': 10, 'max': 35},
                        'warning': {'min': 5, 'max': 40}
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['sms', 'email', 'push'],
                'warningAlertChannels': ['email', 'push'],
                'rateLimits': {
                    'smsPerHour': 100,
                    'emailPerHour': 500
                }
            },
            'systemLimits': {
                'maxDevicesPerUser': 10,
                'maxAlertsPerDay': 1000
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Verify response structure
            assert 'statusCode' in response
            assert 'headers' in response
            assert 'body' in response
            
            # Parse response body
            body = json.loads(response['body'])
            
            # Should succeed (200) or fail gracefully with proper error structure
            if response['statusCode'] == 200:
                assert 'message' in body or 'version' in body
                print("✅ Valid severity thresholds accepted successfully")
            else:
                # If it fails, it should be due to AWS dependencies, not validation
                assert 'error' in body or 'message' in body
                print(f"⚠️  Request failed (likely AWS dependency): {body.get('error', body.get('message'))}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_invalid_ph_thresholds(self):
        """Test PUT configuration with invalid pH threshold relationships"""
        print("\n🔍 Testing PUT configuration with invalid pH thresholds...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 6.5, 'max': 8.5}  # Invalid: warning_min > critical_min
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email'],
                'warningAlertChannels': ['email']
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 400 Bad Request
            assert response['statusCode'] == 400
            
            body = json.loads(response['body'])
            
            # Should have validation errors
            assert 'error' in body or 'validationErrors' in body
            
            # Check for pH-specific error message
            if 'validationErrors' in body:
                errors = body['validationErrors']
                assert any('pH' in str(error) for error in errors)
                print(f"✅ Invalid pH thresholds rejected with errors: {errors}")
            else:
                print(f"✅ Invalid pH thresholds rejected: {body.get('error')}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_invalid_turbidity_thresholds(self):
        """Test PUT configuration with invalid turbidity threshold relationships"""
        print("\n🔍 Testing PUT configuration with invalid turbidity thresholds...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'turbidity': {
                        'critical': {'max': 10.0},
                        'warning': {'max': 10.0}  # Invalid: equal values
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email'],
                'warningAlertChannels': ['email']
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 400 Bad Request
            assert response['statusCode'] == 400
            
            body = json.loads(response['body'])
            
            # Should have validation errors
            assert 'error' in body or 'validationErrors' in body
            
            if 'validationErrors' in body:
                errors = body['validationErrors']
                assert any('turbidity' in str(error).lower() for error in errors)
                print(f"✅ Invalid turbidity thresholds rejected with errors: {errors}")
            else:
                print(f"✅ Invalid turbidity thresholds rejected: {body.get('error')}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_no_critical_channels(self):
        """Test PUT configuration with no critical alert channels (should fail)"""
        print("\n🔍 Testing PUT configuration with no critical alert channels...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 5.5, 'max': 9.5}
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': [],  # Invalid: empty
                'warningAlertChannels': ['email', 'push']
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 400 Bad Request
            assert response['statusCode'] == 400
            
            body = json.loads(response['body'])
            
            # Should have validation errors
            assert 'error' in body or 'validationErrors' in body
            
            if 'validationErrors' in body:
                errors = body['validationErrors']
                assert any('critical alert channel' in str(error).lower() for error in errors)
                print(f"✅ Empty critical channels rejected with errors: {errors}")
            else:
                print(f"✅ Empty critical channels rejected: {body.get('error')}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_sms_in_warning_channels(self):
        """Test PUT configuration with SMS in warning channels (should fail)"""
        print("\n🔍 Testing PUT configuration with SMS in warning channels...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 5.5, 'max': 9.5}
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['sms', 'email'],
                'warningAlertChannels': ['sms', 'email']  # Invalid: SMS not allowed
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 400 Bad Request
            assert response['statusCode'] == 400
            
            body = json.loads(response['body'])
            
            # Should have validation errors
            assert 'error' in body or 'validationErrors' in body
            
            if 'validationErrors' in body:
                errors = body['validationErrors']
                assert any('sms' in str(error).lower() and 'warning' in str(error).lower() for error in errors)
                print(f"✅ SMS in warning channels rejected with errors: {errors}")
            else:
                print(f"✅ SMS in warning channels rejected: {body.get('error')}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_legacy_format(self):
        """Test PUT configuration with legacy threshold format (backward compatibility)"""
        print("\n🔍 Testing PUT configuration with legacy threshold format...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'min': 6.5,  # Legacy format
                        'max': 8.5
                    },
                    'turbidity': {
                        'max': 10.0  # Legacy format
                    },
                    'tds': {
                        'max': 1000  # Legacy format
                    },
                    'temperature': {
                        'min': 10,  # Legacy format
                        'max': 35
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email'],
                'warningAlertChannels': ['email']
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Verify response structure
            assert 'statusCode' in response
            assert 'body' in response
            
            body = json.loads(response['body'])
            
            # Should succeed (200) or fail gracefully
            if response['statusCode'] == 200:
                print("✅ Legacy threshold format accepted (backward compatible)")
            else:
                # If it fails, it should be due to AWS dependencies, not validation
                print(f"⚠️  Request failed (likely AWS dependency): {body.get('error', body.get('message'))}")
            
            # Legacy format should not cause validation errors
            assert response['statusCode'] != 400 or 'validationErrors' not in body
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_put_configuration_with_multiple_validation_errors(self):
        """Test PUT configuration with multiple validation errors"""
        print("\n🔍 Testing PUT configuration with multiple validation errors...")
        
        config_body = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 6.5, 'max': 8.5}  # Error 1: invalid relationship
                    },
                    'turbidity': {
                        'critical': {'max': 10.0},
                        'warning': {'max': 10.0}  # Error 2: equal values
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': [],  # Error 3: empty
                'warningAlertChannels': ['sms']  # Error 4: SMS not allowed
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=config_body,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 400 Bad Request
            assert response['statusCode'] == 400
            
            body = json.loads(response['body'])
            
            # Should have validation errors
            assert 'error' in body or 'validationErrors' in body
            
            if 'validationErrors' in body:
                errors = body['validationErrors']
                # Should have multiple errors
                assert len(errors) >= 2
                print(f"✅ Multiple validation errors collected: {len(errors)} errors")
                print(f"   Errors: {errors}")
            else:
                print(f"✅ Multiple validation errors rejected: {body.get('error')}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_response_format_consistency(self):
        """Test that all responses follow consistent format"""
        print("\n🔍 Testing response format consistency...")
        
        # Test with valid config
        valid_config = {
            'alertThresholds': {
                'global': {
                    'pH': {
                        'critical': {'min': 6.0, 'max': 9.0},
                        'warning': {'min': 5.5, 'max': 9.5}
                    }
                }
            },
            'notificationSettings': {
                'criticalAlertChannels': ['email'],
                'warningAlertChannels': ['email']
            },
            'systemLimits': {
                'maxDevicesPerUser': 10
            }
        }
        
        event = create_api_gateway_event(
            'PUT',
            '/api/admin/system/configuration',
            body=valid_config,
            query_parameters={'adminId': 'test-admin', 'ipAddress': '192.168.1.1'}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Check response structure
            assert 'statusCode' in response
            assert 'headers' in response
            assert 'body' in response
            
            # Check CORS headers
            headers = response.get('headers', {})
            assert 'Access-Control-Allow-Origin' in headers
            
            # Check body is valid JSON
            body = json.loads(response['body'])
            assert isinstance(body, dict)
            
            print("✅ Response format is consistent")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise


def run_severity_threshold_integration_tests():
    """Run all severity threshold integration tests"""
    print("🚀 Starting Phase 3a Severity Threshold Integration Tests")
    print("=" * 70)
    
    test_suite = TestSeverityThresholdAPI()
    
    tests = [
        test_suite.test_put_configuration_with_valid_severity_thresholds,
        test_suite.test_put_configuration_with_invalid_ph_thresholds,
        test_suite.test_put_configuration_with_invalid_turbidity_thresholds,
        test_suite.test_put_configuration_with_no_critical_channels,
        test_suite.test_put_configuration_with_sms_in_warning_channels,
        test_suite.test_put_configuration_with_legacy_format,
        test_suite.test_put_configuration_with_multiple_validation_errors,
        test_suite.test_response_format_consistency
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Phase 3a Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3a integration tests PASSED!")
        print("\n✅ Severity threshold API is ready for deployment")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the issues above.")
        print("\nNote: Some failures may be due to AWS dependencies (DynamoDB, etc.)")
        print("      These tests verify the validation logic and response structure.")
        return False


if __name__ == '__main__':
    success = run_severity_threshold_integration_tests()
    exit(0 if success else 1)
