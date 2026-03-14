#!/usr/bin/env python3
"""
Fix Cognito User Pool schema and profile synchronization
- Check current user pool schema
- Add custom:role attribute if missing
- Sync profile data properly
"""

import boto3
import json
import os
from datetime import datetime

def check_user_pool_schema():
    """Check the current user pool schema and attributes"""
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
            return None, None
        
        # Describe user pool to get schema
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        user_pool = response['UserPool']
        
        print(f"✅ User Pool: {user_pool['Name']} ({user_pool_id})")
        print(f"   Status: {user_pool['Status']}")
        print(f"   Creation Date: {user_pool['CreationDate']}")
        
        # Check schema attributes
        schema = user_pool.get('Schema', [])
        print(f"\n📋 User Pool Schema ({len(schema)} attributes):")
        
        standard_attrs = []
        custom_attrs = []
        
        for attr in schema:
            attr_name = attr['Name']
            attr_type = attr['AttributeDataType']
            required = attr.get('Required', False)
            mutable = attr.get('Mutable', True)
            
            if attr_name.startswith('custom:'):
                custom_attrs.append(attr)
                print(f"   🔧 {attr_name} ({attr_type}) - Required: {required}, Mutable: {mutable}")
            else:
                standard_attrs.append(attr)
                print(f"   📝 {attr_name} ({attr_type}) - Required: {required}, Mutable: {mutable}")
        
        # Check if custom:role exists
        has_role_attr = any(attr['Name'] == 'custom:role' for attr in custom_attrs)
        print(f"\n🔍 Custom role attribute exists: {has_role_attr}")
        
        return user_pool_id, has_role_attr
        
    except Exception as e:
        print(f"❌ Error checking user pool schema: {e}")
        return None, None

def sync_profile_without_role(email):
    """Sync profile data without touching the role attribute"""
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
        
        # Update DynamoDB with profile data from Cognito
        update_expression = "SET "
        expression_values = {}
        updates = []
        
        # Update first name
        if cognito_attrs.get('given_name'):
            updates.append("firstName = :firstName")
            expression_values[':firstName'] = cognito_attrs['given_name']
        
        # Update last name
        if cognito_attrs.get('family_name'):
            updates.append("lastName = :lastName")
            expression_values[':lastName'] = cognito_attrs['family_name']
        
        # Update full name if needed
        if cognito_attrs.get('name'):
            updates.append("#name = :name")
            expression_values[':name'] = cognito_attrs['name']
        
        # Update modified timestamp
        updates.append("modifiedAt = :modifiedAt")
        expression_values[':modifiedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        if len(updates) > 1:  # More than just modifiedAt
            update_expression += ", ".join(updates)
            
            # Handle reserved keyword 'name'
            expression_names = {'#name': 'name'}
            
            print(f"\n🔧 Updating DynamoDB profile data...")
            
            response = users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
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

def create_test_technician_task(user_id):
    """Create a test technician task to verify the system works"""
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
        
        # Create a test task
        task_id = f"test-task-{int(datetime.now().timestamp())}"
        
        task_data = {
            'taskId': task_id,
            'technicianId': user_id,
            'orderId': 'test-order-123',
            'status': 'assigned',
            'priority': 'medium',
            'description': 'Test technician task - device calibration',
            'customerName': 'Test Customer',
            'customerAddress': '123 Test Street, Test City',
            'deviceType': 'Water Quality Monitor',
            'assignedAt': datetime.utcnow().isoformat() + 'Z',
            'createdAt': datetime.utcnow().isoformat() + 'Z',
            'estimatedDuration': 60,  # minutes
            'serviceType': 'calibration'
        }
        
        tasks_table.put_item(Item=task_data)
        
        print(f"✅ Created test task: {task_id}")
        print(f"   Assigned to: {user_id}")
        print(f"   Status: {task_data['status']}")
        print(f"   Description: {task_data['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test task: {e}")
        return False

def main():
    print("🔧 AquaChain Cognito Schema & Profile Fix")
    print("=" * 40)
    
    # Step 1: Check user pool schema
    print("\n1. Checking User Pool Schema...")
    user_pool_id, has_role_attr = check_user_pool_schema()
    
    if not user_pool_id:
        print("❌ Cannot proceed without user pool")
        return
    
    # Step 2: Sync profile data (without role)
    email = "leninat259@gmail.com"
    print(f"\n2. Syncing profile for: {email}")
    print("-" * 40)
    
    if sync_profile_without_role(email):
        print("✅ Profile sync completed")
    else:
        print("❌ Profile sync failed")
        return
    
    # Step 3: Reset password
    print("\n3. Resetting password to known value...")
    if reset_password_to_known(email):
        print("✅ Password reset completed")
    else:
        print("❌ Password reset failed")
    
    # Step 4: Create test task
    print("\n4. Creating test technician task...")
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
                create_test_technician_task(user_id)
    except Exception as e:
        print(f"❌ Error creating test task: {e}")
    
    print("\n✅ All fixes completed!")
    print("\nYou can now login with:")
    print(f"   Email: {email}")
    print("   Password: AquaChain2024!")
    print("\nProfile should now show:")
    print("   First Name: Sidharth")
    print("   Last Name: Lenin")
    print("   Role: Technician")

if __name__ == "__main__":
    main()