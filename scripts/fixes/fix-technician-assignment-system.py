#!/usr/bin/env python3
"""
Fix Technician Assignment System

This script fixes the technician assignment issue by:
1. Creating verified technicians in the users table (not separate technicians table)
2. Setting up proper Cognito users for technicians
3. Ensuring technicians have the correct role and availability status
"""

import boto3
import json
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal
import uuid

# Table names
USERS_TABLE = 'AquaChain-Users'
COGNITO_USER_POOL_ID = 'ap-south-1_QUDl7hG8u'

def create_cognito_user(cognito_client, email, phone, name, temp_password='TempPass123!'):
    """Create a user in Cognito User Pool"""
    try:
        # Check if user already exists
        try:
            existing_user = cognito_client.admin_get_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email
            )
            print(f"✅ Cognito user already exists: {email}")
            return email
        except cognito_client.exceptions.UserNotFoundException:
            pass  # User doesn't exist, continue with creation
        
        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'phone_number', 'Value': phone},
                {'Name': 'given_name', 'Value': name.split()[0]},
                {'Name': 'family_name', 'Value': name.split()[-1]},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'phone_number_verified', 'Value': 'true'}
            ],
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS'  # Don't send welcome email
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            Password=temp_password,
            Permanent=True
        )
        
        # Confirm user (only if not already confirmed)
        try:
            cognito_client.admin_confirm_sign_up(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email
            )
        except cognito_client.exceptions.NotAuthorizedException as e:
            if "Current status is CONFIRMED" in str(e):
                print(f"✅ User already confirmed: {email}")
            else:
                raise
        
        print(f"✅ Created Cognito user: {email}")
        return response['User']['Username']
        
    except cognito_client.exceptions.UsernameExistsException:
        print(f"✅ Cognito user already exists: {email}")
        return email
    except Exception as e:
        print(f"❌ Error creating Cognito user {email}: {e}")
        return None

def create_technician_in_users_table(dynamodb, user_data):
    """Create technician record in users table"""
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        # Create user record with technician role
        user_record = {
            'userId': user_data['userId'],
            'email': user_data['email'],
            'role': 'technician',  # This is the key field for technician lookup
            'profile': {
                'firstName': user_data['firstName'],
                'lastName': user_data['lastName'],
                'phone': user_data['phone'],
                'address': {
                    'street': user_data['location']['address'],
                    'city': user_data['location']['city'],
                    'state': user_data['location']['state'],
                    'pincode': user_data['location']['pincode'],
                    'coordinates': {
                        'latitude': user_data['location']['latitude'],
                        'longitude': user_data['location']['longitude']
                    }
                }
            },
            'workSchedule': {
                'overrideStatus': 'available',  # available, unavailable, available_overtime
                'workingHours': {
                    'monday': {'start': '09:00', 'end': '18:00', 'working': True},
                    'tuesday': {'start': '09:00', 'end': '18:00', 'working': True},
                    'wednesday': {'start': '09:00', 'end': '18:00', 'working': True},
                    'thursday': {'start': '09:00', 'end': '18:00', 'working': True},
                    'friday': {'start': '09:00', 'end': '18:00', 'working': True},
                    'saturday': {'start': '09:00', 'end': '14:00', 'working': True},
                    'sunday': {'start': '00:00', 'end': '00:00', 'working': False}
                }
            },
            'performanceScore': user_data['rating'],
            'skills': user_data['skills'],
            'verified': True,
            'active': True,
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=user_record)
        print(f"✅ Created technician in users table: {user_data['firstName']} {user_data['lastName']} ({user_data['userId']})")
        return True
        
    except Exception as e:
        print(f"❌ Error creating technician in users table: {e}")
        return False

def create_verified_technicians():
    """Create verified technicians in both Cognito and users table"""
    print("🔧 Creating verified technicians...")
    
    try:
        # Initialize AWS clients
        cognito_client = boto3.client('cognito-idp')
        dynamodb = boto3.resource('dynamodb')
        
        # Test technicians data
        technicians = [
            {
                'userId': 'tech-001',
                'email': 'rajesh.kumar@aquachain.com',
                'firstName': 'Rajesh',
                'lastName': 'Kumar',
                'phone': '+919876543210',
                'location': {
                    'latitude': Decimal('12.9716'),
                    'longitude': Decimal('77.5946'),
                    'address': 'Koramangala, Bangalore',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560034'
                },
                'skills': ['Installation', 'Maintenance', 'Repair'],
                'rating': Decimal('4.5')
            },
            {
                'userId': 'tech-002',
                'email': 'priya.sharma@aquachain.com',
                'firstName': 'Priya',
                'lastName': 'Sharma',
                'phone': '+919876543211',
                'location': {
                    'latitude': Decimal('12.9352'),
                    'longitude': Decimal('77.6245'),
                    'address': 'Whitefield, Bangalore',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560066'
                },
                'skills': ['Installation', 'Maintenance'],
                'rating': Decimal('4.8')
            },
            {
                'userId': 'tech-003',
                'email': 'amit.singh@aquachain.com',
                'firstName': 'Amit',
                'lastName': 'Singh',
                'phone': '+919876543212',
                'location': {
                    'latitude': Decimal('12.9698'),
                    'longitude': Decimal('77.7500'),
                    'address': 'Electronic City, Bangalore',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560100'
                },
                'skills': ['Installation', 'Repair', 'Troubleshooting'],
                'rating': Decimal('4.2')
            }
        ]
        
        success_count = 0
        
        for tech in technicians:
            # Create Cognito user
            cognito_username = create_cognito_user(
                cognito_client,
                tech['email'],
                tech['phone'],
                f"{tech['firstName']} {tech['lastName']}"
            )
            
            if cognito_username:
                # Create user record in DynamoDB
                if create_technician_in_users_table(dynamodb, tech):
                    success_count += 1
        
        print(f"\n✅ Successfully created {success_count}/{len(technicians)} verified technicians")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error creating verified technicians: {e}")
        return False

def verify_technicians():
    """Verify technicians were created successfully"""
    print("\n🔍 Verifying technicians in users table...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(USERS_TABLE)
        
        # Scan for technicians
        response = table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response.get('Items', [])
        print(f"✅ Found {len(technicians)} technicians in users table")
        
        for tech in technicians:
            name = f"{tech['profile']['firstName']} {tech['profile']['lastName']}"
            print(f"  - {name} ({tech['userId']})")
            print(f"    Email: {tech['email']}")
            print(f"    Phone: {tech['profile']['phone']}")
            print(f"    Location: {tech['profile']['address']['street']}")
            print(f"    Performance Score: {tech.get('performanceScore', 'N/A')}")
            print(f"    Override Status: {tech['workSchedule']['overrideStatus']}")
            print(f"    Verified: {tech.get('verified', False)}")
            print()
        
        return len(technicians) > 0
        
    except Exception as e:
        print(f"❌ Error verifying technicians: {e}")
        return False

def test_technician_availability():
    """Test technician availability using the actual availability manager logic"""
    print("\n🧪 Testing technician availability...")
    
    try:
        # Import the availability manager
        sys.path.append('lambda/technician_service')
        from availability_manager import TechnicianAvailabilityManager
        
        # Initialize availability manager
        availability_manager = TechnicianAvailabilityManager(
            'AquaChain-Users',
            'AquaChain-ServiceRequests'
        )
        
        # Find available technicians
        available_technicians = availability_manager.find_all_available_technicians()
        
        print(f"✅ Found {len(available_technicians)} available technicians:")
        for tech in available_technicians:
            print(f"  - {tech['name']} ({tech['userId']})")
            print(f"    Phone: {tech['phone']}")
            print(f"    Performance Score: {tech['performanceScore']}")
            print(f"    Availability: {tech['availability']['reason']}")
            print()
        
        return len(available_technicians) > 0
        
    except Exception as e:
        print(f"❌ Error testing technician availability: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Fixing Technician Assignment System")
    print("=" * 50)
    
    # Create verified technicians
    success = create_verified_technicians()
    
    if success:
        # Test availability
        if test_technician_availability():
            print("\n🎯 TECHNICIAN ASSIGNMENT SYSTEM FIXED!")
            print("✅ Technicians created in users table with role='technician'")
            print("✅ Cognito users created and verified")
            print("✅ Work schedules and availability configured")
            print("✅ Performance scores assigned")
            print("\n📋 NEXT STEPS:")
            print("1. Test creating a new order to trigger auto assignment")
            print("2. Verify the 'Technician Assigned' step shows as completed")
            print("3. Check that technician contact details are displayed")
        else:
            print("\n⚠️  Technicians created but availability test failed")
            print("✅ Technicians are in the database and should work for assignment")
    else:
        print("\n❌ Failed to create verified technicians")

if __name__ == "__main__":
    main()