#!/usr/bin/env python3
"""
Script to manually update phone number for a user in DynamoDB
Usage: python scripts/update_user_phone.py
"""
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Configuration
REGION = 'ap-south-1'
TABLE_NAME = 'AquaChain-Users'
USER_EMAIL = 'karthikkpradeep123@gmail.com'  # Email for Karthik K Pradeep
PHONE_NUMBER = '+918547613649'  # Replace with actual phone number

def find_user_by_email(table, email):
    """Find user by email using scan"""
    try:
        response = table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email},
            Limit=1
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None

def update_user_phone(table, user_id, phone):
    """Update user's phone number"""
    try:
        response = table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET profile.phone = :phone, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':phone': phone,
                ':updatedAt': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return None

def main():
    """Main function to update user phone"""
    print("=" * 60)
    print("AquaChain User Phone Update Script")
    print("=" * 60)
    print()
    
    # Initialize DynamoDB
    print(f"📡 Connecting to DynamoDB in region: {REGION}")
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    print(f"✅ Connected to table: {TABLE_NAME}")
    print()
    
    # Find user
    print(f"🔍 Searching for user: {USER_EMAIL}")
    user = find_user_by_email(table, USER_EMAIL)
    
    if not user:
        print(f"❌ User not found with email: {USER_EMAIL}")
        print()
        print("💡 Tip: Make sure the email is correct and the user exists in DynamoDB")
        return
    
    print(f"✅ User found!")
    print(f"   User ID: {user['userId']}")
    print(f"   Name: {user.get('profile', {}).get('firstName', '')} {user.get('profile', {}).get('lastName', '')}")
    print(f"   Current Phone: {user.get('profile', {}).get('phone', 'Not set')}")
    print()
    
    # Confirm update
    print(f"📱 New phone number: {PHONE_NUMBER}")
    confirm = input("⚠️  Do you want to update this phone number? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Update cancelled")
        return
    
    print()
    print("🔄 Updating phone number...")
    
    # Update phone
    updated_user = update_user_phone(table, user['userId'], PHONE_NUMBER)
    
    if updated_user:
        print("✅ Phone number updated successfully!")
        print()
        print("Updated user details:")
        print(f"   User ID: {updated_user['userId']}")
        print(f"   Email: {updated_user['email']}")
        print(f"   Name: {updated_user.get('profile', {}).get('firstName', '')} {updated_user.get('profile', {}).get('lastName', '')}")
        print(f"   Phone: {updated_user.get('profile', {}).get('phone', 'Not set')}")
        print(f"   Updated At: {updated_user.get('updatedAt', 'N/A')}")
        print()
        print("✅ Done! The user can now place orders.")
    else:
        print("❌ Failed to update phone number")
        print("💡 Check the error message above for details")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
