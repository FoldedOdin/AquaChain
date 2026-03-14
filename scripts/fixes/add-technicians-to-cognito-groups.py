#!/usr/bin/env python3
"""
Add technician users to the 'technicians' Cognito group
"""

import boto3

def add_technicians_to_groups():
    """Add technician users to the technicians group"""
    print("🔧 Adding technicians to Cognito groups...")
    
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        
        # Technician emails
        technician_emails = [
            'karthiikkpradeep897@gmail.com',
            'leninat259@gmail.com'
        ]
        
        # First, create the technicians group if it doesn't exist
        try:
            cognito.create_group(
                GroupName='technicians',
                UserPoolId=user_pool_id,
                Description='Technician users group'
            )
            print("✅ Created 'technicians' group")
        except cognito.exceptions.GroupExistsException:
            print("✅ 'technicians' group already exists")
        except Exception as e:
            print(f"❌ Error creating group: {e}")
            return False
        
        # Add each technician to the group
        for email in technician_emails:
            try:
                cognito.admin_add_user_to_group(
                    UserPoolId=user_pool_id,
                    Username=email,
                    GroupName='technicians'
                )
                print(f"✅ Added {email} to technicians group")
            except Exception as e:
                print(f"❌ Error adding {email} to group: {e}")
        
        # Verify group membership
        print("\n🔍 Verifying group memberships...")
        for email in technician_emails:
            try:
                response = cognito.admin_list_groups_for_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
                groups = [group['GroupName'] for group in response['Groups']]
                print(f"   👤 {email}: Groups = {groups}")
            except Exception as e:
                print(f"   ❌ Error checking groups for {email}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error managing Cognito groups: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Adding Technicians to Cognito Groups")
    print("=" * 60)
    
    success = add_technicians_to_groups()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ Technicians added to groups successfully")
        print("\n🎯 NEXT STEPS:")
        print("1. Try logging in as a technician:")
        print("   📧 karthiikkpradeep897@gmail.com")
        print("   🔒 Password: AquaChain123!")
        print("   📧 leninat259@gmail.com")
        print("   🔒 Password: AquaChain123!")
        print("2. Check if tasks appear in dashboard")
        print("3. Verify API calls work with real token")
    else:
        print("❌ Failed to add technicians to groups")

if __name__ == "__main__":
    main()