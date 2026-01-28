#!/usr/bin/env python3
"""
Verify Users and Configuration
Checks if users were created correctly and diagnoses login issues
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def check_user_pool_config():
    """Check User Pool configuration"""
    try:
        # Try to read saved User Pool ID
        user_pool_id = None
        try:
            with open('user_pool_id.txt', 'r') as f:
                user_pool_id = f.read().strip()
        except FileNotFoundError:
            print("⚠ user_pool_id.txt not found")
        
        if not user_pool_id:
            print("❌ No User Pool ID found. Run scripts/find-user-pool-id.bat first")
            return None
        
        print(f"✓ Using User Pool ID: {user_pool_id}")
        
        # Get User Pool details
        cognito_client = boto3.client('cognito-idp')
        pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
        
        pool = pool_response['UserPool']
        print(f"✓ User Pool Name: {pool['Name']}")
        print(f"✓ User Pool Status: {pool['Status']}")
        print(f"✓ User Pool Domain: {pool.get('Domain', 'Not configured')}")
        
        # Check User Pool Client
        clients_response = cognito_client.list_user_pool_clients(
            UserPoolId=user_pool_id,
            MaxResults=10
        )
        
        if clients_response['UserPoolClients']:
            client = clients_response['UserPoolClients'][0]
            client_id = client['ClientId']
            print(f"✓ User Pool Client ID: {client_id}")
            
            # Get client details
            client_details = cognito_client.describe_user_pool_client(
                UserPoolId=user_pool_id,
                ClientId=client_id
            )
            
            client_config = client_details['UserPoolClient']
            print(f"✓ Client Name: {client_config['ClientName']}")
            print(f"✓ Auth Flows: {client_config.get('ExplicitAuthFlows', [])}")
            
            return user_pool_id, client_id
        else:
            print("❌ No User Pool Clients found")
            return user_pool_id, None
            
    except Exception as e:
        print(f"❌ Error checking User Pool config: {e}")
        return None, None

def verify_created_users(user_pool_id):
    """Verify the created users exist in Cognito"""
    try:
        # Read the created users
        with open('supply_chain_users_login_credentials.json', 'r') as f:
            users = json.load(f)
        
        cognito_client = boto3.client('cognito-idp')
        
        print(f"\n🔍 Verifying {len(users)} created users...")
        
        verified_users = []
        for user in users:
            email = user['email']
            try:
                # Check if user exists
                response = cognito_client.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
                
                user_status = response['UserStatus']
                enabled = response['Enabled']
                
                print(f"✓ {user['name']}: {email}")
                print(f"  Status: {user_status}, Enabled: {enabled}")
                
                # Check user groups
                try:
                    groups_response = cognito_client.admin_list_groups_for_user(
                        UserPoolId=user_pool_id,
                        Username=email
                    )
                    groups = [g['GroupName'] for g in groups_response.get('Groups', [])]
                    print(f"  Groups: {groups}")
                except Exception as e:
                    print(f"  Groups: Error - {e}")
                
                verified_users.append({
                    **user,
                    'cognito_status': user_status,
                    'enabled': enabled,
                    'groups': groups if 'groups' in locals() else []
                })
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'UserNotFoundException':
                    print(f"❌ {user['name']}: {email} - NOT FOUND in Cognito")
                else:
                    print(f"❌ {user['name']}: {email} - Error: {e}")
        
        return verified_users
        
    except FileNotFoundError:
        print("❌ supply_chain_users_login_credentials.json not found")
        print("   Run the user creation script first")
        return []
    except Exception as e:
        print(f"❌ Error verifying users: {e}")
        return []

def check_frontend_config():
    """Check frontend configuration"""
    print(f"\n🔍 Checking frontend configuration...")
    
    # Check frontend .env files
    env_files = [
        'frontend/.env',
        'frontend/.env.local',
        'frontend/.env.development',
        'frontend/.env.production'
    ]
    
    found_config = False
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✓ Found: {env_file}")
            found_config = True
            
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                if 'REACT_APP_USER_POOL_ID' in content:
                    # Extract the value
                    for line in content.split('\n'):
                        if line.startswith('REACT_APP_USER_POOL_ID'):
                            print(f"  {line}")
                            
                if 'REACT_APP_USER_POOL_CLIENT_ID' in content:
                    for line in content.split('\n'):
                        if line.startswith('REACT_APP_USER_POOL_CLIENT_ID'):
                            print(f"  {line}")
                            
                if 'REACT_APP_API_ENDPOINT' in content:
                    for line in content.split('\n'):
                        if line.startswith('REACT_APP_API_ENDPOINT'):
                            print(f"  {line}")
                            
            except Exception as e:
                print(f"  Error reading {env_file}: {e}")
    
    if not found_config:
        print("⚠ No frontend .env files found")
        print("  Frontend may be using default/hardcoded values")

def test_authentication(user_pool_id, client_id, test_user):
    """Test authentication with one of the created users"""
    if not client_id:
        print("❌ Cannot test authentication - no client ID")
        return
    
    try:
        cognito_client = boto3.client('cognito-idp')
        
        print(f"\n🧪 Testing authentication for: {test_user['email']}")
        
        # Try to initiate auth
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': test_user['email'],
                'PASSWORD': test_user['password']
            }
        )
        
        if 'AuthenticationResult' in response:
            print("✅ Authentication successful!")
            print(f"  Access token received (length: {len(response['AuthenticationResult']['AccessToken'])})")
            return True
        elif 'ChallengeName' in response:
            print(f"⚠ Authentication challenge required: {response['ChallengeName']}")
            return False
        else:
            print("❌ Unexpected authentication response")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Authentication failed: {error_code} - {error_message}")
        
        if error_code == 'UserNotFoundException':
            print("  → User not found in this User Pool")
        elif error_code == 'NotAuthorizedException':
            print("  → Invalid credentials or user not confirmed")
        elif error_code == 'UserNotConfirmedException':
            print("  → User needs to be confirmed")
            
        return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def provide_solutions(user_pool_id, client_id, verified_users):
    """Provide solutions based on findings"""
    print(f"\n💡 SOLUTIONS:")
    print("=" * 50)
    
    if not verified_users:
        print("1. Users not found - recreate them:")
        print("   scripts\\create-supply-chain-users-with-passwords.bat")
        return
    
    # Check if frontend config matches
    if user_pool_id and client_id:
        print("1. Update frontend configuration:")
        print(f"   Create/update frontend/.env.local with:")
        print(f"   REACT_APP_USER_POOL_ID={user_pool_id}")
        print(f"   REACT_APP_USER_POOL_CLIENT_ID={client_id}")
        print(f"   REACT_APP_REGION=ap-south-1")
        
        # Create the .env.local file
        env_content = f"""# AquaChain Frontend Configuration - Auto-generated
REACT_APP_USER_POOL_ID={user_pool_id}
REACT_APP_USER_POOL_CLIENT_ID={client_id}
REACT_APP_REGION=ap-south-1
REACT_APP_API_ENDPOINT=http://localhost:3002
"""
        
        try:
            with open('frontend/.env.local', 'w') as f:
                f.write(env_content)
            print("   ✓ Created frontend/.env.local")
        except Exception as e:
            print(f"   ❌ Could not create .env.local: {e}")
    
    print("\n2. Restart your frontend development server:")
    print("   cd frontend")
    print("   npm start")
    
    print("\n3. Test login with these credentials:")
    for user in verified_users[:2]:  # Show first 2 users
        print(f"   Email: {user['email']}")
        print(f"   Password: {user['password']}")

def main():
    print("🔧 AquaChain - Verify Users and Configuration")
    print("=" * 60)
    
    # Step 1: Check User Pool configuration
    user_pool_id, client_id = check_user_pool_config()
    
    if not user_pool_id:
        print("\n❌ Cannot proceed without User Pool ID")
        return
    
    # Step 2: Verify created users
    verified_users = verify_created_users(user_pool_id)
    
    # Step 3: Check frontend configuration
    check_frontend_config()
    
    # Step 4: Test authentication with one user
    if verified_users and client_id:
        test_authentication(user_pool_id, client_id, verified_users[0])
    
    # Step 5: Provide solutions
    provide_solutions(user_pool_id, client_id, verified_users)

if __name__ == "__main__":
    main()