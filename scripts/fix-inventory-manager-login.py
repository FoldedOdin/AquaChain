#!/usr/bin/env python3
"""
Fix Inventory Manager Login Issue
Resets password for the inventory manager user so they can sign in
"""

import boto3
import json
import secrets
import string
from botocore.exceptions import ClientError

def generate_temp_password():
    """Generate a secure temporary password"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(12))

def fix_inventory_manager_login():
    """Fix the inventory manager login issue"""
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp')
    
    # You'll need to replace these with your actual values
    USER_POOL_ID = input("Enter your Cognito User Pool ID: ").strip()
    USERNAME = "karthikpradeep897@gmail.com"  # The inventory manager's email
    
    try:
        print(f"Fixing login for user: {USERNAME}")
        
        # Generate new temporary password
        temp_password = generate_temp_password()
        print(f"Generated temporary password: {temp_password}")
        
        # Check if user exists
        try:
            user_response = cognito_client.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=USERNAME
            )
            print("✓ User found in Cognito")
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                print("✗ User not found in Cognito")
                return
            else:
                raise
        
        # Set temporary password
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=USERNAME,
                Password=temp_password,
                Permanent=False  # Force password change on first login
            )
            print("✓ Temporary password set")
        except ClientError as e:
            print(f"✗ Failed to set password: {e}")
            return
        
        # Ensure user is in the correct group (technicians for inventory manager)
        try:
            # Remove from any existing groups first
            try:
                groups_response = cognito_client.admin_list_groups_for_user(
                    UserPoolId=USER_POOL_ID,
                    Username=USERNAME
                )
                for group in groups_response.get('Groups', []):
                    cognito_client.admin_remove_user_from_group(
                        UserPoolId=USER_POOL_ID,
                        Username=USERNAME,
                        GroupName=group['GroupName']
                    )
                    print(f"✓ Removed from group: {group['GroupName']}")
            except:
                pass  # User might not be in any groups
            
            # Add to technicians group
            cognito_client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=USERNAME,
                GroupName='technicians'
            )
            print("✓ Added to technicians group")
            
        except ClientError as e:
            print(f"⚠ Warning: Could not update user groups: {e}")
        
        # Enable the user account
        try:
            cognito_client.admin_enable_user(
                UserPoolId=USER_POOL_ID,
                Username=USERNAME
            )
            print("✓ User account enabled")
        except ClientError as e:
            print(f"⚠ Warning: Could not enable user: {e}")
        
        # Set user status to force password change
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=USERNAME,
                Password=temp_password,
                Permanent=False
            )
            print("✓ User will be required to change password on first login")
        except ClientError as e:
            print(f"⚠ Warning: Could not set password change requirement: {e}")
        
        print("\n" + "="*50)
        print("✅ Inventory Manager Login Fixed!")
        print("="*50)
        print(f"Username: {USERNAME}")
        print(f"Temporary Password: {temp_password}")
        print("\nInstructions for the user:")
        print("1. Go to the AquaChain login page")
        print("2. Enter your email and the temporary password above")
        print("3. You will be prompted to create a new permanent password")
        print("4. After setting the new password, you can access the system")
        print("\nNote: Save this temporary password securely and share it with the user.")
        
    except Exception as e:
        print(f"✗ Error fixing user login: {e}")
        return

def get_user_pool_id():
    """Helper to get User Pool ID from CloudFormation"""
    try:
        cf_client = boto3.client('cloudformation')
        response = cf_client.describe_stacks(StackName='AquaChain-API-dev')
        
        for output in response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'UserPoolId':
                return output['OutputValue']
        
        print("Could not find User Pool ID in CloudFormation outputs")
        return None
        
    except Exception as e:
        print(f"Could not get User Pool ID from CloudFormation: {e}")
        return None

if __name__ == "__main__":
    print("🔧 AquaChain - Fix Inventory Manager Login")
    print("="*50)
    
    # Try to get User Pool ID automatically
    user_pool_id = get_user_pool_id()
    if user_pool_id:
        print(f"Found User Pool ID: {user_pool_id}")
        confirm = input("Use this User Pool ID? (y/n): ").strip().lower()
        if confirm != 'y':
            user_pool_id = input("Enter your Cognito User Pool ID: ").strip()
    else:
        user_pool_id = input("Enter your Cognito User Pool ID: ").strip()
    
    if not user_pool_id:
        print("User Pool ID is required")
        exit(1)
    
    # Update the global variable
    globals()['USER_POOL_ID'] = user_pool_id
    
    fix_inventory_manager_login()