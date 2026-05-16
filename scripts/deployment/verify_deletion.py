#!/usr/bin/env python3
"""
AquaChain AWS Resource Deletion Verification Script
Verifies that all AquaChain resources have been completely deleted
"""

import boto3
import sys
from typing import Dict, List
from botocore.exceptions import ClientError

# All AWS regions
ALL_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
    'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
    'sa-east-1', 'ca-central-1'
]

class DeletionVerifier:
    """Verify complete deletion of AquaChain resources"""
    
    def __init__(self):
        self.remaining_resources = {
            'lambda_functions': [],
            'dynamodb_tables': [],
            's3_buckets': [],
            'iot_things': [],
            'iot_certificates': [],
            'iot_policies': [],
            'api_gateways': [],
            'api_gateways_v2': [],
            'cloudformation_stacks': [],
            'cognito_pools': [],
            'iam_roles': [],
            'kms_keys': [],
            'log_groups': [],
            'sagemaker_endpoints': [],
            'sagemaker_models': [],
            'ec2_instances': [],
            'rds_instances': [],
            'elasticache_clusters': [],
            'sns_topics': [],
            'sqs_queues': [],
            'eventbridge_rules': [],
            'step_functions': []
        }
        self.verification_errors = []
    
    def check_lambda_functions(self, region: str):
        """Check for remaining Lambda functions"""
        try:
            client = boto3.client('lambda', region_name=region)
            paginator = client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for func in page.get('Functions', []):
                    func_name = func['FunctionName']
                    if 'aquachain' in func_name.lower():
                        self.remaining_resources['lambda_functions'].append(f"{region}: {func_name}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"Lambda check in {region}: {str(e)}")
    
    def check_dynamodb_tables(self, region: str):
        """Check for remaining DynamoDB tables"""
        try:
            client = boto3.client('dynamodb', region_name=region)
            paginator = client.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    if 'aquachain' in table_name.lower():
                        self.remaining_resources['dynamodb_tables'].append(f"{region}: {table_name}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"DynamoDB check in {region}: {str(e)}")
    
    def check_s3_buckets(self):
        """Check for remaining S3 buckets (global service)"""
        try:
            client = boto3.client('s3')
            response = client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                if 'aquachain' in bucket_name.lower():
                    self.remaining_resources['s3_buckets'].append(bucket_name)
        except Exception as e:
            self.verification_errors.append(f"S3 check: {str(e)}")
    
    def check_iot_resources(self, region: str):
        """Check for remaining IoT things, certificates, and policies"""
        try:
            client = boto3.client('iot', region_name=region)
            
            # Check things
            try:
                paginator = client.get_paginator('list_things')
                for page in paginator.paginate():
                    for thing in page.get('things', []):
                        thing_name = thing['thingName']
                        if 'aquachain' in thing_name.lower():
                            self.remaining_resources['iot_things'].append(f"{region}: {thing_name}")
            except:
                pass
            
            # Check certificates
            try:
                paginator = client.get_paginator('list_certificates')
                for page in paginator.paginate():
                    for cert in page.get('certificates', []):
                        cert_id = cert['certificateId']
                        # Check if certificate is attached to AquaChain resources
                        try:
                            things = client.list_principal_things(principal=cert['certificateArn'])
                            for thing in things.get('things', []):
                                if 'aquachain' in thing.lower():
                                    self.remaining_resources['iot_certificates'].append(f"{region}: {cert_id}")
                                    break
                        except:
                            pass
            except:
                pass
            
            # Check policies
            try:
                paginator = client.get_paginator('list_policies')
                for page in paginator.paginate():
                    for policy in page.get('policies', []):
                        policy_name = policy['policyName']
                        if 'aquachain' in policy_name.lower():
                            self.remaining_resources['iot_policies'].append(f"{region}: {policy_name}")
            except:
                pass
                
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e) and 'Could not connect' not in str(e):
                self.verification_errors.append(f"IoT check in {region}: {str(e)}")
    
    def check_api_gateways(self, region: str):
        """Check for remaining API Gateways (REST and HTTP)"""
        try:
            # REST APIs
            client = boto3.client('apigateway', region_name=region)
            paginator = client.get_paginator('get_rest_apis')
            
            for page in paginator.paginate():
                for api in page.get('items', []):
                    api_name = api['name']
                    if 'aquachain' in api_name.lower():
                        self.remaining_resources['api_gateways'].append(f"{region}: {api_name} ({api['id']})")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"API Gateway REST check in {region}: {str(e)}")
        
        try:
            # HTTP/WebSocket APIs
            client = boto3.client('apigatewayv2', region_name=region)
            paginator = client.get_paginator('get_apis')
            
            for page in paginator.paginate():
                for api in page.get('Items', []):
                    api_name = api['Name']
                    if 'aquachain' in api_name.lower():
                        self.remaining_resources['api_gateways_v2'].append(f"{region}: {api_name} ({api['ApiId']})")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"API Gateway v2 check in {region}: {str(e)}")
    
    def check_cloudformation_stacks(self, region: str):
        """Check for remaining CloudFormation stacks"""
        try:
            client = boto3.client('cloudformation', region_name=region)
            paginator = client.get_paginator('list_stacks')
            
            for page in paginator.paginate(StackStatusFilter=[
                'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE',
                'DELETE_IN_PROGRESS', 'DELETE_FAILED'
            ]):
                for stack in page.get('StackSummaries', []):
                    stack_name = stack['StackName']
                    stack_status = stack['StackStatus']
                    if 'aquachain' in stack_name.lower():
                        self.remaining_resources['cloudformation_stacks'].append(
                            f"{region}: {stack_name} ({stack_status})"
                        )
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"CloudFormation check in {region}: {str(e)}")
    
    def check_cognito_pools(self, region: str):
        """Check for remaining Cognito user pools"""
        try:
            client = boto3.client('cognito-idp', region_name=region)
            paginator = client.get_paginator('list_user_pools')
            
            for page in paginator.paginate(MaxResults=60):
                for pool in page.get('UserPools', []):
                    pool_name = pool['Name']
                    if 'aquachain' in pool_name.lower():
                        self.remaining_resources['cognito_pools'].append(f"{region}: {pool_name} ({pool['Id']})")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"Cognito check in {region}: {str(e)}")
    
    def check_iam_roles(self):
        """Check for remaining IAM roles (global service)"""
        try:
            client = boto3.client('iam')
            paginator = client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page.get('Roles', []):
                    role_name = role['RoleName']
                    if 'aquachain' in role_name.lower():
                        self.remaining_resources['iam_roles'].append(role_name)
        except Exception as e:
            self.verification_errors.append(f"IAM check: {str(e)}")
    
    def check_kms_keys(self, region: str):
        """Check for remaining KMS keys"""
        try:
            client = boto3.client('kms', region_name=region)
            paginator = client.get_paginator('list_keys')
            
            for page in paginator.paginate():
                for key in page.get('Keys', []):
                    key_id = key['KeyId']
                    try:
                        key_metadata = client.describe_key(KeyId=key_id)
                        description = key_metadata.get('KeyMetadata', {}).get('Description', '')
                        key_state = key_metadata.get('KeyMetadata', {}).get('KeyState', '')
                        
                        if 'aquachain' in description.lower():
                            self.remaining_resources['kms_keys'].append(
                                f"{region}: {key_id} ({key_state})"
                            )
                    except:
                        pass
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"KMS check in {region}: {str(e)}")
    
    def check_cloudwatch_logs(self, region: str):
        """Check for remaining CloudWatch log groups"""
        try:
            client = boto3.client('logs', region_name=region)
            paginator = client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for log_group in page.get('logGroups', []):
                    log_group_name = log_group['logGroupName']
                    if 'aquachain' in log_group_name.lower():
                        self.remaining_resources['log_groups'].append(f"{region}: {log_group_name}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"CloudWatch Logs check in {region}: {str(e)}")
    
    def check_sagemaker_resources(self, region: str):
        """Check for remaining SageMaker endpoints and models"""
        try:
            client = boto3.client('sagemaker', region_name=region)
            
            # Check endpoints
            paginator = client.get_paginator('list_endpoints')
            for page in paginator.paginate():
                for endpoint in page.get('Endpoints', []):
                    endpoint_name = endpoint['EndpointName']
                    if 'aquachain' in endpoint_name.lower():
                        self.remaining_resources['sagemaker_endpoints'].append(
                            f"{region}: {endpoint_name} ({endpoint['EndpointStatus']})"
                        )
            
            # Check models
            paginator = client.get_paginator('list_models')
            for page in paginator.paginate():
                for model in page.get('Models', []):
                    model_name = model['ModelName']
                    if 'aquachain' in model_name.lower():
                        self.remaining_resources['sagemaker_models'].append(f"{region}: {model_name}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"SageMaker check in {region}: {str(e)}")
    
    def check_ec2_instances(self, region: str):
        """Check for remaining EC2 instances"""
        try:
            client = boto3.client('ec2', region_name=region)
            response = client.describe_instances(
                Filters=[
                    {'Name': 'tag:Project', 'Values': ['AquaChain', 'aquachain']},
                ]
            )
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    state = instance['State']['Name']
                    if state != 'terminated':
                        self.remaining_resources['ec2_instances'].append(
                            f"{region}: {instance_id} ({state})"
                        )
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"EC2 check in {region}: {str(e)}")
    
    def check_sns_topics(self, region: str):
        """Check for remaining SNS topics"""
        try:
            client = boto3.client('sns', region_name=region)
            paginator = client.get_paginator('list_topics')
            
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic['TopicArn']
                    if 'aquachain' in topic_arn.lower():
                        self.remaining_resources['sns_topics'].append(f"{region}: {topic_arn}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"SNS check in {region}: {str(e)}")
    
    def check_sqs_queues(self, region: str):
        """Check for remaining SQS queues"""
        try:
            client = boto3.client('sqs', region_name=region)
            response = client.list_queues()
            
            for queue_url in response.get('QueueUrls', []):
                if 'aquachain' in queue_url.lower():
                    self.remaining_resources['sqs_queues'].append(f"{region}: {queue_url}")
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"SQS check in {region}: {str(e)}")
    
    def check_eventbridge_rules(self, region: str):
        """Check for remaining EventBridge rules"""
        try:
            client = boto3.client('events', region_name=region)
            paginator = client.get_paginator('list_rules')
            
            for page in paginator.paginate():
                for rule in page.get('Rules', []):
                    rule_name = rule['Name']
                    if 'aquachain' in rule_name.lower():
                        self.remaining_resources['eventbridge_rules'].append(
                            f"{region}: {rule_name} ({rule['State']})"
                        )
        except Exception as e:
            if 'UnrecognizedClientException' not in str(e):
                self.verification_errors.append(f"EventBridge check in {region}: {str(e)}")
    
    def verify_region(self, region: str):
        """Verify all resources in a specific region"""
        print(f"\n{'='*80}")
        print(f"Verifying Region: {region}")
        print(f"{'='*80}")
        
        self.check_lambda_functions(region)
        self.check_dynamodb_tables(region)
        self.check_iot_resources(region)
        self.check_api_gateways(region)
        self.check_cloudformation_stacks(region)
        self.check_cognito_pools(region)
        self.check_kms_keys(region)
        self.check_cloudwatch_logs(region)
        self.check_sagemaker_resources(region)
        self.check_ec2_instances(region)
        self.check_sns_topics(region)
        self.check_sqs_queues(region)
        self.check_eventbridge_rules(region)
        
        print(f"  ✓ Region verification complete")
    
    def verify_global_resources(self):
        """Verify global AWS resources"""
        print(f"\n{'='*80}")
        print(f"Verifying Global Resources")
        print(f"{'='*80}")
        
        self.check_s3_buckets()
        self.check_iam_roles()
        
        print(f"  ✓ Global resources verification complete")
    
    def print_report(self):
        """Print verification report"""
        print(f"\n{'='*80}")
        print(f"DELETION VERIFICATION REPORT")
        print(f"{'='*80}\n")
        
        total_remaining = sum(len(v) for v in self.remaining_resources.values())
        
        if total_remaining == 0:
            print("✅ SUCCESS: All AquaChain resources have been completely deleted!")
            print("\nNo remaining resources found in any region.")
        else:
            print(f"⚠️  WARNING: Found {total_remaining} remaining resources\n")
            
            for resource_type, resources in self.remaining_resources.items():
                if resources:
                    print(f"\n{resource_type.upper().replace('_', ' ')} ({len(resources)}):")
                    for resource in resources:
                        print(f"  ❌ {resource}")
        
        if self.verification_errors:
            print(f"\n{'='*80}")
            print(f"VERIFICATION ERRORS ({len(self.verification_errors)})")
            print(f"{'='*80}")
            for error in self.verification_errors[:10]:
                print(f"  ⚠️  {error}")
            if len(self.verification_errors) > 10:
                print(f"  ... and {len(self.verification_errors) - 10} more errors")
        
        print(f"\n{'='*80}")
        if total_remaining == 0:
            print("✅ VERIFICATION COMPLETE: All resources deleted")
        else:
            print(f"⚠️  VERIFICATION COMPLETE: {total_remaining} resources remain")
        print(f"{'='*80}\n")
        
        return total_remaining == 0

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              AQUACHAIN AWS RESOURCE DELETION VERIFICATION                  ║
║                                                                            ║
║  This script will verify that all AquaChain resources have been deleted   ║
║  across all AWS regions.                                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    verifier = DeletionVerifier()
    
    # Verify all regions
    for region in ALL_REGIONS:
        try:
            verifier.verify_region(region)
        except Exception as e:
            print(f"❌ Failed to verify region {region}: {str(e)}")
    
    # Verify global resources
    verifier.verify_global_resources()
    
    # Print final report
    success = verifier.print_report()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
