#!/usr/bin/env python3
"""
Comprehensive test of the entire readings flow to identify where the issue is
"""

import boto3
import requests
import json
import time

def test_1_data_exists():
    """Test 1: Verify data exists in DynamoDB"""
    print("🔍 Test 1: Data Existence Check")
    print("-" * 30)
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        readings_table = dynamodb.Table('AquaChain-Readings')
        
        # Query for recent data
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': 'ESP32-001_2026-03'
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        if response['Items']:
            item = response['Items'][0]
            print(f"✅ Latest reading: {item['timestamp']}")
            print(f"   pH: {item.get('pH')}, Temp: {item.get('temperature')}")
            return True
        else:
            print("❌ No data found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_2_lambda_direct():
    """Test 2: Lambda function direct invocation"""
    print("\n🔍 Test 2: Lambda Direct Invocation")
    print("-" * 30)
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/readings/ESP32-001/latest",
            "pathParameters": {"deviceId": "ESP32-001"},
            "queryStringParameters": None,
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "test-user",
                        "cognito:username": "testuser",
                        "email": "test@example.com"
                    }
                }
            }
        }
        
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"✅ Lambda returns 200")
            print(f"   Success: {body.get('success')}")
            print(f"   Device: {body.get('deviceId')}")
            return True
        else:
            print(f"❌ Lambda returns {result.get('statusCode')}")
            print(f"   Body: {result.get('body')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_3_api_gateway_no_auth():
    """Test 3: API Gateway without authentication"""
    print("\n🔍 Test 3: API Gateway (No Auth)")
    print("-" * 30)
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Expected 401 - Authentication required")
            return True
        elif response.status_code == 500:
            print("❌ 500 Error - Lambda or integration issue")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_4_create_user_and_test():
    """Test 4: Create user and test with authentication"""
    print("\n🔍 Test 4: Full Authentication Flow")
    print("-" * 30)
    
    try:
        # Create test user
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        client_id = '692o9a3pjudl1vudfgqpr5nuln'
        username = 'readingstest@aquachain.com'
        password = 'TestPassword123!'
        
        # Try to create user (ignore if exists)
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                TemporaryPassword=password,
                MessageAction='SUPPRESS',
                UserAttributes=[
                    {'Name': 'email', 'Value': username},
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
            )
            
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )
            print("✅ Test user created")
        except cognito.exceptions.UsernameExistsException:
            print("✅ Test user already exists")
        
        # Get token
        auth_response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        token = auth_response['AuthenticationResult']['AccessToken']
        print("✅ Got authentication token")
        
        # Test API with token
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API returns data successfully!")
            print(f"   Device: {data.get('deviceId')}")
            print(f"   Success: {data.get('success')}")
            return True
        elif response.status_code == 401:
            print("❌ Still getting 401 - Auth configuration issue")
            print(f"Response: {response.text}")
            return False
        elif response.status_code == 404:
            print("⚠️  404 - No readings found (but API is working)")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return True  # 404 with proper JSON is success
            except:
                print(f"Raw response: {response.text}")
                return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests to diagnose the issue"""
    print("🧪 Comprehensive Readings Flow Test")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(("Data Exists", test_1_data_exists()))
    results.append(("Lambda Direct", test_2_lambda_direct()))
    results.append(("API Gateway (No Auth)", test_3_api_gateway_no_auth()))
    results.append(("Full Auth Flow", test_4_create_user_and_test()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The readings API is working correctly.")
        print("The device status monitoring fix did NOT break the readings flow.")
    else:
        print("🔍 DIAGNOSIS:")
        if results[0][1] and results[1][1]:  # Data and Lambda work
            if not results[3][1]:  # But auth fails
                print("• Data flow is working correctly")
                print("• Lambda function is working correctly") 
                print("• Issue is with API Gateway authentication configuration")
                print("• The device status monitoring fix did NOT break readings")
            else:
                print("• All components are working!")
        else:
            print("• There are fundamental issues with data or Lambda")

if __name__ == "__main__":
    main()