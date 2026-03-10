#!/usr/bin/env python3
"""
Fix IAM permissions for device management Lambda function
Grants DynamoDB access to AquaChain-Devices and AquaChain-Users tables
"""

import boto3
import json
import sys

def fix_permissions(environment='dev'):
    """Add DynamoDB permissions to Lambda execution role"""
    
    iam = boto3.client('iam')
    role_name = 'aquachain-lambda-execution-role'
    
    # Policy document for DynamoDB access
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:ap-south-1:*:table/AquaChain-Devices",
                    f"arn:aws:dynamodb:ap-south-1:*:table/AquaChain-Devices/index/*",
                    f"arn:aws:dynamodb:ap-south-1:*:table/AquaChain-Users",
                    f"arn:aws:dynamodb:ap-south-1:*:table/AquaChain-Users/index/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:DescribeThing",
                    "iot:ListThings"
                ],
                "Resource": "*"
            }
        ]
    }
    
    policy_name = 'AquaChainDeviceManagementPolicy'
    
    try:
        # Try to create the policy
        print(f"Creating IAM policy: {policy_name}")
        policy_response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description='Permissions for AquaChain device management Lambda'
        )
        policy_arn = policy_response['Policy']['Arn']
        print(f"✓ Policy created: {policy_arn}")
        
    except iam.exceptions.EntityAlreadyExistsException:
        # Policy already exists, get its ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
        print(f"Policy already exists: {policy_arn}")
        
        # Update the policy with new version
        try:
            print("Updating policy with new version...")
            iam.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=json.dumps(policy_document),
                SetAsDefault=True
            )
            print("✓ Policy updated")
        except Exception as e:
            print(f"Note: Could not update policy: {e}")
    
    # Attach policy to role
    try:
        print(f"Attaching policy to role: {role_name}")
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✓ Policy attached to role")
    except iam.exceptions.NoSuchEntityException:
        print(f"✗ Error: Role {role_name} does not exist")
        return False
    except Exception as e:
        if 'already attached' in str(e).lower():
            print(f"Policy already attached to role")
        else:
            print(f"Error attaching policy: {e}")
            return False
    
    print("\n✓ Permissions fixed successfully!")
    print("\nThe Lambda function now has access to:")
    print("  - DynamoDB: AquaChain-Devices (read/write)")
    print("  - DynamoDB: AquaChain-Users (read/write)")
    print("  - IoT Core: DescribeThing (read)")
    
    return True

if __name__ == '__main__':
    environment = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    
    print(f"Fixing IAM permissions for device management Lambda ({environment})")
    print("=" * 60)
    
    success = fix_permissions(environment)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Permissions update complete!")
        print("\nYou can now test the Lambda function:")
        print("  aws lambda invoke --function-name aquachain-function-device-management-dev \\")
        print("    --region ap-south-1 --payload file://test-payload.json response.json")
    else:
        print("\n✗ Failed to update permissions")
        sys.exit(1)
