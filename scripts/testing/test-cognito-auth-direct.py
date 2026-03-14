#!/usr/bin/env python3
"""
Test Cognito authentication directly using the same method as the Lambda function
"""

import boto3
import json
from botocore.exceptions import ClientError

def test_cognito_auth():
    """Test Cognito authentication using the same method as Lambda"""
    print("🔐 Testing Cognito Authentication (Lambda Method)")
    print("=" * 60)
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Same parameters as Lambda function
        client_id = '692o9a3pjudl1vudfgqpr5nuln'
        email = 'leninat259@gmail.com'
        password = 'AquaChain123!'
        
        print(f"📋 Testing with:")
        print(f"   Client ID: {client_id}")
        print(f"   Email: {email}")
        print(f"   Password: {'*' * len(password)}")
        
        # Use the exact same method as the Lambda function
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        print(f"\n✅ Authentication successful!")
        
        # Extract tokens
        auth_result = response['AuthenticationResult']
        access_token = auth_result['AccessToken']
        id_token = auth_result['IdToken']
        refresh_token = auth_result['RefreshToken']
        
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   ID Token: {id_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...")
        
        # Decode ID token (same as Lambda)
        import jwt
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        
        user_id = decoded_token.get('sub')
        user_role = decoded_token.get('cognito:groups', ['consumers'])[0]
        
        print(f"\n📋 Decoded Token Info:")
        print(f"   User ID: {user_id}")
        print(f"   Email: {decoded_token.get('email')}")
        print(f"   Name: {decoded_token.get('name')}")
        print(f"   Groups: {decoded_token.get('cognito:groups', [])}")
        print(f"   Role: {user_role}")
        print(f"   Email Verified: {decoded_token.get('email_verified')}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"\n❌ Cognito Authentication Failed:")
        print(f"   Error Code: {error_code}")
        print(f"   Error Message: {error_message}")
        
        if error_code == 'NotAuthorizedException':
            print(f"   🚨 This is the same error the Lambda is getting!")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

def test_other_technician():
    """Test with the other technician account"""
    print(f"\n🔐 Testing Other Technician Account")
    print("=" * 60)
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
        
        client_id = '692o9a3pjudl1vudfgqpr5nuln'
        email = 'karthiikkpradeep897@gmail.com'
        password = 'AquaChain123!'
        
        print(f"📋 Testing with:")
        print(f"   Email: {email}")
        
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        print(f"✅ Authentication successful for {email}!")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Authentication failed for {email}: {error_code}")
        return False

def main():
    """Main function"""
    print("🚀 Testing Cognito Authentication Direct")
    print("=" * 60)
    
    # Test primary technician
    result1 = test_cognito_auth()
    
    # Test other technician
    result2 = test_other_technician()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    if result1:
        print("✅ Sidharth Lenin (leninat259@gmail.com): SUCCESS")
    else:
        print("❌ Sidharth Lenin (leninat259@gmail.com): FAILED")
    
    if result2:
        print("✅ Karthik K Pradeep (karthiikkpradeep897@gmail.com): SUCCESS")
    else:
        print("❌ Karthik K Pradeep (karthiikkpradeep897@gmail.com): FAILED")
    
    if result1 and result2:
        print("\n🎉 BOTH TECHNICIANS CAN AUTHENTICATE!")
        print("   The issue is NOT with Cognito authentication")
        print("   The problem must be elsewhere in the Lambda function")
    else:
        print("\n🔧 AUTHENTICATION ISSUES FOUND")
        print("   Need to fix Cognito user setup")

if __name__ == "__main__":
    main()