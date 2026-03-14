#!/usr/bin/env python3
"""
Test the technician tasks Lambda function directly to see what it returns
"""

import boto3
import json

def test_technician_tasks_lambda():
    """Test the technician tasks Lambda function directly"""
    print("🧪 Testing technician tasks Lambda function directly...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Create a test event that simulates the API Gateway request
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/technician/tasks",
            "headers": {
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            },
            "queryStringParameters": None,
            "body": None,
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "11e3edea-2081-7042-7a5c-d360cc94780a",  # Karthik's user ID
                        "email": "karthiikkpradeep897@gmail.com",
                        "custom:role": "technician"
                    }
                }
            }
        }
        
        print(f"📋 Invoking Lambda with test event...")
        print(f"   User ID: {test_event['requestContext']['authorizer']['claims']['sub']}")
        print(f"   Email: {test_event['requestContext']['authorizer']['claims']['email']}")
        
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName='aquachain-function-technician-tasks-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        
        print(f"✅ Lambda function response:")
        print(f"   Status Code: {payload.get('statusCode', 'N/A')}")
        
        if 'body' in payload:
            try:
                body = json.loads(payload['body']) if isinstance(payload['body'], str) else payload['body']
                print(f"   Response Body:")
                print(json.dumps(body, indent=2))
                
                # Check if it has the expected structure
                if 'tasks' in body:
                    tasks = body['tasks']
                    print(f"   ✅ Found {len(tasks)} tasks in response")
                    
                    if tasks:
                        print(f"   📋 First task structure:")
                        first_task = tasks[0]
                        for key, value in first_task.items():
                            print(f"      {key}: {value}")
                else:
                    print(f"   ⚠️  No 'tasks' field in response")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Could not parse response body as JSON: {e}")
                print(f"   Raw body: {payload['body']}")
        else:
            print(f"   ❌ No body in response")
            
        return payload
        
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    print("🚀 Testing Technician Tasks Lambda Function")
    print("=" * 60)
    
    result = test_technician_tasks_lambda()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if result:
        status_code = result.get('statusCode', 0)
        if status_code == 200:
            print("✅ Lambda function is working correctly")
            print("✅ Returns 200 status code")
            
            try:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                if 'tasks' in body and isinstance(body['tasks'], list):
                    print("✅ Returns tasks array as expected")
                    print(f"✅ Found {len(body['tasks'])} tasks")
                else:
                    print("❌ Response structure doesn't match frontend expectations")
                    print("   Expected: { tasks: [...] }")
                    print(f"   Got: {list(body.keys()) if isinstance(body, dict) else type(body)}")
            except:
                print("❌ Response body is not valid JSON")
        else:
            print(f"❌ Lambda function returned error status: {status_code}")
    else:
        print("❌ Lambda function test failed")
    
    print("\n🎯 NEXT STEPS:")
    print("1. If Lambda works, check frontend API call")
    print("2. If Lambda fails, check Lambda function code")
    print("3. Verify authentication token handling")

if __name__ == "__main__":
    main()