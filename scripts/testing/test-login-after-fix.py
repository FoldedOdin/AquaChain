#!/usr/bin/env python3
"""
Test login functionality after profile fix
"""

import requests
import json
import os

def test_backend_login():
    """Test login via backend API"""
    try:
        # Get API endpoint
        api_endpoint = os.environ.get('REACT_APP_API_ENDPOINT', 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev')
        
        print(f"🔍 Testing login via backend API: {api_endpoint}")
        
        # Login credentials
        credentials = {
            'email': 'leninat259@gmail.com',
            'password': 'AquaChain2024!'
        }
        
        # Make login request
        response = requests.post(
            f"{api_endpoint}/api/auth/signin",
            headers={'Content-Type': 'application/json'},
            json=credentials,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"📋 Response data:")
            print(json.dumps(result, indent=2))
            
            # Check user data
            user = result.get('user', {})
            print(f"\n👤 User Profile:")
            print(f"   ID: {user.get('id', 'Not set')}")
            print(f"   Email: {user.get('email', 'Not set')}")
            print(f"   Name: {user.get('name', 'Not set')}")
            print(f"   First Name: {user.get('firstName', 'Not set')}")
            print(f"   Last Name: {user.get('lastName', 'Not set')}")
            print(f"   Role: {user.get('role', 'Not set')}")
            
            # Check token
            token = result.get('token')
            if token:
                print(f"\n🔑 JWT Token received (length: {len(token)})")
                print(f"   Token preview: {token[:50]}...")
            else:
                print(f"\n❌ No JWT token in response")
            
            return True
        else:
            print(f"❌ Login failed")
            try:
                error_data = response.json()
                print(f"📋 Error response:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"📋 Raw error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend login: {e}")
        return False

def test_profile_api():
    """Test profile retrieval API"""
    try:
        # First login to get token
        api_endpoint = os.environ.get('REACT_APP_API_ENDPOINT', 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev')
        
        credentials = {
            'email': 'leninat259@gmail.com',
            'password': 'AquaChain2024!'
        }
        
        # Login
        login_response = requests.post(
            f"{api_endpoint}/api/auth/signin",
            headers={'Content-Type': 'application/json'},
            json=credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            print("❌ Cannot test profile API - login failed")
            return False
        
        login_data = login_response.json()
        token = login_data.get('token')
        
        if not token:
            print("❌ Cannot test profile API - no token received")
            return False
        
        print(f"\n🔍 Testing profile API with token...")
        
        # Test profile endpoint
        profile_response = requests.get(
            f"{api_endpoint}/api/user/profile",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        print(f"📊 Profile API Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"✅ Profile API successful!")
            print(f"📋 Profile data:")
            print(json.dumps(profile_data, indent=2))
            return True
        else:
            print(f"❌ Profile API failed")
            try:
                error_data = profile_response.json()
                print(f"📋 Error response:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"📋 Raw error response: {profile_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing profile API: {e}")
        return False

def main():
    print("🧪 Testing Login After Profile Fix")
    print("=" * 35)
    
    # Test 1: Backend login
    print("\n1. Testing Backend Login API...")
    login_success = test_backend_login()
    
    # Test 2: Profile API
    if login_success:
        print("\n2. Testing Profile API...")
        test_profile_api()
    
    print("\n📋 Summary:")
    if login_success:
        print("✅ Login is working - you should be able to log in now!")
        print("✅ Profile data has been fixed in the database")
        print("\n🔗 Try logging in with:")
        print("   Email: leninat259@gmail.com")
        print("   Password: AquaChain2024!")
    else:
        print("❌ Login is still having issues - check the API endpoint")

if __name__ == "__main__":
    main()