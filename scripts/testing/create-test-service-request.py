#!/usr/bin/env python3
"""
Create test service request for Technician Dashboard testing.

Usage:
    python create-test-service-request.py --technician-id <COGNITO_SUB> --environment dev
"""

import boto3
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

def create_test_service_request(technician_id: str, environment: str = 'dev'):
    """Create a test service request in DynamoDB."""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table_name = f'aquachain-service-requests' if environment == 'dev' else f'aquachain-service-requests-{environment}'
    table = dynamodb.Table(table_name)
    
    request_id = f'SR-TEST-{uuid.uuid4().hex[:8].upper()}'
    now = datetime.utcnow().isoformat() + 'Z'
    scheduled = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
    
    item = {
        'requestId': request_id,
        'userId': 'test-consumer-001',
        'deviceId': 'ESP32-TEST001',
        'technicianId': technician_id,
        'status': 'assigned',
        'priority': 'normal',
        'description': 'Device calibration required - Test service request',
        'location': {
            'latitude': Decimal('12.9716'),
            'longitude': Decimal('77.5946'),
            'address': 'Bangalore, Karnataka, India'
        },
        'createdAt': now,
        'updatedAt': now,
        'scheduledDate': scheduled,
        'statusHistory': [
            {
                'status': 'pending',
                'timestamp': now,
                'note': 'Service request created'
            },
            {
                'status': 'assigned',
                'timestamp': now,
                'technicianId': technician_id,
                'note': 'Assigned to technician'
            }
        ],
        'estimatedDuration': Decimal('60'),  # minutes
        'requiredParts': ['pH Sensor', 'Calibration Solution']
    }
    
    try:
        table.put_item(Item=item)
        print(f"✅ Test service request created successfully!")
        print(f"\nRequest ID: {request_id}")
        print(f"Technician ID: {technician_id}")
        print(f"Status: {item['status']}")
        print(f"Scheduled: {scheduled}")
        print(f"\nThe technician can now see this task in their dashboard.")
        return request_id
    except Exception as e:
        print(f"❌ Error creating service request: {str(e)}")
        return None

def get_technician_cognito_sub(email: str, user_pool_id: str):
    """Get Cognito sub ID for a technician by email."""
    
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    
    try:
        response = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=email
        )
        
        for attr in response['UserAttributes']:
            if attr['Name'] == 'sub':
                return attr['Value']
        
        print(f"❌ Could not find 'sub' attribute for user {email}")
        return None
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Create test service request for Technician Dashboard')
    parser.add_argument('--technician-id', required=True, help='Cognito sub ID of the technician')
    parser.add_argument('--environment', default='dev', choices=['dev', 'staging', 'prod'], help='Environment')
    parser.add_argument('--count', type=int, default=1, help='Number of test requests to create')
    
    args = parser.parse_args()
    
    print(f"Creating {args.count} test service request(s) for technician: {args.technician_id}")
    print(f"Environment: {args.environment}")
    print()
    
    created_ids = []
    for i in range(args.count):
        request_id = create_test_service_request(args.technician_id, args.environment)
        if request_id:
            created_ids.append(request_id)
        if i < args.count - 1:
            print()
    
    if created_ids:
        print(f"\n✅ Successfully created {len(created_ids)} test service request(s)")
        print("\nNext steps:")
        print("1. Log in as the technician user")
        print("2. Navigate to Technician Dashboard")
        print("3. You should see the test service request(s)")
        print("4. Test accepting, updating status, and completing the task")
    else:
        print("\n❌ Failed to create test service requests")

if __name__ == '__main__':
    main()
