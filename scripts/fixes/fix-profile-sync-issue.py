#!/usr/bin/env python3
"""
Fix profile synchronization issues between Cognito and DynamoDB
- Sync profile data from Cognito to DynamoDB
- Set missing role in Cognito
- Reset password if needed
"""

import boto3
import json
import os
from datetime import datetime

def sync_profile_data(email):
    """Sync profile data from Cognito to DynamoDB and fix role"""
    try:
        # Initialize AWS clients
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
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
        
        # Get user from Cognito
        cognito_user = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=email
        )
        
        # Parse Cognito attributes
        cognito_attrs = {}
        for attr in cognito_user['UserAttributes']:
            cognito_attrs[attr['Name']] = attr['Value']
        
        print(f"✅ Retrieved Cognito user data:")
        print(f"   Email: {cognito_attrs.get('email')}")
        print(f"   Name: {cognito_attrs.get('name')}")
        print(f"   Given Name: {cognito_attrs.get('given_name')}")
        print(f"   Family Name: {cognito_attrs.get('family_name')}")
        print(f"   Role: {cognito_attrs.get('custom:role', 'Not set')}")
        
        # Find Users table
        tables = list(dynamodb.tables.all())
        users_table = None
        
        for table in tables:
            if 'users' in table.name.lower() and 'aquachain' in table.name.lower():
                users_table = dynamodb.Table(table.name)
                break
        
        if not users_table:
            print("❌ No AquaChain Users table found")
            return False
        
        # Get user from DynamoDB
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        
        if not response['Items']:
            print(f"❌ User {email} not found in DynamoDB")
            return False
        
        dynamodb_user = response['Items'][0]
        user_id = dynamodb_user['userId']
        
        print(f"✅ Retrieved DynamoDB user data:")
        print(f"   User ID: {user_id}")
        print(f"   Role: {dynamodb_user.get('role')}")
        print(f"   First Name: {dynamodb_user.get('firstName', 'Not set')}")
        print(f"   Last Name: {dynamodb_user.get('lastName', 'Not set')}")
        
        # Step 1: Update Cognito with role from DynamoDB
        if not cognito_attrs.get('custom:role') and dynamodb_user.get('role'):
            print(f"\n🔧 Setting role in Cognito to: {dynamodb_user['role']}")
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {
                        'Name': 'custom:role',
                        'Value': dynamodb_user['role']
                    }
                ]
            )
            print("✅ Role updated in Cognito")
        
        # Step 2: Update DynamoDB with profile data from Cognito
        update_expression = "SET "
        expression_values = {}
        updates = []
        
        # Update first name
        if cognito_attrs.get('given_name') and not dynamodb_user.get('firstName'):
            updates.append("firstName = :firstName")
            expression_values[':firstName'] = cognito_attrs['given_name']
        
        # Update last name
        if cognito_attrs.get('family_name') and not dynamodb_user.get('lastName'):
            updates.append("lastName = :lastName")
            expression_values[':lastName'] = cognito_attrs['family_name']
        
        # Update full name if needed
        if cognito_attrs.get('name') and dynamodb_user.get('name') != cognito_attrs['name']:
            updates.append("#name = :name")
            expression_values[':name'] = cognito_attrs['name']
        
        # Update modified timestamp
        updates.append("modifiedAt = :modifiedAt")
        expression_values[':modifiedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        if len(updates) > 1:  # More than just modifiedAt
            update_expression += ", ".join(updates)
            
            # Handle reserved keyword 'name'
            expression_names = {'#name': 'name'} if '#name' in update_expression else None
            
            print(f"\n🔧 Updating DynamoDB profile data...")
            
            kwargs = {
                'Key': {'userId': user_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if expression_names:
                kwargs['ExpressionAttributeNames'] = expression_names
            
            response = users_table.update_item(**kwargs)
            
            updated_user = response['Attributes']
            print("✅ DynamoDB profile updated:")
            print(f"   First Name: {updated_user.get('firstName', 'Not set')}")
            print(f"   Last Name: {updated_user.get('lastName', 'Not set')}")
            print(f"   Name: {updated_user.get('name', 'Not set')}")
        else:
            print("✅ DynamoDB profile data is already up to date")
        
        return True
        
    except Exception as e:
        print(f"❌ Error syncing profile data: {e}")
        return False

def reset_password_to_known(email, new_password="AquaChain2024!"):
    """Reset password to a known value"""
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
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=new_password,
            Permanent=True  # User won't need to change it
        )
        
        print(f"✅ Password reset for {email}")
        print(f"   New password: {new_password}")
        print("   Password is permanent (no change required)")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

def check_technician_tasks(user_id):
    """Check if user has any technician tasks"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Find technician tasks table
        tables = list(dynamodb.tables.all())
        tasks_table = None
        
        for table in tables:
            if 'technician' in table.name.lower() and 'task' in table.name.lower():
                tasks_table = dynamodb.Table(table.name)
                break
        
        if not tasks_table:
            print("❌ No technician tasks table found")
            return False
        
        # Check for tasks assigned to this user
        response = tasks_table.scan(
            FilterExpression='technicianId = :technicianId',
            ExpressionAttributeValues={':technicianId': user_id}
        )
        
        tasks = response['Items']
        print(f"✅ Found {len(tasks)} tasks for technician {user_id}")
        
        if tasks:
            print("   Recent tasks:")
            for task in tasks[:3]:  # Show first 3 tasks
                print(f"   - Task {task.get('taskId', 'Unknown')}: {task.get('status', 'Unknown status')}")
        
        return len(tasks) > 0
        
    except Exception as e:
        print(f"❌ Error checking technician tasks: {e}")
        return False

def main():
    print("🔧 AquaChain Profile Sync Fix")
    print("=" * 30)
    
    email = "leninat259@gmail.com"
    
    print(f"🔍 Fixing profile for: {email}")
    print("-" * 40)
    
    # Step 1: Sync profile data
    print("\n1. Syncing profile data between Cognito and DynamoDB...")
    if sync_profile_data(email):
        print("✅ Profile sync completed")
    else:
        print("❌ Profile sync failed")
        return
    
    # Step 2: Reset password
    print("\n2. Resetting password to known value...")
    if reset_password_to_known(email):
        print("✅ Password reset completed")
    else:
        print("❌ Password reset failed")
    
    # Step 3: Check technician tasks
    print("\n3. Checking technician tasks...")
    # Get user ID from DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        users_table = None
        
        for table in dynamodb.tables.all():
            if 'users' in table.name.lower() and 'aquachain' in table.name.lower():
                users_table = dynamodb.Table(table.name)
                break
        
        if users_table:
            response = users_table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            if response['Items']:
                user_id = response['Items'][0]['userId']
                check_technician_tasks(user_id)
    except Exception as e:
        print(f"❌ Error checking tasks: {e}")
    
    print("\n✅ Profile fix completed!")
    print("\nYou can now login with:")
    print(f"   Email: {email}")
    print("   Password: AquaChain2024!")

if __name__ == "__main__":
    main()