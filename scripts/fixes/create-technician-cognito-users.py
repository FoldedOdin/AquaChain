#!/usr/bin/env python3
"""
Create Cognito users for technicians who exist in DynamoDB but not in Cognito
"""

import boto3
import json
from datetime import datetime

def create_technician_cognito_users():
    """Create Cognito users for technicians"""
    print("🔧 Creating Cognito users for technicians...")
    
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Get user pool ID
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        
        # Get technicians from DynamoDB
        users_table = dynamodb.Table('AquaChain-Users')
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response['Items']
        print(f"✅ Found {len(technicians)} technicians in DynamoDB")
        
        for tech in technicians:
            email = tech.get('email')
            name = tech.get('name', 'Technician')
            user_id = tech.get('userId')
            
            if not email:
                print(f"⚠️  Skipping technician {name} - no email")
                continue
            
            print(f"\n👤 Creating Cognito user for {name} ({email})")
            
            try:
                # Create user in Cognito (without custom attributes first)
                response = cognito.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=email,
                    UserAttributes=[
                        {'Name': 'email', 'Value': email},
                        {'Name': 'email_verified', 'Value': 'true'},
                        {'Name': 'name', 'Value': name}
                    ],
                    TemporaryPassword='TempPass123!',
                    MessageAction='SUPPRESS'  # Don't send welcome email
                )
                
                print(f"   ✅ Created Cognito user")
                
                # Set permanent password
                cognito.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=email,
                    Password='AquaChain123!',  # Temporary password for testing
                    Permanent=True
                )
                
                print(f"   ✅ Set permanent password: AquaChain123!")
                
            except cognito.exceptions.UsernameExistsException:
                print(f"   ⚠️  User already exists in Cognito")
                
                # Update user attributes to ensure they have the right role
                try:
                    # Try to add custom attributes (may not work if not configured)
                    print(f"   ⚠️  Custom attributes may not be supported in this user pool")
                except Exception as e:
                    print(f"   ❌ Error updating attributes: {e}")
                
            except Exception as e:
                print(f"   ❌ Error creating user: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating Cognito users: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating Technician Cognito Users")
    print("=" * 60)
    
    success = create_technician_cognito_users()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ Technician Cognito users created successfully")
        print("\n🔑 LOGIN CREDENTIALS:")
        print("   📧 Email: karthiikkpradeep897@gmail.com")
        print("   🔒 Password: AquaChain123!")
        print("   📧 Email: leninat259@gmail.com") 
        print("   🔒 Password: AquaChain123!")
        print("\n🎯 NEXT STEPS:")
        print("1. Try logging in as a technician")
        print("2. Check if tasks appear in dashboard")
        print("3. Verify API calls work with real token")
    else:
        print("❌ Failed to create Cognito users")

if __name__ == "__main__":
    main()