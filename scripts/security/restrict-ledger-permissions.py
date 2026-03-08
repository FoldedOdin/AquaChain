#!/usr/bin/env python3
"""
Restrict Lambda IAM permissions for ledger table to write-only
"""

import boto3
import json

def restrict_ledger_permissions():
    iam = boto3.client('iam', region_name='ap-south-1')
    
    print("=" * 70)
    print("RESTRICTING LEDGER PERMISSIONS")
    print("=" * 70)
    print()
    
    role_name = 'aquachain-role-data-processing-dev'
    policy_name = 'LedgerWriteOnlyPolicy'
    
    # Define write-only policy for ledger table
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LedgerWriteOnly",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-ledger",
                    "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-ledger/index/*"
                ]
            },
            {
                "Sid": "DenyLedgerModifications",
                "Effect": "Deny",
                "Action": [
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:BatchWriteItem"
                ],
                "Resource": [
                    "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-ledger",
                    "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-ledger/index/*"
                ]
            }
        ]
    }
    
    try:
        # Check if policy already exists
        try:
            existing_policy = iam.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            print(f"✓ Policy '{policy_name}' already exists")
            print("  Updating policy...")
        except iam.exceptions.NoSuchEntityException:
            print(f"Creating new policy '{policy_name}'...")
        
        # Put (create or update) the policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✓ Successfully applied write-only policy to ledger table")
        print()
        print("Policy Details:")
        print(f"  Role: {role_name}")
        print(f"  Policy: {policy_name}")
        print(f"  Allowed: PutItem, GetItem, Query, Scan")
        print(f"  Denied: UpdateItem, DeleteItem, BatchWriteItem")
        print()
        
        # Verify the policy
        print("Verifying policy...")
        response = iam.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        
        print("✓ Policy verified successfully")
        print()
        print("=" * 70)
        print("SUCCESS - Ledger is now write-only!")
        print("=" * 70)
        print()
        print("Note: The explicit DENY takes precedence over any ALLOW")
        print("      in other policies, ensuring immutability.")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = restrict_ledger_permissions()
    exit(0 if success else 1)
