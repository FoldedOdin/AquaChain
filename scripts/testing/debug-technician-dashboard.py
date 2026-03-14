#!/usr/bin/env python3
"""
Debug Technician Dashboard Issue

This script simulates exactly what the frontend is doing and helps identify
why the dashboard shows "No tasks found" even though tasks exist.
"""

import boto3
import requests
import json
from datetime import datetime

def get_cognito_token_for_sidharth():
    """Get a valid Cognito token for Sidharth Lenin"""
    try:
        cognito = boto3.client('cognito-idp')
        
        # Correct Cognito details
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        client_id = '692o9a3pjudl1vudfgqpr5nuln'
        username = 'leninat259@gmail.com'
        
        print(f"🔐 Getting Cognito token for Sidharth...")
        print(f"   User Pool: {user_pool_id}")
        print(f"   Client ID: {client_id}")
        print(f"   Username: {username}")
        
        # First, let's check the user's status
        user_info = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        print(f"✅ User found in Cognito:")
        print(f"   Status: {user_info['UserStatus']}")
        print(f"   Enabled: {user_info.get('Enabled', 'N/A')}")
        
        # For testing, we'll use a different approach
        # Let's check if we can get user attributes
        attributes = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
        print(f"   Email: {attributes.get('email', 'N/A')}")
        print(f"   Sub (User ID): {attributes.get('sub', 'N/A')}")
        
        # Since we can't easily get a token without the password,
        # let's simulate what would happen with a valid token
        # by checking the Lambda function directly
        
        return attributes.get('sub')  # Return the user ID instead
        
    except Exception as e:
        print(f"❌ Error getting Cognito info: {e}")
        return None

def test_lambda_function_directly(user_id):
    """Test the Lambda function directly by invoking it"""
    try:
        lambda_client = boto3.client('lambda')
        
        # Create a test event that simulates what API Gateway would send
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/technician/tasks",
            "headers": {
                "Authorization": f"Bearer test-token-{user_id}",
                "Content-Type": "application/json"
            },
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": user_id,
                        "email": "leninat259@gmail.com",
                        "cognito:username": "leninat259@gmail.com"
                    }
                }
            },
            "queryStringParameters": None,
            "body": None
        }
        
        print(f"🧪 Testing Lambda function directly...")
        print(f"   Function: aquachain-function-technician-tasks-dev")
        print(f"   User ID: {user_id}")
        
        response = lambda_client.invoke(
            FunctionName='aquachain-function-technician-tasks-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        
        print(f"📊 Lambda Response:")
        print(f"   Status Code: {payload.get('statusCode', 'N/A')}")
        
        if 'body' in payload:
            try:
                body = json.loads(payload['body'])
                print(f"   Response Body: {json.dumps(body, indent=2)}")
                
                if 'tasks' in body:
                    print(f"✅ Tasks found: {len(body['tasks'])}")
                    for task in body['tasks']:
                        print(f"      - {task.get('taskId', 'N/A')}: {task.get('description', 'N/A')}")
                else:
                    print(f"❌ No tasks in response")
                    
            except json.JSONDecodeError:
                print(f"   Raw Body: {payload['body']}")
        
        # Check for errors in logs
        if 'errorMessage' in payload:
            print(f"❌ Lambda Error: {payload['errorMessage']}")
            if 'errorType' in payload:
                print(f"   Error Type: {payload['errorType']}")
            if 'stackTrace' in payload:
                print(f"   Stack Trace: {payload['stackTrace']}")
        
        return payload
        
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return None

def check_service_requests_table_directly():
    """Check the service requests table directly"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('aquachain-service-requests')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        print(f"🔍 Checking service requests table directly...")
        print(f"   Table: aquachain-service-requests")
        print(f"   Technician ID: {sidharth_id}")
        
        # Scan for service requests assigned to Sidharth
        response = table.scan(
            FilterExpression='technicianId = :tech_id',
            ExpressionAttributeValues={':tech_id': sidharth_id}
        )
        
        items = response.get('Items', [])
        print(f"✅ Found {len(items)} service requests for Sidharth")
        
        active_tasks = []
        for item in items:
            status = item.get('status', 'unknown')
            print(f"   📋 {item.get('requestId', 'N/A')}: {status} - {item.get('description', 'N/A')}")
            
            if status in ['assigned', 'in_progress']:
                active_tasks.append(item)
        
        print(f"🎯 Active tasks (assigned/in_progress): {len(active_tasks)}")
        
        return active_tasks
        
    except Exception as e:
        print(f"❌ Error checking service requests table: {e}")
        return []

def check_users_table_for_sidharth():
    """Check if Sidharth exists in the users table with correct role"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('AquaChain-Users')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        print(f"🔍 Checking users table for Sidharth...")
        print(f"   Table: AquaChain-Users")
        print(f"   User ID: {sidharth_id}")
        
        response = table.get_item(Key={'userId': sidharth_id})
        
        if 'Item' in response:
            user = response['Item']
            print(f"✅ Sidharth found in users table:")
            print(f"   Role: {user.get('role', 'N/A')}")
            print(f"   Verified: {user.get('verified', 'N/A')}")
            print(f"   Active: {user.get('active', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            
            return user
        else:
            print(f"❌ Sidharth NOT found in users table")
            return None
            
    except Exception as e:
        print(f"❌ Error checking users table: {e}")
        return None

def main():
    """Main debugging function"""
    print("🚀 Debugging Technician Dashboard Issue")
    print("=" * 60)
    
    # Step 1: Check if Sidharth exists in Cognito
    print("\n1. COGNITO CHECK")
    print("-" * 30)
    user_id = get_cognito_token_for_sidharth()
    
    # Step 2: Check if Sidharth exists in users table
    print("\n2. USERS TABLE CHECK")
    print("-" * 30)
    user_record = check_users_table_for_sidharth()
    
    # Step 3: Check service requests table
    print("\n3. SERVICE REQUESTS TABLE CHECK")
    print("-" * 30)
    active_tasks = check_service_requests_table_directly()
    
    # Step 4: Test Lambda function directly
    print("\n4. LAMBDA FUNCTION TEST")
    print("-" * 30)
    if user_id:
        lambda_response = test_lambda_function_directly(user_id)
    else:
        print("❌ Cannot test Lambda - no user ID available")
        lambda_response = None
    
    # Step 5: Analysis
    print("\n" + "=" * 60)
    print("📊 ANALYSIS")
    print("=" * 60)
    
    print(f"✅ Cognito User ID: {'Found' if user_id else 'Not Found'}")
    print(f"✅ Users Table Record: {'Found' if user_record else 'Not Found'}")
    print(f"✅ Active Service Requests: {len(active_tasks)}")
    print(f"✅ Lambda Function Response: {'Success' if lambda_response and lambda_response.get('statusCode') == 200 else 'Failed'}")
    
    if user_record and user_record.get('role') != 'technician':
        print(f"❌ ISSUE: User role is '{user_record.get('role')}', should be 'technician'")
    
    if len(active_tasks) > 0 and (not lambda_response or lambda_response.get('statusCode') != 200):
        print(f"❌ ISSUE: Tasks exist in database but Lambda function is not returning them")
        print(f"   This suggests an issue with the Lambda function code or authentication")
    
    if len(active_tasks) == 0:
        print(f"❌ ISSUE: No active tasks found in database")
        print(f"   Tasks might be in wrong status or assigned to wrong technician ID")
    
    print(f"\n🎯 CONCLUSION:")
    if len(active_tasks) > 0 and lambda_response and lambda_response.get('statusCode') == 200:
        print(f"✅ Everything looks correct - dashboard should show {len(active_tasks)} tasks")
        print(f"   If dashboard still shows 'No tasks', check frontend authentication")
    else:
        print(f"❌ Issues found that prevent tasks from showing in dashboard")
        print(f"   Fix the issues above and test again")

if __name__ == "__main__":
    main()