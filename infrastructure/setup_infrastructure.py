"""
Main infrastructure setup script for AquaChain system
Orchestrates the creation of all AWS resources in the correct order
"""

import boto3
import json
import time
from typing import Dict, Any, Optional

from dynamodb.tables import DynamoDBTableManager
from s3.buckets import S3BucketManager
from kms.keys import KMSKeyManager
from iot.core_setup import IoTCoreManager

class AquaChainInfrastructureManager:
    def __init__(self, region_name: str = 'us-east-1', replica_account_id: str = None):
        self.region_name = region_name
        self.replica_account_id = replica_account_id
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize managers
        self.dynamodb_manager = DynamoDBTableManager(region_name)
        self.s3_manager = S3BucketManager(region_name, self.account_id)
        self.kms_manager = KMSKeyManager(region_name)
        self.iot_manager = IoTCoreManager(region_name)
        
        self.setup_results = {}
    
    def setup_complete_infrastructure(self) -> Dict[str, Any]:
        """
        Set up complete AquaChain infrastructure in the correct order
        """
        print("=" * 60)
        print("Starting AquaChain Infrastructure Setup")
        print("=" * 60)
        
        try:
            # Step 1: Create KMS keys (needed for encryption)
            print("\n1. Creating KMS encryption keys...")
            self.setup_results['kms'] = self.kms_manager.create_all_keys(self.replica_account_id)
            self._wait_for_resource_creation("KMS keys", 10)
            
            # Step 2: Create S3 buckets with encryption
            print("\n2. Creating S3 buckets...")
            self.setup_results['s3'] = self.s3_manager.create_all_buckets(self.replica_account_id)
            self._wait_for_resource_creation("S3 buckets", 15)
            
            # Step 3: Create DynamoDB tables
            print("\n3. Creating DynamoDB tables...")
            self.dynamodb_manager.create_all_tables()
            self.setup_results['dynamodb'] = {'status': 'created'}
            self._wait_for_resource_creation("DynamoDB tables", 30)
            
            # Step 4: Set up IoT Core
            print("\n4. Setting up AWS IoT Core...")
            self.setup_results['iot'] = self.iot_manager.setup_iot_core()
            self._wait_for_resource_creation("IoT Core resources", 20)
            
            # Step 5: Create IAM roles and policies
            print("\n5. Creating IAM roles and policies...")
            self.setup_results['iam'] = self._create_iam_resources()
            
            # Step 6: Deploy Lambda functions
            print("\n6. Deploying Lambda functions...")
            self.setup_results['lambda'] = self._deploy_lambda_functions()
            
            # Step 7: Configure monitoring and alerting
            print("\n7. Setting up monitoring and alerting...")
            self.setup_results['monitoring'] = self._setup_monitoring()
            
            # Step 8: Validate setup
            print("\n8. Validating infrastructure setup...")
            validation_results = self._validate_infrastructure()
            self.setup_results['validation'] = validation_results
            
            print("\n" + "=" * 60)
            print("AquaChain Infrastructure Setup Complete!")
            print("=" * 60)
            
            self._print_setup_summary()
            return self.setup_results
            
        except Exception as e:
            print(f"\nERROR: Infrastructure setup failed: {e}")
            self._cleanup_partial_setup()
            raise
    
    def _create_iam_resources(self) -> Dict[str, Any]:
        """
        Create necessary IAM roles and policies
        """
        iam_client = boto3.client('iam')
        created_roles = []
        
        # Role definitions
        roles = [
            {
                'name': 'AquaChainDataProcessingRole',
                'assume_role_policy': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                'policies': [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'AquaChainDataProcessingPolicy'
                ]
            },
            {
                'name': 'AquaChainIoTRole',
                'assume_role_policy': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "iot.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                'policies': ['AquaChainIoTPolicy']
            },
            {
                'name': 'AquaChainProvisioningRole',
                'assume_role_policy': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "iot.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                'policies': ['AquaChainProvisioningPolicy']
            }
        ]
        
        # Create custom policies first
        self._create_custom_policies(iam_client)
        
        # Create roles
        for role_def in roles:
            try:
                response = iam_client.create_role(
                    RoleName=role_def['name'],
                    AssumeRolePolicyDocument=json.dumps(role_def['assume_role_policy']),
                    Tags=[
                        {'Key': 'Project', 'Value': 'AquaChain'},
                        {'Key': 'Environment', 'Value': 'production'}
                    ]
                )
                
                # Attach policies
                for policy in role_def['policies']:
                    if policy.startswith('arn:aws:iam::aws:policy'):
                        # AWS managed policy
                        iam_client.attach_role_policy(
                            RoleName=role_def['name'],
                            PolicyArn=policy
                        )
                    else:
                        # Custom policy
                        iam_client.attach_role_policy(
                            RoleName=role_def['name'],
                            PolicyArn=f"arn:aws:iam::{self.account_id}:policy/{policy}"
                        )
                
                created_roles.append(role_def['name'])
                print(f"Created IAM role: {role_def['name']}")
                
            except iam_client.exceptions.EntityAlreadyExistsException:
                print(f"IAM role already exists: {role_def['name']}")
                created_roles.append(role_def['name'])
        
        return {'created_roles': created_roles}
    
    def _create_custom_policies(self, iam_client):
        """
        Create custom IAM policies
        """
        policies = [
            {
                'name': 'AquaChainDataProcessingPolicy',
                'document': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query"
                            ],
                            "Resource": [
                                f"arn:aws:dynamodb:{self.region_name}:{self.account_id}:table/aquachain-*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject",
                                "s3:GetObject"
                            ],
                            "Resource": [
                                f"arn:aws:s3:::aquachain-*/*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                                "kms:Sign"
                            ],
                            "Resource": [
                                f"arn:aws:kms:{self.region_name}:{self.account_id}:key/*"
                            ]
                        }
                    ]
                }
            },
            {
                'name': 'AquaChainIoTPolicy',
                'document': {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "lambda:InvokeFunction"
                            ],
                            "Resource": [
                                f"arn:aws:lambda:{self.region_name}:{self.account_id}:function:AquaChain*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject"
                            ],
                            "Resource": [
                                f"arn:aws:s3:::aquachain-data-lake-{self.account_id}/*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "sns:Publish"
                            ],
                            "Resource": [
                                f"arn:aws:sns:{self.region_name}:{self.account_id}:aquachain-*"
                            ]
                        }
                    ]
                }
            }
        ]
        
        for policy in policies:
            try:
                iam_client.create_policy(
                    PolicyName=policy['name'],
                    PolicyDocument=json.dumps(policy['document']),
                    Tags=[
                        {'Key': 'Project', 'Value': 'AquaChain'},
                        {'Key': 'Environment', 'Value': 'production'}
                    ]
                )
                print(f"Created IAM policy: {policy['name']}")
            except iam_client.exceptions.EntityAlreadyExistsException:
                print(f"IAM policy already exists: {policy['name']}")
    
    def _deploy_lambda_functions(self) -> Dict[str, Any]:
        """
        Deploy Lambda functions (placeholder - would use SAM or CDK in practice)
        """
        print("Lambda deployment would be handled by SAM/CDK in production")
        return {'status': 'configured', 'note': 'Use SAM or CDK for actual deployment'}
    
    def _setup_monitoring(self) -> Dict[str, Any]:
        """
        Set up CloudWatch monitoring and alarms
        """
        cloudwatch = boto3.client('cloudwatch')
        
        # Create basic alarms
        alarms = [
            {
                'AlarmName': 'AquaChain-DynamoDB-Errors',
                'MetricName': 'Errors',
                'Namespace': 'AWS/DynamoDB',
                'Statistic': 'Sum',
                'Threshold': 10,
                'ComparisonOperator': 'GreaterThanThreshold'
            },
            {
                'AlarmName': 'AquaChain-Lambda-Duration',
                'MetricName': 'Duration',
                'Namespace': 'AWS/Lambda',
                'Statistic': 'Average',
                'Threshold': 30000,  # 30 seconds
                'ComparisonOperator': 'GreaterThanThreshold'
            }
        ]
        
        created_alarms = []
        for alarm in alarms:
            try:
                cloudwatch.put_metric_alarm(
                    AlarmName=alarm['AlarmName'],
                    ComparisonOperator=alarm['ComparisonOperator'],
                    EvaluationPeriods=2,
                    MetricName=alarm['MetricName'],
                    Namespace=alarm['Namespace'],
                    Period=300,
                    Statistic=alarm['Statistic'],
                    Threshold=alarm['Threshold'],
                    ActionsEnabled=True,
                    AlarmDescription=f'AquaChain monitoring alarm for {alarm["MetricName"]}',
                    Unit='Count'
                )
                created_alarms.append(alarm['AlarmName'])
                print(f"Created CloudWatch alarm: {alarm['AlarmName']}")
            except Exception as e:
                print(f"Error creating alarm {alarm['AlarmName']}: {e}")
        
        return {'created_alarms': created_alarms}
    
    def _validate_infrastructure(self) -> Dict[str, Any]:
        """
        Validate that all infrastructure components are working
        """
        validation_results = {}
        
        # Validate DynamoDB tables
        try:
            dynamodb = boto3.client('dynamodb')
            tables = ['aquachain-readings', 'aquachain-ledger', 'aquachain-sequence']
            
            for table in tables:
                response = dynamodb.describe_table(TableName=table)
                if response['Table']['TableStatus'] == 'ACTIVE':
                    validation_results[f'dynamodb_{table}'] = 'ACTIVE'
                else:
                    validation_results[f'dynamodb_{table}'] = 'NOT_READY'
        except Exception as e:
            validation_results['dynamodb'] = f'ERROR: {e}'
        
        # Validate S3 buckets
        try:
            s3 = boto3.client('s3')
            buckets = [f'aquachain-data-lake-{self.account_id}', f'aquachain-audit-trail-{self.account_id}']
            
            for bucket in buckets:
                try:
                    s3.head_bucket(Bucket=bucket)
                    validation_results[f's3_{bucket}'] = 'EXISTS'
                except Exception:
                    validation_results[f's3_{bucket}'] = 'NOT_FOUND'
        except Exception as e:
            validation_results['s3'] = f'ERROR: {e}'
        
        # Validate IoT Core endpoint
        try:
            endpoint = self.iot_manager.get_iot_endpoint()
            validation_results['iot_endpoint'] = endpoint
        except Exception as e:
            validation_results['iot_endpoint'] = f'ERROR: {e}'
        
        return validation_results
    
    def _wait_for_resource_creation(self, resource_type: str, seconds: int):
        """
        Wait for AWS resources to be fully created
        """
        print(f"Waiting {seconds} seconds for {resource_type} to be ready...")
        time.sleep(seconds)
    
    def _print_setup_summary(self):
        """
        Print summary of created resources
        """
        print("\nSetup Summary:")
        print("-" * 40)
        
        if 'kms' in self.setup_results:
            print("✓ KMS encryption keys created")
        
        if 's3' in self.setup_results:
            print("✓ S3 buckets created with Object Lock")
        
        if 'dynamodb' in self.setup_results:
            print("✓ DynamoDB tables created with streams")
        
        if 'iot' in self.setup_results:
            print("✓ IoT Core configured with device policies")
        
        if 'iam' in self.setup_results:
            print("✓ IAM roles and policies created")
        
        print("\nNext Steps:")
        print("1. Deploy Lambda functions using SAM or CDK")
        print("2. Configure API Gateway endpoints")
        print("3. Set up monitoring dashboards")
        print("4. Test device provisioning workflow")
    
    def _cleanup_partial_setup(self):
        """
        Clean up resources if setup fails partway through
        """
        print("Cleaning up partially created resources...")
        # Implementation would depend on what was created
        # This is a placeholder for cleanup logic

def main():
    """
    Main function to run infrastructure setup
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up AquaChain infrastructure')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--replica-account', help='Replica account ID for cross-account replication')
    
    args = parser.parse_args()
    
    try:
        manager = AquaChainInfrastructureManager(
            region_name=args.region,
            replica_account_id=args.replica_account
        )
        
        results = manager.setup_complete_infrastructure()
        
        # Save results to file
        with open('infrastructure_setup_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nSetup results saved to: infrastructure_setup_results.json")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()