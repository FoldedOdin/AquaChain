#!/usr/bin/env python3

import boto3
import json

def create_simple_admin():
    """Create a simple admin user without custom attributes."""
    
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    user_pool_id = 'ap-south-1_QUDl7hG8u'
    
    # Admin user credentials
    email = "admin@aquachain.com"
    password = "AdminPassword123!"
    
    print(f"👑 Creating simple admin user: {email}")
    
    try:
        # Create user with basic attributes only
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'name',
                    'Value': 'Admin User'
                }
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        
        print("✅ Admin user created successfully!")
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        print("✅ Admin password set as permanent!")
        
        # Test authentication
        print("🧪 Testing admin authentication...")
        
        auth_response = cognito_client.initiate_auth(
            ClientId='692o9a3pjudl1vudfgqpr5nuln',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        print("✅ Admin authentication successful!")
        return True
        
    except cognito_client.exceptions.UsernameExistsException:
        print("⚠️ Admin user already exists, trying to fix password...")
        
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            
            # Test authentication
            auth_response = cognito_client.initiate_auth(
                ClientId='692o9a3pjudl1vudfgqpr5nuln',
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            print("✅ Admin password fixed and authentication successful!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix admin password: {str(e)}")
            return False
    
    except Exception as e:
        print(f"❌ Failed to create admin user: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_simple_admin()
    
    if success:
        print("\n🎯 Admin credentials ready:")
        print("📧 Email: admin@aquachain.com")
        print("🔑 Password: AdminPassword123!")
    else:
        print("\n❌ Failed to set up admin user")