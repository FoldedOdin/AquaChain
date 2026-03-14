#!/usr/bin/env python3
"""
Diagnose authentication and profile issues for AquaChain
- Check if user exists in Cognito
- Check if user data is properly stored
- Verify profile information retrieval
"""

import boto3
import json
import os
from datetime import datetime

def check_cognito_user(email):
    """Check if user exists in Cognito and get their attributes"""
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Get user pool ID from environment or use default
        user_pool_id = os.environ.get('USER_POOL_ID', 'ap-south-1_example')
        
        # List user pools to find the correct one
        pools = cognito.list_user_pools(MaxResults=10)
        aquachain_pool = None
        
        for pool in pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                aquachain_pool = pool
                user_pool_id = pool['Id']
                break
        
        if not aquachain_pool:
            print("❌ No AquaChain user pool found")
            return None
            
        print(f"✅ Found AquaChain user pool: {aquachain_pool['Name']} ({user_pool_id})")
        
        # Try to get user by email
        try:
            response = cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            user_data = {
                'username': response['Username'],
                'user_status': response['UserStatus'],
                'enabled': response['Enabled'],
                'created': response['UserCreateDate'].isoformat(),
                'modified': response['UserLastModifiedDate'].isoformat(),
                'attributes': {}
            }
            
            # Parse user attributes
            for attr in response['UserAttributes']:
                user_data['attributes'][attr['Name']] = attr['Value']
            
            print(f"✅ User found in Cognito:")
            print(f"   Username: {user_data['username']}")
            print(f"   Status: {user_data['user_status']}")
            print(f"   Enabled: {user_data['enabled']}")
            print(f"   Email: {user_data['attributes'].get('email', 'Not set')}")
            print(f"   Email Verified: {user_data['attributes'].get('email_verified', 'Not set')}")
            print(f"   Role: {user_data['attributes'].get('custom:role', 'Not set')}")
            print(f"   Name: {user_data['attributes'].get('name', 'Not set')}")
            print(f"   Given Name: {user_data['attributes'].get('given_name', 'Not set')}")
            print(f"   Family Name: {user_data['attributes'].get('family_name', 'Not set')}")
            
            return user_data
            
        except cognito.exceptions.UserNotFoundException:
            print(f"❌ User {email} not found in Cognito")
            return None
            
    except Exception as e:
        print(f"❌ Error checking Cognito user: {e}")
        return None

def check_dynamodb_user(email):
    """Check if user exists in DynamoDB Users table"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Find the Users table
        tables = list(dynamodb.tables.all())
        users_table = None
        
        for table in tables:
            if 'users' in table.name.lower() and 'aquachain' in table.name.lower():
                users_table = dynamodb.Table(table.name)
                break
        
        if not users_table:
            print("❌ No AquaChain Users table found")
            return None
            
        print(f"✅ Found Users table: {users_table.name}")
        
        # Try to get user by email
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        
        if response['Items']:
            user_data = response['Items'][0]
            print(f"✅ User found in DynamoDB:")
            print(f"   User ID: {user_data.get('userId', 'Not set')}")
            print(f"   Email: {user_data.get('email', 'Not set')}")
            print(f"   Role: {user_data.get('role', 'Not set')}")
            print(f"   Name: {user_data.get('name', 'Not set')}")
            print(f"   First Name: {user_data.get('firstName', 'Not set')}")
            print(f"   Last Name: {user_data.get('lastName', 'Not set')}")
            print(f"   Created: {user_data.get('createdAt', 'Not set')}")
            return user_data
        else:
            print(f"❌ User {email} not found in DynamoDB")
            return None
            
    except Exception as e:
        print(f"❌ Error checking DynamoDB user: {e}")
        return None

def reset_user_password(email, temp_password="TempPass123!"):
    """Reset user password in Cognito"""
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Get user pool ID
        pools = cognito.list_user_pools(MaxResults=10)
        user_pool_id = None
        
        for pool in pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                user_pool_id = pool['Id']
                break
        
        if not user_pool_id:
            print("❌ No AquaChain user pool found")
            return False
        
        # Set temporary password
        response = cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=temp_password,
            Permanent=False  # User will need to change on next login
        )
        
        print(f"✅ Temporary password set for {email}")
        print(f"   Temporary password: {temp_password}")
        print("   User will be prompted to change password on next login")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

def update_user_profile(email, first_name=None, last_name=None):
    """Update user profile attributes in Cognito"""
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Get user pool ID
        pools = cognito.list_user_pools(MaxResults=10)
        user_pool_id = None
        
        for pool in pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                user_pool_id = pool['Id']
                break
        
        if not user_pool_id:
            print("❌ No AquaChain user pool found")
            return False
        
        # Prepare attributes to update
        attributes = []
        
        if first_name:
            attributes.append({
                'Name': 'given_name',
                'Value': first_name
            })
            attributes.append({
                'Name': 'name',
                'Value': f"{first_name} {last_name or ''}".strip()
            })
        
        if last_name:
            attributes.append({
                'Name': 'family_name',
                'Value': last_name
            })
        
        if attributes:
            response = cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=attributes
            )
            
            print(f"✅ Profile updated for {email}")
            if first_name:
                print(f"   First Name: {first_name}")
            if last_name:
                print(f"   Last Name: {last_name}")
            return True
        else:
            print("❌ No attributes to update")
            return False
        
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        return False

def main():
    print("🔍 AquaChain Authentication & Profile Diagnosis")
    print("=" * 50)
    
    # Get email from user
    email = input("Enter email to diagnose: ").strip()
    if not email:
        email = "leninat259@gmail.com"  # Default from the issue
    
    print(f"\n🔍 Checking user: {email}")
    print("-" * 30)
    
    # Check Cognito
    print("\n1. Checking AWS Cognito...")
    cognito_user = check_cognito_user(email)
    
    # Check DynamoDB
    print("\n2. Checking DynamoDB...")
    dynamodb_user = check_dynamodb_user(email)
    
    # Provide recommendations
    print("\n📋 Recommendations:")
    print("-" * 20)
    
    if not cognito_user:
        print("❌ User not found in Cognito - need to create user")
    elif cognito_user['user_status'] != 'CONFIRMED':
        print(f"⚠️ User status is {cognito_user['user_status']} - may need confirmation")
    
    if not dynamodb_user:
        print("❌ User not found in DynamoDB - may need to sync from Cognito")
    
    # Check if profile data is missing
    if cognito_user:
        missing_attrs = []
        if not cognito_user['attributes'].get('given_name'):
            missing_attrs.append('First Name')
        if not cognito_user['attributes'].get('family_name'):
            missing_attrs.append('Last Name')
        if not cognito_user['attributes'].get('name'):
            missing_attrs.append('Full Name')
        
        if missing_attrs:
            print(f"⚠️ Missing profile attributes: {', '.join(missing_attrs)}")
    
    # Offer fixes
    print("\n🔧 Available Fixes:")
    print("-" * 15)
    
    if cognito_user:
        print("1. Reset password (sets temporary password)")
        print("2. Update profile (set first/last name)")
        
        choice = input("\nEnter choice (1-2) or press Enter to skip: ").strip()
        
        if choice == "1":
            if reset_user_password(email):
                print("✅ Password reset complete")
        elif choice == "2":
            first_name = input("Enter first name: ").strip()
            last_name = input("Enter last name: ").strip()
            if first_name or last_name:
                update_user_profile(email, first_name, last_name)

if __name__ == "__main__":
    main()