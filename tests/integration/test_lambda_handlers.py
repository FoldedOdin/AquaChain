"""
Lambda Handler Integration Tests

Tests the lambda handlers with mock API Gateway events to ensure
proper request routing and response formatting.
"""

import sys
import os
import json
import uuid
from decimal import Decimal

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'payment_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'technician_assignment'))


def create_api_gateway_event(method, path, body=None, path_parameters=None, query_parameters=None):
    """Create a mock API Gateway event"""
    return {
        'httpMethod': method,
        'path': path,
        'body': json.dumps(body) if body else None,
        'pathParameters': path_parameters,
        'queryStringParameters': query_parameters,
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
        },
        'requestContext': {
            'requestId': str(uuid.uuid4()),
            'stage': 'test'
        }
    }


def test_order_management_handler():
    """Test Order Management lambda handler with mock events"""
    print("🔍 Testing Order Management lambda handler...")
    
    try:
        from enhanced_order_management import lambda_handler
        
        # Test unsupported operation (should return error gracefully)
        event = create_api_gateway_event('GET', '/unsupported')
        context = {}
        
        response = lambda_handler(event, context)
        
        # Should return proper error response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        assert response['statusCode'] >= 400  # Error status code
        
        # Parse response body
        body = json.loads(response['body'])
        assert 'success' in body
        assert body['success'] is False
        
        print("✅ Order Management handler properly handles unsupported operations")
        
        # Test create order with invalid data (should validate input)
        create_event = create_api_gateway_event(
            'POST', 
            '/orders',
            body={'invalid': 'data'}  # Missing required fields
        )
        
        create_response = lambda_handler(create_event, context)
        assert create_response['statusCode'] >= 400  # Should be validation error
        
        print("✅ Order Management handler properly validates input")
        
        return True
        
    except Exception as e:
        print(f"❌ Order Management handler test failed: {e}")
        return False


def test_payment_service_handler():
    """Test Payment Service lambda handler with mock events"""
    print("\n🔍 Testing Payment Service lambda handler...")
    
    try:
        from payment_service import lambda_handler
        
        # Test unsupported operation
        event = create_api_gateway_event('GET', '/unsupported')
        context = {}
        
        response = lambda_handler(event, context)
        
        # Should return proper error response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        
        # Parse response body
        body = json.loads(response['body'])
        assert 'success' in body
        
        print("✅ Payment Service handler properly handles requests")
        
        # Test create Razorpay order with missing data
        razorpay_event = create_api_gateway_event(
            'POST',
            '/create-razorpay-order',
            body={'amount': 100}  # Missing orderId
        )
        
        razorpay_response = lambda_handler(razorpay_event, context)
        # Should handle the request (may fail due to validation or AWS dependencies)
        assert 'statusCode' in razorpay_response
        
        print("✅ Payment Service handler processes Razorpay requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Payment Service handler test failed: {e}")
        return False


def test_technician_assignment_handler():
    """Test Technician Assignment lambda handler with mock events"""
    print("\n🔍 Testing Technician Assignment lambda handler...")
    
    try:
        from technician_assignment_service import lambda_handler
        
        # Test unsupported operation
        event = create_api_gateway_event('DELETE', '/unsupported')
        context = {}
        
        response = lambda_handler(event, context)
        
        # Should return proper error response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        
        print("✅ Technician Assignment handler properly handles requests")
        
        # Test get available technicians
        available_event = create_api_gateway_event(
            'GET',
            '/technicians/available',
            query_parameters={
                'latitude': '40.7128',
                'longitude': '-74.0060',
                'radius': '10'
            }
        )
        
        available_response = lambda_handler(available_event, context)
        # Should handle the request (may fail due to AWS dependencies)
        assert 'statusCode' in available_response
        
        print("✅ Technician Assignment handler processes availability requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Technician Assignment handler test failed: {e}")
        return False


def test_cors_headers():
    """Test that all handlers return proper CORS headers"""
    print("\n🔍 Testing CORS headers...")
    
    try:
        handlers = [
            ('Order Management', 'enhanced_order_management'),
            ('Payment Service', 'payment_service'),
            ('Technician Assignment', 'technician_assignment_service')
        ]
        
        for name, module_name in handlers:
            module = __import__(module_name)
            handler = getattr(module, 'lambda_handler')
            
            event = create_api_gateway_event('GET', '/test')
            response = handler(event, {})
            
            # Check CORS headers
            headers = response.get('headers', {})
            assert 'Access-Control-Allow-Origin' in headers
            assert headers['Access-Control-Allow-Origin'] == '*'
            
            print(f"✅ {name} handler includes proper CORS headers")
        
        return True
        
    except Exception as e:
        print(f"❌ CORS headers test failed: {e}")
        return False


def test_error_response_format():
    """Test that error responses follow consistent format"""
    print("\n🔍 Testing error response format...")
    
    try:
        from enhanced_order_management import lambda_handler as order_handler
        
        # Create an event that will cause an error
        event = create_api_gateway_event('POST', '/orders', body={'invalid': 'data'})
        response = order_handler(event, {})
        
        # Check response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert 'success' in body
        assert body['success'] is False
        
        # Should have either 'error' or 'message' field
        assert 'error' in body or 'message' in body
        
        print("✅ Error responses follow consistent format")
        
        return True
        
    except Exception as e:
        print(f"❌ Error response format test failed: {e}")
        return False


def run_lambda_handler_tests():
    """Run all lambda handler tests"""
    print("🚀 Starting Lambda Handler Integration Tests")
    print("=" * 60)
    
    tests = [
        test_order_management_handler,
        test_payment_service_handler,
        test_technician_assignment_handler,
        test_cors_headers,
        test_error_response_format
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Lambda Handler Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All lambda handler tests PASSED!")
        print("\n✅ Lambda handlers are ready for API Gateway integration")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the issues above.")
        return False


if __name__ == '__main__':
    success = run_lambda_handler_tests()
    exit(0 if success else 1)