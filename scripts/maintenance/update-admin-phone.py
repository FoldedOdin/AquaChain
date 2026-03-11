#!/usr/bin/env python3
"""
Update admin user phone number in DynamoDB
"""

import boto3
from datetime import datetime

# Configuration
REGION = 'ap-south-1'
TABLE_NAME = 'AquaChain-Users'
ADMIN_USER_ID = '81236d7a-4081-7041-50cb-2f80214e3109'
ADMIN_PHONE = '7012187566'  # From the profile screenshot

def main():
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    
    # Get current record
    print(f"Checking DynamoDB record for user: {ADMIN_USER_ID}")
    response = table.get_item(Key={'userId': ADMIN_USER_ID})
    
    if 'Item' in response:
        item = response['Item']
        print(f"\nCurrent record found:")
        print(f"  - firstName: {item.get('firstName', 'N/A')}")
        print(f"  - lastName: {item.get('lastName', 'N/A')}")
        print(f"  - phone: {item.get('phone', 'N/A')}")
        print(f"  - profile: {item.get('profile', 'N/A')}")
        
        # Update with phone number
        print(f"\nUpdating phone number to: {ADMIN_PHONE}")
        table.update_item(
            Key={'userId': ADMIN_USER_ID},
            UpdateExpression='SET phone = :phone, updatedAt = :updated_at',
            ExpressionAttributeValues={
                ':phone': ADMIN_PHONE,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        print("✅ Phone number updated successfully!")
        
    else:
        print(f"\n❌ No DynamoDB record found for user: {ADMIN_USER_ID}")
        print("This user might only exist in Cognito.")
        print("\nCreating DynamoDB record...")
        
        # Create a basic record
        table.put_item(Item={
            'userId': ADMIN_USER_ID,
            'email': 'contact.aquachain@gmail.com',
            'role': 'administrator',
            'firstName': 'Akash',
            'lastName': 'Vinod',
            'phone': ADMIN_PHONE,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        })
        print("✅ DynamoDB record created successfully!")
    
    # Verify the update
    print("\nVerifying update...")
    response = table.get_item(Key={'userId': ADMIN_USER_ID})
    if 'Item' in response:
        item = response['Item']
        print(f"  - phone: {item.get('phone', 'N/A')}")
        print("\n✅ Verification complete!")
    else:
        print("\n❌ Verification failed - record not found")

if __name__ == '__main__':
    main()
