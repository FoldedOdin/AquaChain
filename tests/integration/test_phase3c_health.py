"""
Integration Tests for Phase 3c: System Health API

Tests the system health monitoring API endpoint with mock API Gateway events
to ensure proper health checks, caching behavior, and authentication.

Test Coverage:
- GET /api/admin/system/health returns 200
- Response includes all 5 services (IoT Core, Lambda, DynamoDB, SNS, ML Inference)
- Response includes overallStatus field
- Refresh parameter forces cache bypass
- Caching behavior (30-second cache)
- Authentication required (admin JWT token)
- Error handling and graceful degradation
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'admin_service'))

from handler import lambda_handler


def create_api_gateway_event(method, path, body=None, path_parameters=None, query_parameters=None, include_auth=True):
    """Create a mock API Gateway event for testing"""
    event = {
        'httpMethod': method,
        'path': path,
        'body': json.dumps(body) if body else None,
        'pathParameters': path_parameters,
        'queryStringParameters': query_parameters or {},
        'headers': {
            'Content-Type': 'application/json'
        },
        'requestContext': {
            'requestId': str(uuid.uuid4()),
            'stage': 'test',
            'identity': {
                'sourceIp': '192.168.1.1'
            }
        }
    }
    
    # Add admin authorization if requested
    if include_auth:
        event['headers']['Authorization'] = 'Bearer test-admin-token'
        event['requestContext']['authorizer'] = {
            'claims': {
                'cognito:groups': 'administrators',
                'sub': 'test-admin-user-id',
                'email': 'admin@aquachain.test'
            }
        }
    
    return event


class TestSystemHealthAPI:
    """Test suite for system health API endpoint"""
    
    def test_get_system_health_returns_200(self):
        """Test GET /api/admin/system/health returns 200 OK"""
        print("\n🔍 Testing GET /api/admin/system/health returns 200...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Verify response structure
            assert 'statusCode' in response, "Response missing statusCode"
            assert 'headers' in response, "Response missing headers"
            assert 'body' in response, "Response missing body"
            
            # Should return 200 OK
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            # Parse response body
            body = json.loads(response['body'])
            
            # Should have health data structure
            assert isinstance(body, dict), "Response body should be a dict"
            
            print(f"✅ GET /api/admin/system/health returned 200 OK")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_response_includes_all_five_services(self):
        """Test response includes all 5 monitored services"""
        print("\n🔍 Testing response includes all 5 services...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            
            # Should have services array
            assert 'services' in body, "Response missing 'services' field"
            assert isinstance(body['services'], list), "'services' should be a list"
            
            # Should have exactly 5 services
            services = body['services']
            assert len(services) == 5, f"Expected 5 services, got {len(services)}"
            
            # Check for required service names
            service_names = [s['name'] for s in services]
            expected_services = ['IoT Core', 'Lambda', 'DynamoDB', 'SNS', 'ML Inference']
            
            for expected in expected_services:
                assert expected in service_names, f"Missing service: {expected}"
            
            print(f"✅ Response includes all 5 services: {service_names}")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_response_includes_overall_status(self):
        """Test response includes overallStatus field"""
        print("\n🔍 Testing response includes overallStatus...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            
            # Should have overallStatus field
            assert 'overallStatus' in body, "Response missing 'overallStatus' field"
            
            # Should be one of the valid statuses
            overall_status = body['overallStatus']
            valid_statuses = ['healthy', 'degraded', 'down']
            assert overall_status in valid_statuses, f"Invalid overallStatus: {overall_status}"
            
            print(f"✅ Response includes overallStatus: {overall_status}")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_service_health_structure(self):
        """Test each service has required health fields"""
        print("\n🔍 Testing service health structure...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            services = body['services']
            
            # Check each service has required fields
            for service in services:
                assert 'name' in service, f"Service missing 'name' field: {service}"
                assert 'status' in service, f"Service missing 'status' field: {service}"
                assert 'lastCheck' in service, f"Service missing 'lastCheck' field: {service}"
                
                # Status should be valid
                status = service['status']
                valid_statuses = ['healthy', 'degraded', 'down', 'unknown']
                assert status in valid_statuses, f"Invalid status '{status}' for {service['name']}"
                
                # lastCheck should be ISO8601 timestamp
                last_check = service['lastCheck']
                assert 'T' in last_check and 'Z' in last_check, f"Invalid timestamp format: {last_check}"
            
            print(f"✅ All services have required health fields")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_refresh_parameter_forces_cache_bypass(self):
        """Test refresh=true parameter forces cache bypass"""
        print("\n🔍 Testing refresh parameter forces cache bypass...")
        
        # First request (should populate cache)
        event1 = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response1 = lambda_handler(event1, {})
            assert response1['statusCode'] == 200
            
            body1 = json.loads(response1['body'])
            
            # Should be a cache miss (first request)
            assert 'cacheHit' in body1, "Response missing 'cacheHit' field"
            # First request might be cache miss or hit depending on previous tests
            
            # Second request with refresh=true (should bypass cache)
            event2 = create_api_gateway_event(
                'GET',
                '/api/admin/system/health',
                query_parameters={'refresh': 'true'}
            )
            
            response2 = lambda_handler(event2, {})
            assert response2['statusCode'] == 200
            
            body2 = json.loads(response2['body'])
            
            # Should be a cache miss (forced refresh)
            assert body2['cacheHit'] == False, "refresh=true should bypass cache"
            
            print(f"✅ refresh=true parameter bypasses cache (cacheHit={body2['cacheHit']})")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_caching_behavior(self):
        """Test caching behavior (30-second cache)"""
        print("\n🔍 Testing caching behavior...")
        
        # First request (should populate cache)
        event1 = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={'refresh': 'true'}  # Force fresh data
        )
        
        try:
            response1 = lambda_handler(event1, {})
            assert response1['statusCode'] == 200
            
            body1 = json.loads(response1['body'])
            assert body1['cacheHit'] == False, "First request with refresh=true should be cache miss"
            
            # Second request immediately after (should hit cache)
            event2 = create_api_gateway_event(
                'GET',
                '/api/admin/system/health',
                query_parameters={}
            )
            
            response2 = lambda_handler(event2, {})
            assert response2['statusCode'] == 200
            
            body2 = json.loads(response2['body'])
            
            # Should be a cache hit (within 30 seconds)
            assert body2['cacheHit'] == True, "Second request should hit cache"
            
            # Timestamps should be the same (from cache)
            assert body1['checkedAt'] == body2['checkedAt'], "Cached response should have same timestamp"
            
            print(f"✅ Caching works correctly (cache hit on second request)")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_authentication_required(self):
        """Test authentication is required (should fail without admin token)"""
        print("\n🔍 Testing authentication required...")
        
        # Request without authentication
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={},
            include_auth=False  # No admin token
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 403 Forbidden (admin access required)
            assert response['statusCode'] == 403, f"Expected 403, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            
            # Should have error message
            assert 'error' in body, "Response should include error message"
            
            print(f"✅ Authentication required (403 without admin token)")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_response_includes_checked_at_timestamp(self):
        """Test response includes checkedAt timestamp"""
        print("\n🔍 Testing response includes checkedAt timestamp...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            body = json.loads(response['body'])
            
            # Should have checkedAt field
            assert 'checkedAt' in body, "Response missing 'checkedAt' field"
            
            # Should be ISO8601 timestamp
            checked_at = body['checkedAt']
            assert 'T' in checked_at and 'Z' in checked_at, f"Invalid timestamp format: {checked_at}"
            
            # Should be recent (within last minute)
            from datetime import datetime, timedelta
            checked_time = datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
            now = datetime.now(checked_time.tzinfo)
            age = (now - checked_time).total_seconds()
            
            assert age < 60, f"checkedAt timestamp too old: {age} seconds"
            
            print(f"✅ Response includes checkedAt timestamp: {checked_at}")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_cors_headers_present(self):
        """Test CORS headers are present in response"""
        print("\n🔍 Testing CORS headers present...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            
            # Check CORS headers
            headers = response.get('headers', {})
            assert 'Access-Control-Allow-Origin' in headers, "Missing CORS header: Access-Control-Allow-Origin"
            
            print(f"✅ CORS headers present in response")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_error_handling_graceful_degradation(self):
        """Test error handling and graceful degradation"""
        print("\n🔍 Testing error handling and graceful degradation...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Should return 200 even if some checks fail
            # (graceful degradation - services marked as 'unknown')
            assert response['statusCode'] in [200, 500], f"Unexpected status code: {response['statusCode']}"
            
            body = json.loads(response['body'])
            
            if response['statusCode'] == 200:
                # Should have services array even if some checks failed
                assert 'services' in body, "Response missing 'services' field"
                
                # Services with failed checks should be marked as 'unknown'
                services = body['services']
                for service in services:
                    if service['status'] == 'unknown':
                        # Should have a message explaining the failure
                        assert 'message' in service or 'metrics' in service, \
                            f"Unknown service should have message or metrics: {service['name']}"
                
                print(f"✅ Error handling works with graceful degradation")
            else:
                # If 500, should have error structure
                assert 'error' in body or 'message' in body, "Error response should have error/message"
                print(f"✅ Error handling returns proper error structure")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise
    
    def test_response_format_consistency(self):
        """Test that all responses follow consistent format"""
        print("\n🔍 Testing response format consistency...")
        
        event = create_api_gateway_event(
            'GET',
            '/api/admin/system/health',
            query_parameters={}
        )
        
        try:
            response = lambda_handler(event, {})
            
            # Check response structure
            assert 'statusCode' in response, "Response missing statusCode"
            assert 'headers' in response, "Response missing headers"
            assert 'body' in response, "Response missing body"
            
            # Check body is valid JSON
            body = json.loads(response['body'])
            assert isinstance(body, dict), "Response body should be a dict"
            
            # Check required fields based on status code
            if response['statusCode'] == 200:
                assert 'services' in body, "Success response missing 'services'"
                assert 'overallStatus' in body, "Success response missing 'overallStatus'"
                assert 'checkedAt' in body, "Success response missing 'checkedAt'"
                assert 'cacheHit' in body, "Success response missing 'cacheHit'"
            else:
                assert 'error' in body or 'message' in body, "Error response should have error/message"
            
            print("✅ Response format is consistent")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            raise


def run_system_health_integration_tests():
    """Run all system health integration tests"""
    print("🚀 Starting Phase 3c System Health API Integration Tests")
    print("=" * 70)
    
    test_suite = TestSystemHealthAPI()
    
    tests = [
        test_suite.test_get_system_health_returns_200,
        test_suite.test_response_includes_all_five_services,
        test_suite.test_response_includes_overall_status,
        test_suite.test_service_health_structure,
        test_suite.test_refresh_parameter_forces_cache_bypass,
        test_suite.test_caching_behavior,
        test_suite.test_authentication_required,
        test_suite.test_response_includes_checked_at_timestamp,
        test_suite.test_cors_headers_present,
        test_suite.test_error_handling_graceful_degradation,
        test_suite.test_response_format_consistency
    ]
    
    passed = 0
    failed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ Test {test.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Phase 3c Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3c system health integration tests PASSED!")
        print("\n✅ System health API is ready for deployment")
        return True
    else:
        print(f"⚠️  {failed} tests failed. Please review the issues above.")
        print("\nNote: Some failures may be due to AWS dependencies (CloudWatch, etc.)")
        print("      These tests verify the API structure and response format.")
        return False


if __name__ == '__main__':
    success = run_system_health_integration_tests()
    exit(0 if success else 1)

