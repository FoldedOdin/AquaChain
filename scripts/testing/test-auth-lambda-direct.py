#!/usr/bin/env python3

import boto3
import json
import sys

def test_auth_lambda_direct():
    """Test the auth Lambda function directly to debug the signin issue."""
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event that mimics API Gateway request
    test_event = {
        "httpMethod": "POST",
        "path": "/api/auth/signin",
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "body": json.dumps({
            "email": "test@aquachain.com",
            "password": "TestPassword123!"
        }),
        "requestContext": {
            "requestId": "test-request-123",
            "identity": {
                "sourceIp": "127.0.0.1"
            }
        }
    }
    
    print("🧪 Testing auth Lambda function directly...")
    print(f"📧 Email: test@aquachain.com")
    
    try:
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName='aquachain-function-auth-service-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        
        print(f"✅ Lambda Response Status: {response['StatusCode']}")
        print(f"📄 Response Payload:")
        print(json.dumps(payload, indent=2))
        
        if 'errorMessage' in payload:
            print(f"❌ Error: {payload['errorMessage']}")
            if 'errorType' in payload:
                print(f"🔍 Error Type: {payload['errorType']}")
            if 'stackTrace' in payload:
                print(f"📚 Stack Trace:")
                for line in payload['stackTrace']:
                    print(f"  {line}")
        
        return payload
        
    except Exception as e:
        print(f"❌ Failed to invoke Lambda: {str(e)}")
        return None

def test_cognito_direct():
    """Test Cognito authentication directly."""
    
    print("\n🔐 Testing Cognito authentication directly...")
    
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    
    try:
        response = cognito_client.initiate_auth(
            ClientId='692o9a3pjudl1vudfgqpr5nuln',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'test@aquachain.com',
                'PASSWORD': 'TestPassword123!'
            }
        )
        
        print("✅ Cognito authentication successful!")
        print(f"📄 Response keys: {list(response.keys())}")
        
        if 'AuthenticationResult' in response:
            auth_result = response['AuthenticationResult']
            print(f"🔑 Token types: {list(auth_result.keys())}")
            
            # Decode ID token to see user info
            import jwt
            id_token = auth_result['IdToken']
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            print(f"👤 User info: {json.dumps(decoded, indent=2, default=str)}")
        
        return response
        
    except Exception as e:
        print(f"❌ Cognito authentication failed: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 Starting auth debugging...")
    
    # Test Cognito directly first
    cognito_result = test_cognito_direct()
    
    # Test Lambda function
    lambda_result = test_auth_lambda_direct()
    
    if cognito_result and not lambda_result:
        print("\n🔍 Cognito works but Lambda fails - likely a Lambda code issue")
    elif not cognito_result and not lambda_result:
        print("\n🔍 Both Cognito and Lambda fail - likely a credentials issue")
    elif cognito_result and lambda_result:
        print("\n✅ Both Cognito and Lambda work - issue might be in API Gateway")
    else:
        print("\n🤔 Unexpected result combination")