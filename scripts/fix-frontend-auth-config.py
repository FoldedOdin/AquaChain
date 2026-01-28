#!/usr/bin/env python3
"""
Fix Frontend Authentication Configuration
Updates frontend to use real Cognito instead of mock auth
"""

import boto3
import os
from botocore.exceptions import ClientError

def get_cognito_config():
    """Get Cognito configuration from AWS"""
    try:
        # Try to read saved User Pool ID
        user_pool_id = None
        try:
            with open('user_pool_id.txt', 'r') as f:
                user_pool_id = f.read().strip()
        except FileNotFoundError:
            pass
        
        if not user_pool_id:
            # Try CloudFormation
            cf_client = boto3.client('cloudformation')
            stack_names = ['AquaChain-API-dev', 'aquachain-api-dev']
            
            for stack_name in stack_names:
                try:
                    response = cf_client.describe_stacks(StackName=stack_name)
                    for output in response['Stacks'][0]['Outputs']:
                        if output['OutputKey'] in ['UserPoolId', 'CognitoUserPoolId']:
                            user_pool_id = output['OutputValue']
                            break
                    if user_pool_id:
                        break
                except ClientError:
                    continue
        
        if not user_pool_id:
            print("❌ Could not find User Pool ID")
            return None, None
        
        # Get User Pool Client ID
        cognito_client = boto3.client('cognito-idp')
        clients_response = cognito_client.list_user_pool_clients(
            UserPoolId=user_pool_id,
            MaxResults=10
        )
        
        if not clients_response['UserPoolClients']:
            print("❌ No User Pool Clients found")
            return user_pool_id, None
        
        client_id = clients_response['UserPoolClients'][0]['ClientId']
        
        print(f"✓ Found User Pool ID: {user_pool_id}")
        print(f"✓ Found Client ID: {client_id}")
        
        return user_pool_id, client_id
        
    except Exception as e:
        print(f"❌ Error getting Cognito config: {e}")
        return None, None

def update_frontend_config(user_pool_id, client_id):
    """Update frontend configuration to use real Cognito"""
    
    # Create the correct .env.local configuration
    env_content = f"""# AquaChain Frontend Configuration - Real Cognito Auth
# Updated automatically to use real Cognito authentication

# Cognito Configuration
REACT_APP_USER_POOL_ID={user_pool_id}
REACT_APP_USER_POOL_CLIENT_ID={client_id}
REACT_APP_REGION=ap-south-1

# API Configuration
REACT_APP_API_ENDPOINT=http://localhost:3002

# Disable mock auth - use real Cognito
REACT_APP_USE_MOCK_AUTH=false

# Optional: Enable additional features
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_AB_TESTING=false
"""
    
    try:
        # Backup existing .env.local if it exists
        if os.path.exists('frontend/.env.local'):
            with open('frontend/.env.local.backup', 'w') as backup_file:
                with open('frontend/.env.local', 'r') as original_file:
                    backup_file.write(original_file.read())
            print("✓ Backed up existing .env.local to .env.local.backup")
        
        # Write new configuration
        with open('frontend/.env.local', 'w') as f:
            f.write(env_content)
        
        print("✅ Updated frontend/.env.local with real Cognito configuration")
        return True
        
    except Exception as e:
        print(f"❌ Error updating frontend config: {e}")
        return False

def main():
    print("🔧 Fix Frontend Authentication Configuration")
    print("=" * 50)
    print("This will update your frontend to use real Cognito authentication")
    print("instead of mock authentication.")
    print("=" * 50)
    
    # Get Cognito configuration
    user_pool_id, client_id = get_cognito_config()
    
    if not user_pool_id or not client_id:
        print("\n❌ Cannot proceed without Cognito configuration")
        print("\nTry running:")
        print("1. scripts\\find-user-pool-id.bat")
        print("2. Then run this script again")
        return
    
    # Update frontend configuration
    success = update_frontend_config(user_pool_id, client_id)
    
    if success:
        print("\n✅ Frontend configuration updated successfully!")
        print("\n📋 NEXT STEPS:")
        print("1. Restart your frontend development server:")
        print("   cd frontend")
        print("   npm start")
        print("\n2. Try logging in with your supply chain users:")
        
        # Show user credentials if available
        try:
            import json
            with open('supply_chain_users_login_credentials.json', 'r') as f:
                users = json.load(f)
            
            print("\n   Available users:")
            for user in users[:2]:  # Show first 2
                print(f"   • {user['name']}: {user['email']}")
                print(f"     Password: {user['password']}")
        except:
            print("   (Check supply_chain_users_login_info.txt for credentials)")
        
        print("\n3. If login still fails, run:")
        print("   scripts\\verify-users-and-config.bat")
    
    else:
        print("\n❌ Failed to update frontend configuration")

if __name__ == "__main__":
    main()