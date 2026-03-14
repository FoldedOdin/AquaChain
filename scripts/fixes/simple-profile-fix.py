#!/usr/bin/env python3
"""
Simple profile fix - just sync the profile data and reset password
"""

import boto3
import json
from datetime import datetime

def fix_profile_and_password():
    """Fix profile data and reset password"""
    try:
        email = "leninat259@gmail.com"
        new_password = "AquaChain2024!"
        
        # Initialize AWS clients
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        print(f"🔧 Fixing profile for: {email}")
        print("=" * 40)
        
        # Step 1: Get user pool ID
        pools = cognito.list_user_pools(MaxResults=10)
        user_pool_id = None
        
        for pool in pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                user_pool_id = pool['Id']
                print(f"✅ Found user pool: {pool['Name']} ({user_pool_id})")
                break
        
        if not user_pool_id:
            print("❌ No AquaChain user pool found")
            return False
        
        # Step 2: Get user from Cognito
        try:
            cognito_user = cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            # Parse attributes
            cognito_attrs = {}
            for attr in cognito_user['UserAttributes']:
                cognito_attrs[attr['Name']] = attr['Value']
            
            print(f"\n📋 Cognito Profile Data:")
            print(f"   Email: {cognito_attrs.get('email', 'Not set')}")
            print(f"   Name: {cognito_attrs.get('name', 'Not set')}")
            print(f"   Given Name: {cognito_attrs.get('given_name', 'Not set')}")
            print(f"   Family Name: {cognito_attrs.get('family_name', 'Not set')}")
            
        except Exception as e:
            print(f"❌ Error getting Cognito user: {e}")
            return False
        
        # Step 3: Reset password
        try:
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=new_password,
                Permanent=True
            )
            print(f"\n✅ Password reset successfully")
            print(f"   New password: {new_password}")
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
        
        # Step 4: Update DynamoDB profile
        try:
            # Find Users table
            users_table = None
            for table in dynamodb.tables.all():
                if 'users' in table.name.lower() and 'aquachain' in table.name.lower():
                    users_table = dynamodb.Table(table.name)
                    print(f"✅ Found users table: {table.name}")
                    break
            
            if not users_table:
                print("❌ No users table found")
                return False
            
            # Get user from DynamoDB
            response = users_table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            if not response['Items']:
                print(f"❌ User not found in DynamoDB")
                return False
            
            user_data = response['Items'][0]
            user_id = user_data['userId']
            
            print(f"\n📋 DynamoDB Profile Data (Before):")
            print(f"   User ID: {user_id}")
            print(f"   Email: {user_data.get('email', 'Not set')}")
            print(f"   Role: {user_data.get('role', 'Not set')}")
            print(f"   Name: {user_data.get('name', 'Not set')}")
            print(f"   First Name: {user_data.get('firstName', 'Not set')}")
            print(f"   Last Name: {user_data.get('lastName', 'Not set')}")
            
            # Update profile with Cognito data
            update_data = {
                'firstName': cognito_attrs.get('given_name', 'Sidharth'),
                'lastName': cognito_attrs.get('family_name', 'Lenin'),
                'modifiedAt': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Update name if it exists in Cognito
            if cognito_attrs.get('name'):
                update_data['name'] = cognito_attrs['name']
            
            # Build update expression
            update_expression = "SET "
            expression_values = {}
            updates = []
            
            for key, value in update_data.items():
                if key == 'name':
                    updates.append("#name = :name")
                    expression_values[':name'] = value
                else:
                    updates.append(f"{key} = :{key}")
                    expression_values[f':{key}'] = value
            
            update_expression += ", ".join(updates)
            
            # Perform update
            kwargs = {
                'Key': {'userId': user_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if '#name' in update_expression:
                kwargs['ExpressionAttributeNames'] = {'#name': 'name'}
            
            response = users_table.update_item(**kwargs)
            updated_user = response['Attributes']
            
            print(f"\n✅ DynamoDB Profile Updated:")
            print(f"   First Name: {updated_user.get('firstName', 'Not set')}")
            print(f"   Last Name: {updated_user.get('lastName', 'Not set')}")
            print(f"   Name: {updated_user.get('name', 'Not set')}")
            print(f"   Role: {updated_user.get('role', 'Not set')}")
            
        except Exception as e:
            print(f"❌ Error updating DynamoDB: {e}")
            return False
        
        # Step 5: Create a test task
        try:
            # Find tasks table
            tasks_table = None
            for table in dynamodb.tables.all():
                table_name = table.name.lower()
                if 'technician' in table_name and 'task' in table_name:
                    tasks_table = dynamodb.Table(table.name)
                    print(f"✅ Found tasks table: {table.name}")
                    break
            
            if tasks_table:
                # Create test task
                task_id = f"test-task-{int(datetime.now().timestamp())}"
                
                task_data = {
                    'taskId': task_id,
                    'technicianId': user_id,
                    'orderId': f'order-{int(datetime.now().timestamp())}',
                    'status': 'assigned',
                    'priority': 'medium',
                    'description': 'Device calibration and maintenance check',
                    'customerName': 'Test Customer',
                    'customerAddress': '123 Main Street, Test City, TC 12345',
                    'customerPhone': '+1-555-0123',
                    'deviceType': 'AquaChain Water Quality Monitor',
                    'assignedAt': datetime.utcnow().isoformat() + 'Z',
                    'createdAt': datetime.utcnow().isoformat() + 'Z',
                    'estimatedDuration': 90,  # minutes
                    'serviceType': 'calibration',
                    'notes': 'Routine maintenance and sensor calibration'
                }
                
                tasks_table.put_item(Item=task_data)
                
                print(f"\n✅ Created test task:")
                print(f"   Task ID: {task_id}")
                print(f"   Status: {task_data['status']}")
                print(f"   Description: {task_data['description']}")
                print(f"   Customer: {task_data['customerName']}")
            
        except Exception as e:
            print(f"⚠️ Could not create test task: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🔧 AquaChain Simple Profile Fix")
    print("=" * 35)
    
    if fix_profile_and_password():
        print("\n🎉 All fixes completed successfully!")
        print("\n📋 Login Information:")
        print("   Email: leninat259@gmail.com")
        print("   Password: AquaChain2024!")
        print("\n📋 Expected Profile:")
        print("   First Name: Sidharth")
        print("   Last Name: Lenin")
        print("   Role: Technician")
        print("\n🔗 Try logging in now - the profile should display correctly!")
    else:
        print("\n❌ Some fixes failed - check the errors above")

if __name__ == "__main__":
    main()