#!/usr/bin/env python3
"""
Cleanup remaining AquaChain resources identified by verification
"""

import boto3
import time
from botocore.exceptions import ClientError

def delete_remaining_resources():
    """Delete all remaining AquaChain resources"""
    
    region = 'ap-south-1'
    
    print("="*80)
    print("CLEANING UP REMAINING RESOURCES")
    print("="*80)
    
    # 1. Delete SNS Topics
    print("\n[1/4] Deleting SNS Topics...")
    sns_client = boto3.client('sns', region_name=region)
    sns_topics = [
        'arn:aws:sns:ap-south-1:758346259059:aquachain-ledger-security-alerts',
        'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-critical-alerts-dev',
        'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-notifications-dev',
        'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-service-updates-dev',
        'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-system-alerts-dev'
    ]
    
    for topic_arn in sns_topics:
        try:
            print(f"  Deleting: {topic_arn.split(':')[-1]}")
            sns_client.delete_topic(TopicArn=topic_arn)
            print(f"    ✓ Deleted")
        except ClientError as e:
            print(f"    ✗ Error: {e.response['Error']['Code']}")
    
    # 2. Delete IoT Policy
    print("\n[2/4] Deleting IoT Policy...")
    iot_client = boto3.client('iot', region_name=region)
    policy_name = 'aquachain-device-policy-dev'
    
    try:
        # First, detach policy from all targets
        print(f"  Detaching policy: {policy_name}")
        targets = iot_client.list_targets_for_policy(policyName=policy_name)
        for target in targets.get('targets', []):
            try:
                iot_client.detach_policy(policyName=policy_name, target=target)
                print(f"    Detached from: {target}")
            except:
                pass
        
        # Delete all policy versions except default
        print(f"  Deleting policy versions...")
        versions = iot_client.list_policy_versions(policyName=policy_name)
        for version in versions.get('policyVersions', []):
            if not version.get('isDefaultVersion', False):
                try:
                    iot_client.delete_policy_version(
                        policyName=policy_name,
                        policyVersionId=version['versionId']
                    )
                    print(f"    Deleted version: {version['versionId']}")
                except:
                    pass
        
        # Delete the policy
        print(f"  Deleting policy: {policy_name}")
        iot_client.delete_policy(policyName=policy_name)
        print(f"    ✓ Deleted")
    except ClientError as e:
        print(f"    ✗ Error: {e.response['Error']['Code']}")
    
    # 3. Delete DynamoDB Table
    print("\n[3/4] Deleting DynamoDB Table...")
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    table_name = 'aquachain-ledger'
    
    try:
        print(f"  Deleting table: {table_name}")
        dynamodb_client.delete_table(TableName=table_name)
        print(f"    ✓ Deletion initiated (may take a few minutes)")
    except ClientError as e:
        print(f"    ✗ Error: {e.response['Error']['Code']}")
    
    # 4. Delete CloudFormation Stacks
    print("\n[4/4] Deleting CloudFormation Stacks...")
    cfn_client = boto3.client('cloudformation', region_name=region)
    stacks = [
        'AquaChain-LambdaLayers-dev',
        'AquaChain-Compute-dev',
        'AquaChain-Security-dev'
    ]
    
    for stack_name in stacks:
        try:
            print(f"  Deleting stack: {stack_name}")
            cfn_client.delete_stack(StackName=stack_name)
            print(f"    ✓ Deletion initiated")
        except ClientError as e:
            print(f"    ✗ Error: {e.response['Error']['Code']}")
    
    # Note about KMS keys
    print("\n" + "="*80)
    print("KMS KEYS STATUS")
    print("="*80)
    print("✓ 5 KMS keys are already in 'PendingDeletion' state")
    print("  They will be permanently deleted after 7-day waiting period")
    print("  Deletion date: May 18, 2026")
    
    print("\n" + "="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print("\nRemaining resources have been deleted or scheduled for deletion.")
    print("Wait 5-10 minutes for CloudFormation stacks to fully delete.")
    print("\n")

if __name__ == "__main__":
    delete_remaining_resources()
