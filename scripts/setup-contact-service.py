#!/usr/bin/env python3
"""
Setup script for Contact Form Service
Creates DynamoDB table, Lambda function, and API Gateway endpoint
"""

import boto3
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from infrastructure.dynamodb.contact_table import ContactTableManager


def setup_contact_service():
    """
    Complete setup for contact form service
    """
    print("=" * 60)
    print("AquaChain Contact Form Service Setup")
    print("=" * 60)
    
    # Step 1: Create DynamoDB table
    print("\n[1/4] Creating DynamoDB table...")
    try:
        table_manager = ContactTableManager()
        table_manager.create_contact_submissions_table()
        print("✓ DynamoDB table created successfully")
    except Exception as e:
        print(f"✗ Error creating DynamoDB table: {e}")
        return False
    
    # Step 2: Verify SES email addresses
    print("\n[2/4] Verifying SES email configuration...")
    try:
        verify_ses_emails()
        print("✓ SES email configuration verified")
    except Exception as e:
        print(f"⚠ Warning: SES email verification needed: {e}")
        print("  Please verify email addresses in AWS SES console")
    
    # Step 3: Create Lambda function
    print("\n[3/4] Lambda function setup...")
    print("  Note: Lambda function should be deployed via CDK/CloudFormation")
    print("  Location: lambda/contact_service/handler.py")
    print("  Required environment variables:")
    print("    - CONTACT_TABLE_NAME: aquachain-contact-submissions")
    print("    - ADMIN_EMAIL: admin@aquachain.io")
    print("    - FROM_EMAIL: noreply@aquachain.io")
    
    # Step 4: API Gateway setup
    print("\n[4/4] API Gateway setup...")
    print("  Note: API Gateway endpoint should be configured via CDK/CloudFormation")
    print("  Required endpoint: POST /contact")
    print("  CORS should be enabled for frontend domain")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Verify email addresses in AWS SES console")
    print("2. Deploy Lambda function using CDK/CloudFormation")
    print("3. Configure API Gateway endpoint")
    print("4. Update frontend .env with API_URL")
    print("\nFrontend Configuration:")
    print("  Add to frontend/.env:")
    print("  REACT_APP_API_URL=https://your-api-gateway-url")
    
    return True


def verify_ses_emails():
    """
    Verify SES email addresses for sending emails
    """
    ses_client = boto3.client('ses', region_name='us-east-1')
    
    emails_to_verify = [
        'noreply@aquachain.io',
        'admin@aquachain.io'
    ]
    
    for email in emails_to_verify:
        try:
            # Check if email is already verified
            response = ses_client.get_identity_verification_attributes(
                Identities=[email]
            )
            
            status = response['VerificationAttributes'].get(email, {}).get('VerificationStatus')
            
            if status == 'Success':
                print(f"  ✓ {email} is verified")
            else:
                # Request verification
                ses_client.verify_email_identity(EmailAddress=email)
                print(f"  → Verification email sent to {email}")
                
        except Exception as e:
            print(f"  ⚠ Could not verify {email}: {e}")


def check_prerequisites():
    """
    Check if AWS credentials are configured
    """
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"AWS User: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"Error: AWS credentials not configured: {e}")
        return False


if __name__ == '__main__':
    print("\nChecking AWS credentials...")
    if not check_prerequisites():
        print("\nPlease configure AWS credentials and try again.")
        sys.exit(1)
    
    print("\nStarting setup...\n")
    success = setup_contact_service()
    
    sys.exit(0 if success else 1)
