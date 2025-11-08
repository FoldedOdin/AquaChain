"""
Complete security infrastructure setup for AquaChain.
Orchestrates all security components: encryption, audit logging, rate limiting, and compliance.
Requirements: 8.5, 15.5, 2.4, 15.1
"""

import boto3
import json
import logging
import time
from typing import Dict, Any
from botocore.exceptions import ClientError

# Import our security setup modules
from .encryption_setup import EncryptionInfrastructureSetup
from .audit_infrastructure import AuditInfrastructureSetup
from .rate_limiting_setup import RateLimitingSetup

logger = logging.getLogger(__name__)

class CompleteSecuritySetup:
    """Orchestrates complete security infrastructure setup"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.encryption_setup = EncryptionInfrastructureSetup(region)
        self.audit_setup = AuditInfrastructureSetup(region)
        self.rate_limiting_setup = RateLimitingSetup(region)
        
        # AWS clients
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
    
    def create_security_roles(self) -> Dict[str, Any]:
        """Create IAM roles for security services"""
        try:
            roles_created = {}
            
            # Security Lambda execution role
            security_lambda_role = {
                'RoleName': 'AquaChainSecurityLambdaRole',
                'AssumeRolePolicyDocument': json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }),
                'Description': 'Execution role for AquaChain security Lambda functions',
                'Tags': [
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Security'}
                ]
            }
            
            try:
                response = self.iam.create_role(**security_lambda_role)
                roles_created['security_lambda_role'] = response['Role']['Arn']
                
                # Attach managed policies
                managed_policies = [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess'
                ]
                
                for policy_arn in managed_policies:
                    self.iam.attach_role_policy(
                        RoleName=security_lambda_role['RoleName'],
                        PolicyArn=policy_arn
                    )
                
                # Create custom policy for security operations
                security_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:GenerateDataKey*",
                                "kms:Sign",
                                "kms:Verify",
                                "kms:DescribeKey"
                            ],
                            "Resource": "*",
                            "Condition": {
                                "StringEquals": {
                                    "kms:ViaService": [
                                        f"s3.{self.region}.amazonaws.com",
                                        f"dynamodb.{self.region}.amazonaws.com"
                                    ]
                                }
                            }
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            "Resource": [
                                f"arn:aws:dynamodb:{self.region}:*:table/aquachain-*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject"
                            ],
                            "Resource": [
                                "arn:aws:s3:::aquachain-*/*"
                            ]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": "*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "sns:Publish"
                            ],
                            "Resource": [
                                f"arn:aws:sns:{self.region}:*:aquachain-*"
                            ]
                        }
                    ]
                }
                
                self.iam.put_role_policy(
                    RoleName=security_lambda_role['RoleName'],
                    PolicyName='AquaChainSecurityPolicy',
                    PolicyDocument=json.dumps(security_policy)
                )
                
                logger.info(f"Created security Lambda role: {security_lambda_role['RoleName']}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityAlreadyExistsException':
                    response = self.iam.get_role(RoleName=security_lambda_role['RoleName'])
                    roles_created['security_lambda_role'] = response['Role']['Arn']
                    logger.info(f"Security Lambda role already exists: {security_lambda_role['RoleName']}")
                else:
                    raise
            
            return roles_created
            
        except Exception as e:
            logger.error(f"Error creating security roles: {e}")
            raise
    
    def create_security_topics(self) -> Dict[str, Any]:
        """Create SNS topics for security alerts"""
        try:
            topics_created = {}
            
            # Security alerts topic
            security_topic = self.sns.create_topic(
                Name='aquachain-security-alerts',
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Security'},
                    {'Key': 'AlertType', 'Value': 'Security'}
                ]
            )
            
            topics_created['security_alerts'] = security_topic['TopicArn']
            
            # Compliance alerts topic
            compliance_topic = self.sns.create_topic(
                Name='aquachain-compliance-alerts',
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Compliance'},
                    {'Key': 'AlertType', 'Value': 'Compliance'}
                ]
            )
            
            topics_created['compliance_alerts'] = compliance_topic['TopicArn']
            
            # Set topic policies
            for topic_name, topic_arn in topics_created.items():
                topic_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sns:Publish",
                            "Resource": topic_arn,
                            "Condition": {
                                "StringEquals": {
                                    "aws:SourceAccount": "123456789012"
                                }
                            }
                        }
                    ]
                }
                
                self.sns.set_topic_attributes(
                    TopicArn=topic_arn,
                    AttributeName='Policy',
                    AttributeValue=json.dumps(topic_policy)
                )
            
            logger.info("Created security SNS topics")
            return topics_created
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'TopicLimitExceeded':
                logger.warning("SNS topic limit exceeded, using existing topics")
                # Get existing topics
                response = self.sns.list_topics()
                existing_topics = {}
                for topic in response['Topics']:
                    topic_name = topic['TopicArn'].split(':')[-1]
                    if topic_name.startswith('aquachain-'):
                        existing_topics[topic_name.replace('aquachain-', '')] = topic['TopicArn']
                return existing_topics
            else:
                logger.error(f"Error creating security topics: {e}")
                raise
    
    def create_security_monitoring(self) -> Dict[str, Any]:
        """Set up CloudWatch monitoring for security events"""
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            # Create custom metrics for security monitoring
            security_metrics = [
                {
                    'MetricName': 'SecurityViolations',
                    'Namespace': 'AquaChain/Security',
                    'Description': 'Number of security violations detected'
                },
                {
                    'MetricName': 'FailedAuthentications',
                    'Namespace': 'AquaChain/Security',
                    'Description': 'Number of failed authentication attempts'
                },
                {
                    'MetricName': 'RateLimitViolations',
                    'Namespace': 'AquaChain/Security',
                    'Description': 'Number of rate limit violations'
                },
                {
                    'MetricName': 'EncryptionErrors',
                    'Namespace': 'AquaChain/Security',
                    'Description': 'Number of encryption/decryption errors'
                },
                {
                    'MetricName': 'AuditLogErrors',
                    'Namespace': 'AquaChain/Security',
                    'Description': 'Number of audit logging errors'
                }
            ]
            
            # Create CloudWatch alarms
            alarms_created = []
            
            for metric in security_metrics:
                alarm_name = f"AquaChain-{metric['MetricName']}-High"
                
                try:
                    cloudwatch.put_metric_alarm(
                        AlarmName=alarm_name,
                        ComparisonOperator='GreaterThanThreshold',
                        EvaluationPeriods=2,
                        MetricName=metric['MetricName'],
                        Namespace=metric['Namespace'],
                        Period=300,  # 5 minutes
                        Statistic='Sum',
                        Threshold=10.0,
                        ActionsEnabled=True,
                        AlarmActions=[
                            # Will be populated with SNS topic ARNs
                        ],
                        AlarmDescription=f"High {metric['MetricName']} detected",
                        Unit='Count',
                        Tags=[
                            {'Key': 'Project', 'Value': 'AquaChain'},
                            {'Key': 'Component', 'Value': 'Security'},
                            {'Key': 'AlertType', 'Value': 'Metric'}
                        ]
                    )
                    
                    alarms_created.append(alarm_name)
                    
                except ClientError as e:
                    if e.response['Error']['Code'] != 'AlarmAlreadyExists':
                        logger.error(f"Error creating alarm {alarm_name}: {e}")
            
            logger.info(f"Created {len(alarms_created)} security monitoring alarms")
            
            return {
                'metrics': security_metrics,
                'alarms': alarms_created
            }
            
        except Exception as e:
            logger.error(f"Error setting up security monitoring: {e}")
            raise
    
    def validate_security_setup(self) -> Dict[str, Any]:
        """Validate that all security components are properly configured"""
        try:
            validation_results = {
                'encryption': {'status': 'unknown', 'details': {}},
                'audit_logging': {'status': 'unknown', 'details': {}},
                'rate_limiting': {'status': 'unknown', 'details': {}},
                'monitoring': {'status': 'unknown', 'details': {}},
                'overall_status': 'unknown'
            }
            
            # Validate encryption setup
            try:
                kms = boto3.client('kms', region_name=self.region)
                
                # Check if master key exists and is enabled
                response = kms.describe_key(KeyId='alias/aquachain-master-key')
                if response['KeyMetadata']['KeyState'] == 'Enabled':
                    validation_results['encryption']['status'] = 'healthy'
                    validation_results['encryption']['details']['master_key'] = 'enabled'
                else:
                    validation_results['encryption']['status'] = 'error'
                    validation_results['encryption']['details']['master_key'] = 'disabled'
                
            except ClientError as e:
                validation_results['encryption']['status'] = 'error'
                validation_results['encryption']['details']['error'] = str(e)
            
            # Validate audit logging setup
            try:
                dynamodb = boto3.client('dynamodb', region_name=self.region)
                
                # Check if audit table exists
                response = dynamodb.describe_table(TableName='aquachain-audit-logs')
                if response['Table']['TableStatus'] == 'ACTIVE':
                    validation_results['audit_logging']['status'] = 'healthy'
                    validation_results['audit_logging']['details']['table'] = 'active'
                else:
                    validation_results['audit_logging']['status'] = 'error'
                    validation_results['audit_logging']['details']['table'] = response['Table']['TableStatus']
                
            except ClientError as e:
                validation_results['audit_logging']['status'] = 'error'
                validation_results['audit_logging']['details']['error'] = str(e)
            
            # Validate rate limiting setup
            try:
                dynamodb = boto3.client('dynamodb', region_name=self.region)
                
                # Check if rate limiting table exists
                response = dynamodb.describe_table(TableName='aquachain-rate-limits')
                if response['Table']['TableStatus'] == 'ACTIVE':
                    validation_results['rate_limiting']['status'] = 'healthy'
                    validation_results['rate_limiting']['details']['table'] = 'active'
                else:
                    validation_results['rate_limiting']['status'] = 'error'
                    validation_results['rate_limiting']['details']['table'] = response['Table']['TableStatus']
                
            except ClientError as e:
                validation_results['rate_limiting']['status'] = 'error'
                validation_results['rate_limiting']['details']['error'] = str(e)
            
            # Validate monitoring setup
            try:
                cloudwatch = boto3.client('cloudwatch', region_name=self.region)
                
                # Check if security alarms exist
                response = cloudwatch.describe_alarms(
                    AlarmNamePrefix='AquaChain-SecurityViolations'
                )
                
                if response['MetricAlarms']:
                    validation_results['monitoring']['status'] = 'healthy'
                    validation_results['monitoring']['details']['alarms'] = len(response['MetricAlarms'])
                else:
                    validation_results['monitoring']['status'] = 'warning'
                    validation_results['monitoring']['details']['alarms'] = 0
                
            except ClientError as e:
                validation_results['monitoring']['status'] = 'error'
                validation_results['monitoring']['details']['error'] = str(e)
            
            # Determine overall status
            component_statuses = [
                validation_results['encryption']['status'],
                validation_results['audit_logging']['status'],
                validation_results['rate_limiting']['status'],
                validation_results['monitoring']['status']
            ]
            
            if all(status == 'healthy' for status in component_statuses):
                validation_results['overall_status'] = 'healthy'
            elif any(status == 'error' for status in component_statuses):
                validation_results['overall_status'] = 'error'
            else:
                validation_results['overall_status'] = 'warning'
            
            logger.info(f"Security validation completed: {validation_results['overall_status']}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating security setup: {e}")
            return {
                'overall_status': 'error',
                'error': str(e)
            }
    
    def setup_complete_security_infrastructure(self) -> Dict[str, Any]:
        """Set up complete security infrastructure"""
        try:
            logger.info("Starting complete security infrastructure setup...")
            
            setup_results = {
                'start_time': time.time(),
                'components': {}
            }
            
            # 1. Create security roles
            logger.info("Creating security IAM roles...")
            setup_results['components']['iam_roles'] = self.create_security_roles()
            
            # 2. Set up encryption infrastructure
            logger.info("Setting up encryption infrastructure...")
            setup_results['components']['encryption'] = self.encryption_setup.setup_encryption_infrastructure()
            
            # 3. Set up audit logging infrastructure
            logger.info("Setting up audit logging infrastructure...")
            setup_results['components']['audit_logging'] = self.audit_setup.setup_audit_infrastructure()
            
            # 4. Set up rate limiting infrastructure
            logger.info("Setting up rate limiting infrastructure...")
            setup_results['components']['rate_limiting'] = self.rate_limiting_setup.setup_security_infrastructure()
            
            # 5. Create security monitoring
            logger.info("Setting up security monitoring...")
            setup_results['components']['monitoring'] = self.create_security_monitoring()
            
            # 6. Create SNS topics for alerts
            logger.info("Creating security alert topics...")
            setup_results['components']['sns_topics'] = self.create_security_topics()
            
            # 7. Validate setup
            logger.info("Validating security setup...")
            setup_results['validation'] = self.validate_security_setup()
            
            setup_results['end_time'] = time.time()
            setup_results['duration'] = setup_results['end_time'] - setup_results['start_time']
            setup_results['status'] = 'completed'
            
            logger.info(f"Complete security infrastructure setup completed in {setup_results['duration']:.2f} seconds")
            logger.info(f"Overall security status: {setup_results['validation']['overall_status']}")
            
            return setup_results
            
        except Exception as e:
            logger.error(f"Error setting up complete security infrastructure: {e}")
            raise

def main():
    """Main function to set up complete security infrastructure"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    setup = CompleteSecuritySetup()
    result = setup.setup_complete_security_infrastructure()
    
    print("\n" + "="*80)
    print("AQUACHAIN SECURITY INFRASTRUCTURE SETUP COMPLETE")
    print("="*80)
    
    print(f"\nSetup Duration: {result['duration']:.2f} seconds")
    print(f"Overall Status: {result['validation']['overall_status'].upper()}")
    
    print(f"\nComponents Configured:")
    print(f"  ✓ Encryption Keys: {len(result['components']['encryption']['kms_keys'])}")
    print(f"  ✓ S3 Buckets: {len(result['components']['encryption']['s3_buckets'])}")
    print(f"  ✓ DynamoDB Tables: {len(result['components']['encryption']['dynamodb_tables'])}")
    print(f"  ✓ Audit Infrastructure: {len(result['components']['audit_logging']['tables'])}")
    print(f"  ✓ Rate Limiting: {result['components']['rate_limiting']['rateLimiting']['status']}")
    print(f"  ✓ Security Monitoring: {len(result['components']['monitoring']['alarms'])} alarms")
    print(f"  ✓ SNS Topics: {len(result['components']['sns_topics'])}")
    
    print(f"\nValidation Results:")
    for component, status in result['validation'].items():
        if component != 'overall_status':
            print(f"  {component.replace('_', ' ').title()}: {status['status'].upper()}")
    
    if result['validation']['overall_status'] == 'healthy':
        print(f"\n🎉 All security components are healthy and ready for production!")
    elif result['validation']['overall_status'] == 'warning':
        print(f"\n⚠️  Security setup completed with warnings. Review component details.")
    else:
        print(f"\n❌ Security setup completed with errors. Manual intervention required.")
    
    print("="*80)
    
    return result

if __name__ == "__main__":
    main()