#!/usr/bin/env python3
"""
Test the complete technician login flow to identify where it breaks
"""

import boto3
import json
import requests
from datetime import datetime

def test_cognito_user_exists():
    """Test if technician users exist in Cognito"""
    print("🔍 Checking Cognito users...")
    
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Get user pool ID from environment or use known value
        user_pool_id = 'ap-south-1_Ej8Ej8Ej8'  # This might need to be updated
        
        # Try to find the user pool first
        user_pools = cognito.list_user_pools(MaxResults=10)
        aquachain_pool = None
        
        for pool in user_pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                aquachain_pool = pool
                user_pool_id = pool['Id']
                break
        
        if not aquachain_pool:
            print("❌ No AquaChain user pool found")
            return False
        
        print(f"✅ Found user pool: {aquachain_pool['Name']} (ID: {user_pool_id})")
        
        # List users to find technicians
        users = cognito.list_users(UserPoolId=user_pool_id)
        
        technician_users = []
        for user in users['Users']:
            # Check user attributes for role
            attributes = {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
            
            if attributes.get('custom:role') == 'technician':
                technician_users.append({
                    'username': user['Username'],
                    'email': attributes.get('email', 'N/A'),
                    'status': user['UserStatus'],
                    'enabled': user['Enabled']
                })
        
        print(f"✅ Found {len(technician_users)} technician users:")
        for user in technician_users:
            print(f"   👤 {user['email']} - Status: {user['status']}, Enabled: {user['enabled']}")
        
        return len(technician_users) > 0
        
    except Exception as e:
        print(f"❌ Error checking Cognito users: {e}")
        return False

def test_api_with_mock_token():
    """Test API with a mock token to see if routing works"""
    print("\n🧪 Testing API with mock authentication...")
    
    try:
        # Create a mock JWT token structure (this won't work but will show routing)
        api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks"
        
        headers = {
            'Authorization': 'Bearer mock-token',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        print(f"✅ API Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📋 Response Body (raw): {response.text}")
        
        # 401 is expected, but it shows the endpoint is reachable
        return response.status_code in [401, 403]  # Auth errors are expected
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def check_dynamodb_technician_data():
    """Check if technician data exists in DynamoDB"""
    print("\n🔍 Checking DynamoDB technician data...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Check Users table
        users_table = dynamodb.Table('AquaChain-Users')
        
        # Scan for technician users
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response['Items']
        print(f"✅ Found {len(technicians)} technicians in DynamoDB:")
        
        for tech in technicians:
            print(f"   👤 {tech.get('name', 'N/A')} ({tech.get('email', 'N/A')})")
            print(f"      User ID: {tech.get('userId', 'N/A')}")
            print(f"      Active: {tech.get('active', 'N/A')}")
            print(f"      Verified: {tech.get('verified', 'N/A')}")
        
        return len(technicians) > 0
        
    except Exception as e:
        print(f"❌ Error checking DynamoDB: {e}")
        return False

def check_service_requests_for_technicians():
    """Check if there are service requests assigned to technicians"""
    print("\n🔍 Checking service requests...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Check service requests table
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        # Scan for assigned requests
        response = service_requests_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'assigned'}
        )
        
        requests = response['Items']
        print(f"✅ Found {len(requests)} assigned service requests:")
        
        technician_counts = {}
        for req in requests:
            tech_id = req.get('technicianId', 'Unknown')
            technician_counts[tech_id] = technician_counts.get(tech_id, 0) + 1
        
        for tech_id, count in technician_counts.items():
            print(f"   👤 Technician {tech_id}: {count} tasks")
        
        return len(requests) > 0
        
    except Exception as e:
        print(f"❌ Error checking service requests: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Technician Login Flow")
    print("=" * 60)
    
    results = {
        'cognito_users_exist': test_cognito_user_exists(),
        'api_routing_works': test_api_with_mock_token(),
        'dynamodb_data_exists': check_dynamodb_technician_data(),
        'service_requests_exist': check_service_requests_for_technicians()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print("\n🎯 DIAGNOSIS:")
    
    if not results['cognito_users_exist']:
        print("❌ ISSUE: Technician users don't exist in Cognito")
        print("   FIX: Create technician users in Cognito with proper role")
    
    if not results['api_routing_works']:
        print("❌ ISSUE: API Gateway routing is broken")
        print("   FIX: Check API Gateway configuration")
    
    if not results['dynamodb_data_exists']:
        print("❌ ISSUE: No technician data in DynamoDB")
        print("   FIX: Create technician profiles in Users table")
    
    if not results['service_requests_exist']:
        print("❌ ISSUE: No service requests assigned to technicians")
        print("   FIX: Create test service requests")
    
    if all(results.values()):
        print("✅ ALL SYSTEMS WORKING - Issue is likely in frontend token handling")
        print("   🔍 Check browser localStorage for authToken")
        print("   🔍 Check if token contains correct user ID and role")
        print("   🔍 Verify token is not expired")
    
    print("\n📋 NEXT STEPS:")
    print("1. Log in as technician in browser")
    print("2. Open dev tools and check localStorage['authToken']")
    print("3. Decode JWT token to verify claims")
    print("4. Check Network tab for API call failures")

if __name__ == "__main__":
    main()