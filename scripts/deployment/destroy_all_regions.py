#!/usr/bin/env python3
"""
AquaChain Multi-Region AWS Resource Destruction Script
WARNING: This will permanently delete ALL AquaChain resources across ALL AWS regions
"""

import boto3
import sys
import time
from typing import List, Dict
from botocore.exceptions import ClientError

# All AWS regions
ALL_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
    'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
    'sa-east-1', 'ca-central-1',
    'af-south-1', 'ap-east-1', 'me-south-1'
]

class AWSResourceCleaner:
    """Comprehensive AWS resource cleanup across all regions"""
    
    def __init__(self):
        self.deletion_report = {
            'lambda_functions': 0,
            'dynamodb_tables': 0,
            's3_buckets': 0,
            'iot_things': 0,
            'api_gateways': 0,
            'cloudformation_stacks': 0,
            'cognito_pools': 0,
            'iam_roles': 0,
            'kms_keys': 0,
            'log_groups': 0,
            'errors': []
        }
    
    def delete_lambda_functions(self, region: str):
        """Delete all AquaChain Lambda functions in a region"""
        try:
            client = boto3.client('lambda', region_name=region)
            response = client.list_functions()
            
            for func in response.get('Functions', []):
                func_name = func['FunctionName']
                if 'AquaChain' in func_name or 'aquachain' in func_name.lower():
                    print(f"  [Lambda] Deleting: {func_name}")
                    try:
                        client.delete_function(FunctionName=func_name)
                        self.deletion_report['lambda_functions'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"Lambda {func_name}: {str(e)}")
        except Exception as e:
            print(f"  [Lambda] Error in {region}: {str(e)}")
    
    def delete_dynamodb_tables(self, region: str):
        """Delete all AquaChain DynamoDB tables in a region"""
        try:
            client = boto3.client('dynamodb', region_name=region)
            response = client.list_tables()
            
            for table_name in response.get('TableNames', []):
                if 'AquaChain' in table_name or 'aquachain' in table_name.lower():
                    print(f"  [DynamoDB] Deleting: {table_name}")
                    try:
                        client.delete_table(TableName=table_name)
                        self.deletion_report['dynamodb_tables'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"DynamoDB {table_name}: {str(e)}")
        except Exception as e:
            print(f"  [DynamoDB] Error in {region}: {str(e)}")
    
    def delete_s3_buckets(self, region: str):
        """Delete all AquaChain S3 buckets (force delete with versioning)"""
        try:
            s3 = boto3.resource('s3', region_name=region)
            client = boto3.client('s3', region_name=region)
            
            response = client.list_buckets()
            for bucket_info in response.get('Buckets', []):
                bucket_name = bucket_info['Name']
                if 'aquachain' in bucket_name.lower():
                    print(f"  [S3] Deleting bucket: {bucket_name}")
                    try:
                        bucket = s3.Bucket(bucket_name)
                        
                        # Delete all versions and delete markers
                        bucket.object_versions.all().delete()
                        
                        # Delete the bucket
                        bucket.delete()
                        self.deletion_report['s3_buckets'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"S3 {bucket_name}: {str(e)}")
        except Exception as e:
            print(f"  [S3] Error in {region}: {str(e)}")
    
    def delete_iot_things(self, region: str):
        """Delete all AquaChain IoT things in a region"""
        try:
            client = boto3.client('iot', region_name=region)
            response = client.list_things()
            
            for thing in response.get('things', []):
                thing_name = thing['thingName']
                if 'AquaChain' in thing_name or 'aquachain' in thing_name.lower():
                    print(f"  [IoT] Deleting thing: {thing_name}")
                    try:
                        # Detach principals first
                        principals = client.list_thing_principals(thingName=thing_name)
                        for principal in principals.get('principals', []):
                            client.detach_thing_principal(thingName=thing_name, principal=principal)
                        
                        # Delete the thing
                        client.delete_thing(thingName=thing_name)
                        self.deletion_report['iot_things'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"IoT {thing_name}: {str(e)}")
        except Exception as e:
            print(f"  [IoT] Error in {region}: {str(e)}")
    
    def delete_api_gateways(self, region: str):
        """Delete all AquaChain API Gateways in a region"""
        try:
            client = boto3.client('apigateway', region_name=region)
            response = client.get_rest_apis()
            
            for api in response.get('items', []):
                api_name = api['name']
                api_id = api['id']
                if 'AquaChain' in api_name or 'aquachain' in api_name.lower():
                    print(f"  [API Gateway] Deleting: {api_name} ({api_id})")
                    try:
                        client.delete_rest_api(restApiId=api_id)
                        self.deletion_report['api_gateways'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"API Gateway {api_name}: {str(e)}")
        except Exception as e:
            print(f"  [API Gateway] Error in {region}: {str(e)}")
    
    def delete_cloudformation_stacks(self, region: str):
        """Delete all AquaChain CloudFormation stacks in a region"""
        try:
            client = boto3.client('cloudformation', region_name=region)
            response = client.list_stacks(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
            )
            
            for stack in response.get('StackSummaries', []):
                stack_name = stack['StackName']
                if 'AquaChain' in stack_name or 'aquachain' in stack_name.lower():
                    print(f"  [CloudFormation] Deleting: {stack_name}")
                    try:
                        client.delete_stack(StackName=stack_name)
                        self.deletion_report['cloudformation_stacks'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"CloudFormation {stack_name}: {str(e)}")
        except Exception as e:
            print(f"  [CloudFormation] Error in {region}: {str(e)}")
    
    def delete_cognito_pools(self, region: str):
        """Delete all AquaChain Cognito user pools in a region"""
        try:
            client = boto3.client('cognito-idp', region_name=region)
            response = client.list_user_pools(MaxResults=60)
            
            for pool in response.get('UserPools', []):
                pool_name = pool['Name']
                pool_id = pool['Id']
                if 'AquaChain' in pool_name or 'aquachain' in pool_name.lower():
                    print(f"  [Cognito] Deleting: {pool_name} ({pool_id})")
                    try:
                        client.delete_user_pool(UserPoolId=pool_id)
                        self.deletion_report['cognito_pools'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"Cognito {pool_name}: {str(e)}")
        except Exception as e:
            print(f"  [Cognito] Error in {region}: {str(e)}")
    
    def delete_cloudwatch_logs(self, region: str):
        """Delete all AquaChain CloudWatch log groups in a region"""
        try:
            client = boto3.client('logs', region_name=region)
            paginator = client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for log_group in page.get('logGroups', []):
                    log_group_name = log_group['logGroupName']
                    if 'aquachain' in log_group_name.lower() or 'AquaChain' in log_group_name:
                        print(f"  [CloudWatch Logs] Deleting: {log_group_name}")
                        try:
                            client.delete_log_group(logGroupName=log_group_name)
                            self.deletion_report['log_groups'] += 1
                        except ClientError as e:
                            self.deletion_report['errors'].append(f"Log Group {log_group_name}: {str(e)}")
        except Exception as e:
            print(f"  [CloudWatch Logs] Error in {region}: {str(e)}")
    
    def delete_iam_roles(self):
        """Delete all AquaChain IAM roles (global service)"""
        try:
            client = boto3.client('iam')
            response = client.list_roles()
            
            for role in response.get('Roles', []):
                role_name = role['RoleName']
                if 'AquaChain' in role_name or 'aquachain' in role_name.lower():
                    print(f"  [IAM] Deleting role: {role_name}")
                    try:
                        # Detach managed policies
                        attached_policies = client.list_attached_role_policies(RoleName=role_name)
                        for policy in attached_policies.get('AttachedPolicies', []):
                            client.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
                        
                        # Delete inline policies
                        inline_policies = client.list_role_policies(RoleName=role_name)
                        for policy_name in inline_policies.get('PolicyNames', []):
                            client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                        
                        # Delete the role
                        client.delete_role(RoleName=role_name)
                        self.deletion_report['iam_roles'] += 1
                    except ClientError as e:
                        self.deletion_report['errors'].append(f"IAM Role {role_name}: {str(e)}")
        except Exception as e:
            print(f"  [IAM] Error: {str(e)}")
    
    def schedule_kms_key_deletion(self, region: str):
        """Schedule deletion of all AquaChain KMS keys in a region"""
        try:
            client = boto3.client('kms', region_name=region)
            response = client.list_keys()
            
            for key in response.get('Keys', []):
                key_id = key['KeyId']
                try:
                    key_metadata = client.describe_key(KeyId=key_id)
                    description = key_metadata.get('KeyMetadata', {}).get('Description', '')
                    
                    if 'AquaChain' in description or 'aquachain' in description.lower():
                        print(f"  [KMS] Scheduling deletion: {key_id}")
                        client.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
                        self.deletion_report['kms_keys'] += 1
                except ClientError:
                    pass  # Skip keys we can't access
        except Exception as e:
            print(f"  [KMS] Error in {region}: {str(e)}")
    
    def clean_region(self, region: str):
        """Clean all AquaChain resources in a specific region"""
        print(f"\n{'='*80}")
        print(f"Cleaning Region: {region}")
        print(f"{'='*80}")
        
        self.delete_lambda_functions(region)
        self.delete_api_gateways(region)
        self.delete_cloudformation_stacks(region)
        self.delete_dynamodb_tables(region)
        self.delete_iot_things(region)
        self.delete_cognito_pools(region)
        self.delete_cloudwatch_logs(region)
        self.schedule_kms_key_deletion(region)
        
        # S3 is global but buckets have regions
        if region == 'us-east-1':
            self.delete_s3_buckets(region)
    
    def clean_global_resources(self):
        """Clean global AWS resources (IAM, etc.)"""
        print(f"\n{'='*80}")
        print(f"Cleaning Global Resources (IAM)")
        print(f"{'='*80}")
        self.delete_iam_roles()
    
    def print_report(self):
        """Print deletion summary report"""
        print(f"\n{'='*80}")
        print(f"DELETION SUMMARY REPORT")
        print(f"{'='*80}")
        print(f"Lambda Functions:        {self.deletion_report['lambda_functions']}")
        print(f"DynamoDB Tables:         {self.deletion_report['dynamodb_tables']}")
        print(f"S3 Buckets:              {self.deletion_report['s3_buckets']}")
        print(f"IoT Things:              {self.deletion_report['iot_things']}")
        print(f"API Gateways:            {self.deletion_report['api_gateways']}")
        print(f"CloudFormation Stacks:   {self.deletion_report['cloudformation_stacks']}")
        print(f"Cognito User Pools:      {self.deletion_report['cognito_pools']}")
        print(f"IAM Roles:               {self.deletion_report['iam_roles']}")
        print(f"KMS Keys (scheduled):    {self.deletion_report['kms_keys']}")
        print(f"CloudWatch Log Groups:   {self.deletion_report['log_groups']}")
        print(f"\nTotal Errors:            {len(self.deletion_report['errors'])}")
        
        if self.deletion_report['errors']:
            print(f"\n{'='*80}")
            print(f"ERRORS ENCOUNTERED")
            print(f"{'='*80}")
            for error in self.deletion_report['errors'][:20]:  # Show first 20 errors
                print(f"  - {error}")
            if len(self.deletion_report['errors']) > 20:
                print(f"  ... and {len(self.deletion_report['errors']) - 20} more errors")

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                   AQUACHAIN AWS RESOURCE DESTRUCTION                       ║
║                                                                            ║
║  WARNING: This will PERMANENTLY DELETE all AquaChain resources            ║
║           across ALL AWS regions.                                          ║
║                                                                            ║
║  This action CANNOT be undone!                                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nConfirmation required. Type 'DELETE ALL RESOURCES' to proceed:")
    confirmation = input("> ").strip()
    
    if confirmation != "DELETE ALL RESOURCES":
        print("\n❌ Deletion cancelled. Exiting.")
        sys.exit(0)
    
    print("\n✅ Confirmation received. Starting deletion process...\n")
    time.sleep(2)
    
    cleaner = AWSResourceCleaner()
    
    # Clean all regions
    for region in ALL_REGIONS:
        try:
            cleaner.clean_region(region)
        except Exception as e:
            print(f"❌ Failed to clean region {region}: {str(e)}")
    
    # Clean global resources
    cleaner.clean_global_resources()
    
    # Print final report
    cleaner.print_report()
    
    print(f"\n{'='*80}")
    print("✅ DELETION COMPLETE")
    print(f"{'='*80}")
    print("\nNote:")
    print("  - KMS keys have a 7-day waiting period before permanent deletion")
    print("  - Some CloudFormation stacks may take 5-10 minutes to fully delete")
    print("  - Verify deletion by checking AWS Console in all regions")
    print("\n")

if __name__ == "__main__":
    main()
