#!/usr/bin/env python3
"""
Test script to verify email verification is working
Run this after deploying Cognito User Pool
"""

import boto3
import time
import sys
import os

def test_email_verification():
    """Test that Cognito sends verification emails"""
    
    print("=" * 60)
    print("AquaChain Email Verification Test")
    print("=" * 60)
    
    # Get configuration from environment or prompt
    user_pool_id = os.environ.get('USER_POOL_ID')
    client_id = os.environ.get('USER_POOL_CLIENT_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id:
        user_pool_id = input("Enter User Pool ID: ").strip()
    if not client_id:
        client_id = input("Enter Client ID: ").strip()
    
    print(f"\n📋 Configuration:")
    print(f"   User Pool ID: {user_pool_id}")
    print(f"   Client ID: {client_id}")
    print(f"   Region: {region}")
    
    # Initialize Cognito client
    try:
        cognito = boto3.client('cognito-idp', region_name=region)
        print("\n✅ Connected to AWS Cognito")
    except Exception as e:
        print(f"\n❌ Failed to connect to AWS: {e}")
        return False
    
    # Get test email
    test_email = input("\n📧 Enter your email address for testing: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    # Generate unique username to avoid conflicts
    username = f"{test_email.split('@')[0]}+test{int(time.time())}"
    test_password = "TestPass123!"
    
    print(f"\n🔄 Creating test user...")
    print(f"   Email: {test_email}")
    print(f"   Username: {username}")
    
    try:
        # Sign up user
        response = cognito.sign_up(
            ClientId=client_id,
            Username=username,
            Password=test_password,
            UserAttributes=[
                {'Name': 'email', 'Value': test_email}
            ]
        )
        
        print("\n✅ User created successfully!")
        print(f"   User Sub: {response['UserSub']}")
        
        # Check code delivery details
        delivery = response.get('CodeDeliveryDetails', {})
        if delivery:
            print(f"\n📬 Code Delivery Details:")
            print(f"   Destination: {delivery.get('Destination', 'N/A')}")
            print(f"   Delivery Medium: {delivery.get('DeliveryMedium', 'N/A')}")
            print(f"   Attribute: {delivery.get('AttributeName', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ EMAIL VERIFICATION CODE SENT!")
        print("=" * 60)
        print("\n📧 Check your email inbox (and spam folder)")
        print("   You should receive an email with a 6-digit code")
        print("   Subject: 'Verify Your AquaChain Account'")
        print("\n⏱️  Email should arrive within 1-2 minutes")
        
        # Prompt for verification code
        print("\n" + "-" * 60)
        verify = input("\nDid you receive the verification email? (y/n): ").strip().lower()
        
        if verify == 'y':
            code = input("Enter the 6-digit verification code: ").strip()
            
            if code and len(code) == 6:
                try:
                    # Confirm signup
                    cognito.confirm_sign_up(
                        ClientId=client_id,
                        Username=username,
                        ConfirmationCode=code
                    )
                    
                    print("\n✅ EMAIL VERIFIED SUCCESSFULLY!")
                    print("   The verification system is working correctly!")
                    
                    # Clean up - delete test user
                    cleanup = input("\nDelete test user? (y/n): ").strip().lower()
                    if cleanup == 'y':
                        try:
                            cognito.admin_delete_user(
                                UserPoolId=user_pool_id,
                                Username=username
                            )
                            print("✅ Test user deleted")
                        except Exception as e:
                            print(f"⚠️  Could not delete user: {e}")
                            print(f"   You may need to delete manually: {username}")
                    
                    return True
                    
                except cognito.exceptions.CodeMismatchException:
                    print("\n❌ Invalid verification code")
                    print("   The code you entered doesn't match")
                except Exception as e:
                    print(f"\n❌ Verification failed: {e}")
            else:
                print("\n❌ Invalid code format (must be 6 digits)")
        else:
            print("\n⚠️  Email not received. Possible issues:")
            print("   1. Check spam/junk folder")
            print("   2. Wait a few more minutes")
            print("   3. Verify Cognito email configuration")
            print("   4. Check CloudWatch logs for errors")
            print(f"\n   Test user created: {username}")
            print("   You can delete it manually from Cognito console")
        
        return False
        
    except cognito.exceptions.UsernameExistsException:
        print("\n❌ User already exists")
        print("   Try with a different email or delete the existing user")
        return False
        
    except cognito.exceptions.InvalidPasswordException as e:
        print(f"\n❌ Invalid password: {e}")
        return False
        
    except cognito.exceptions.InvalidParameterException as e:
        print(f"\n❌ Invalid parameter: {e}")
        print("   Check your Cognito configuration")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def check_cognito_config():
    """Check Cognito User Pool configuration"""
    
    print("\n" + "=" * 60)
    print("Checking Cognito Configuration")
    print("=" * 60)
    
    user_pool_id = os.environ.get('USER_POOL_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id:
        user_pool_id = input("Enter User Pool ID: ").strip()
    
    try:
        cognito = boto3.client('cognito-idp', region_name=region)
        
        # Get user pool details
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        pool = response['UserPool']
        
        print(f"\n✅ User Pool Found: {pool['Name']}")
        print(f"   ID: {pool['Id']}")
        print(f"   Status: {pool['Status']}")
        
        # Check email configuration
        email_config = pool.get('EmailConfiguration', {})
        print(f"\n📧 Email Configuration:")
        print(f"   Sending Account: {email_config.get('EmailSendingAccount', 'Not set')}")
        print(f"   Reply-To: {email_config.get('ReplyToEmailAddress', 'Not set')}")
        
        # Check auto-verified attributes
        auto_verified = pool.get('AutoVerifiedAttributes', [])
        print(f"\n✅ Auto-Verified Attributes: {', '.join(auto_verified) if auto_verified else 'None'}")
        
        if 'email' not in auto_verified:
            print("   ⚠️  WARNING: Email is not in auto-verified attributes!")
            print("   Email verification may not work correctly")
        
        # Check verification message template
        verification = pool.get('VerificationMessageTemplate', {})
        if verification:
            print(f"\n📝 Verification Template:")
            print(f"   Email Subject: {verification.get('EmailSubject', 'Not set')}")
            print(f"   Default Option: {verification.get('DefaultEmailOption', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking configuration: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 AquaChain Email Verification Test Script")
    print("=" * 60)
    
    # Check if we should verify config first
    if len(sys.argv) > 1 and sys.argv[1] == '--check-config':
        check_cognito_config()
    else:
        print("\nThis script will:")
        print("1. Create a test user in Cognito")
        print("2. Trigger verification email sending")
        print("3. Verify you receive the email")
        print("4. Test code verification")
        print("5. Clean up test user")
        
        print("\n⚠️  Make sure you have:")
        print("   - Deployed Cognito User Pool")
        print("   - AWS credentials configured")
        print("   - USER_POOL_ID and USER_POOL_CLIENT_ID set")
        
        proceed = input("\nProceed with test? (y/n): ").strip().lower()
        
        if proceed == 'y':
            success = test_email_verification()
            
            if success:
                print("\n" + "=" * 60)
                print("✅ ALL TESTS PASSED!")
                print("=" * 60)
                print("\nEmail verification is working correctly!")
                print("Users will receive verification codes when they sign up.")
                sys.exit(0)
            else:
                print("\n" + "=" * 60)
                print("⚠️  TEST INCOMPLETE")
                print("=" * 60)
                print("\nPlease check the issues above and try again.")
                sys.exit(1)
        else:
            print("\nTest cancelled.")
            sys.exit(0)
