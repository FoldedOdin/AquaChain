#!/usr/bin/env python3
"""
Get a fresh JWT token for testing.
"""

import boto3
import json
from botocore.exceptions import ClientError

def get_fresh_token():
    """Get a fresh JWT token using Cognito"""
    print("🔐 Getting fresh JWT token...")
    
    # Cognito configuration
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    
    # Your Cognito User Pool details
    user_pool_id = 'ap-south-1_QUDl7hG8u'
    client_id = '692o9a3pjudl1vudfgqpr5nuln'
    
    # Test user credentials (you'll need to use your actual credentials)
    username = 'karthikkpradeep123@gmail.com'  # Your email
    
    print(f"User Pool ID: {user_pool_id}")
    print(f"Client ID: {client_id}")
    print(f"Username: {username}")
    
    try:
        # First, let's check if the user exists
        print("\n📋 Checking user status...")
        
        user_details = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        print(f"✅ User found: {user_details['Username']}")
        print(f"   Status: {user_details['UserStatus']}")
        print(f"   Enabled: {user_details['Enabled']}")
        
        # Check user attributes
        for attr in user_details['UserAttributes']:
            if attr['Name'] in ['email', 'email_verified', 'given_name', 'family_name']:
                print(f"   {attr['Name']}: {attr['Value']}")
        
        print(f"\n💡 To get a new JWT token, you have these options:")
        print(f"")
        print(f"1. **Browser Refresh** (Recommended):")
        print(f"   - Refresh your browser page")
        print(f"   - Login with: {username}")
        print(f"   - Use your password")
        print(f"")
        print(f"2. **Direct Cognito Login** (For testing):")
        print(f"   - Use AWS Cognito SDK")
        print(f"   - Call InitiateAuth with username/password")
        print(f"")
        print(f"3. **Frontend Login Flow** (Normal usage):")
        print(f"   - Go to your login page")
        print(f"   - Enter credentials")
        print(f"   - Frontend handles token refresh")
        
        # Show how to test with curl once you have a token
        print(f"\n🧪 Once you have a new token, test with:")
        print(f"curl -H 'Authorization: Bearer <NEW_JWT_TOKEN>' \\")
        print(f"     https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            print(f"❌ User not found: {username}")
            print(f"   You may need to register first or use a different email")
        else:
            print(f"❌ Error checking user: {e}")
        return False

def show_frontend_auth_flow():
    """Show how the frontend should handle authentication"""
    print(f"\n📱 Frontend Authentication Flow:")
    print(f"")
    print(f"Your frontend should automatically handle token refresh.")
    print(f"Check these files:")
    print(f"")
    print(f"1. frontend/src/services/authService.ts")
    print(f"   - Should detect expired tokens")
    print(f"   - Should redirect to login")
    print(f"")
    print(f"2. frontend/src/services/dataService.ts") 
    print(f"   - Should include Authorization header")
    print(f"   - Should handle 401 responses")
    print(f"")
    print(f"3. Browser Local Storage:")
    print(f"   - Check for 'accessToken' or similar")
    print(f"   - Clear if expired")

def main():
    print("🚀 JWT Token Helper\n")
    
    # Check user and provide guidance
    user_exists = get_fresh_token()
    
    if user_exists:
        show_frontend_auth_flow()
        
        print(f"\n✅ Next Steps:")
        print(f"1. Refresh your browser")
        print(f"2. Login with your credentials")
        print(f"3. The CORS issue should be fixed now!")
    else:
        print(f"\n❌ User setup needed:")
        print(f"1. Register a new account")
        print(f"2. Or check your email/username")

if __name__ == "__main__":
    main()