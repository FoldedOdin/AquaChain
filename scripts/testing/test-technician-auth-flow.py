#!/usr/bin/env python3
"""
Test the complete technician authentication flow
"""

import boto3
import json
import requests
from datetime import datetime

def test_cognito_authentication():
    """Test Cognito authentication for technician"""
    print("🔐 Testing Cognito authentication...")
    
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # User pool details
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        client_id = '6ej8ej8ej8ej8ej8ej8ej8'  # This needs to be the actual client ID
        
        # Get the actual client ID
        user_pools = cognito.list_user_pools(MaxResults=10)
        for pool in user_pools['UserPools']:
            if pool['Id'] == user_pool_id:
                # Get user pool clients
                clients = cognito.list_user_pool_clients(UserPoolId=user_pool_id)
                if clients['UserPoolClients']:
                    client_id = clients['UserPoolClients'][0]['ClientId']
                    print(f"✅ Found client ID: {client_id}")
                break
        
        # Test authentication
        email = 'leninat259@gmail.com'
        password = 'AquaChain123!'
        
        print(f"🔍 Attempting to authenticate {email}...")
        
        try:
            response = cognito.admin_initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            if 'AuthenticationResult' in response:
                access_token = response['AuthenticationResult']['AccessToken']
                id_token = response['AuthenticationResult']['IdToken']
                
                print(f"✅ Authentication successful!")
                print(f"   Access Token: {access_token[:50]}...")
                print(f"   ID Token: {id_token[:50]}...")
                
                return {
                    'access_token': access_token,
                    'id_token': id_token,
                    'email': email
                }
            else:
                print(f"❌ Authentication failed: {response}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        return None

def test_api_with_real_token(auth_result):
    """Test API with real authentication token"""
    print("\n🧪 Testing API with real token...")
    
    if not auth_result:
        print("❌ No authentication result to test with")
        return False
    
    try:
        api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks"
        
        headers = {
            'Authorization': f'Bearer {auth_result["id_token"]}',
            'Content-Type': 'application/json'
        }
        
        print(f"📋 Calling: {api_url}")
        print(f"   User: {auth_result['email']}")
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📋 Response Data:")
                print(json.dumps(data, indent=2))
                
                if 'tasks' in data:
                    tasks = data['tasks']
                    print(f"\n🎉 SUCCESS! Found {len(tasks)} tasks for technician")
                    return True
                else:
                    print(f"⚠️  No tasks field in response")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Testing Complete Technician Authentication Flow")
    print("=" * 60)
    
    # Test authentication
    auth_result = test_cognito_authentication()
    
    # Test API with real token
    api_success = test_api_with_real_token(auth_result)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if auth_result:
        print("✅ Cognito Authentication: PASS")
    else:
        print("❌ Cognito Authentication: FAIL")
    
    if api_success:
        print("✅ API Call with Token: PASS")
        print("\n🎉 TECHNICIAN DASHBOARD SHOULD NOW WORK!")
        print("✅ Users can log in as technicians")
        print("✅ API returns tasks for authenticated technicians")
        print("✅ Frontend should display tasks correctly")
    else:
        print("❌ API Call with Token: FAIL")
        print("\n🔧 STILL NEEDS DEBUGGING:")
        print("   - Check Lambda function logs")
        print("   - Verify token parsing in Lambda")
        print("   - Check DynamoDB queries")
    
    print("\n🎯 FINAL STEPS:")
    print("1. Open frontend in browser")
    print("2. Log in as: leninat259@gmail.com / AquaChain123!")
    print("3. Navigate to technician dashboard")
    print("4. Verify tasks are displayed")

if __name__ == "__main__":
    main()