#!/usr/bin/env python3
"""
Debug Cognito token to see if it's valid and properly formatted
"""

import boto3
import json
import base64
import requests

def get_test_token():
    """Get a test token and analyze it"""
    
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    user_pool_id = 'ap-south-1_QUDl7hG8u'
    client_id = '692o9a3pjudl1vudfgqpr5nuln'
    username = 'readingstest@aquachain.com'
    password = 'TestPassword123!'
    
    try:
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
        
        access_token = auth_response['AuthenticationResult']['AccessToken']
        id_token = auth_response['AuthenticationResult']['IdToken']
        
        print("🔍 Token Analysis")
        print("=" * 40)
        print(f"Access Token Length: {len(access_token)}")
        print(f"ID Token Length: {len(id_token)}")
        
        # Decode JWT header and payload (without verification)
        def decode_jwt_payload(token):
            try:
                # Split token into parts
                parts = token.split('.')
                if len(parts) != 3:
                    return None
                
                # Decode payload (add padding if needed)
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)  # Add padding
                decoded = base64.urlsafe_b64decode(payload)
                return json.loads(decoded)
            except Exception as e:
                print(f"Error decoding JWT: {e}")
                return None
        
        # Analyze access token
        access_payload = decode_jwt_payload(access_token)
        if access_payload:
            print("\n📄 Access Token Payload:")
            print(f"  Token Use: {access_payload.get('token_use')}")
            print(f"  Client ID: {access_payload.get('client_id')}")
            print(f"  Username: {access_payload.get('username')}")
            print(f"  Scope: {access_payload.get('scope')}")
            print(f"  Expires: {access_payload.get('exp')}")
            print(f"  Issued: {access_payload.get('iat')}")
        
        # Analyze ID token
        id_payload = decode_jwt_payload(id_token)
        if id_payload:
            print("\n📄 ID Token Payload:")
            print(f"  Token Use: {id_payload.get('token_use')}")
            print(f"  Audience: {id_payload.get('aud')}")
            print(f"  Subject: {id_payload.get('sub')}")
            print(f"  Email: {id_payload.get('email')}")
            print(f"  Cognito Username: {id_payload.get('cognito:username')}")
        
        return access_token, id_token
        
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None, None

def test_token_with_different_headers(access_token, id_token):
    """Test API with different token formats"""
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    test_cases = [
        ("Access Token", f"Bearer {access_token}"),
        ("ID Token", f"Bearer {id_token}"),
        ("Access Token (no Bearer)", access_token),
        ("ID Token (no Bearer)", id_token),
    ]
    
    print("\n🧪 Testing Different Token Formats")
    print("=" * 50)
    
    for test_name, auth_header in test_cases:
        print(f"\n🔍 Testing: {test_name}")
        
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  Response: {data.get('success', 'No success field')}")
                except:
                    print("  Response: Valid but not JSON")
                return True
            elif response.status_code == 401:
                print("  ❌ 401 Unauthorized")
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data.get('message', 'No message')}")
                except:
                    print(f"  Raw response: {response.text}")
            else:
                print(f"  ⚠️  Status: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    return False

def test_cognito_user_pool_directly():
    """Test if the user pool and client are configured correctly"""
    
    print("\n🔍 Cognito Configuration Check")
    print("=" * 40)
    
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    
    try:
        # Check user pool
        user_pool = cognito.describe_user_pool(UserPoolId='ap-south-1_QUDl7hG8u')
        print(f"✅ User Pool: {user_pool['UserPool']['Name']}")
        print(f"   ID: {user_pool['UserPool']['Id']}")
        
        # Check client
        client = cognito.describe_user_pool_client(
            UserPoolId='ap-south-1_QUDl7hG8u',
            ClientId='692o9a3pjudl1vudfgqpr5nuln'
        )
        print(f"✅ Client: {client['UserPoolClient']['ClientName']}")
        print(f"   Auth Flows: {client['UserPoolClient'].get('ExplicitAuthFlows', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognito config error: {e}")
        return False

def main():
    """Main debugging function"""
    
    print("🔧 Cognito Token Debug")
    print("=" * 60)
    
    # Test Cognito configuration
    cognito_ok = test_cognito_user_pool_directly()
    
    if not cognito_ok:
        print("❌ Cognito configuration issues found")
        return
    
    # Get and analyze tokens
    access_token, id_token = get_test_token()
    
    if not access_token:
        print("❌ Could not get tokens")
        return
    
    # Test different token formats
    success = test_token_with_different_headers(access_token, id_token)
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS")
    print("=" * 60)
    
    if success:
        print("🎉 Found working token format!")
    else:
        print("🔍 All token formats failed - deeper issue exists")
        print("\nPossible causes:")
        print("• API Gateway authorizer misconfiguration")
        print("• Cognito user pool/client mismatch")
        print("• Token validation issues")
        print("• Resource-level authorization problems")

if __name__ == "__main__":
    main()