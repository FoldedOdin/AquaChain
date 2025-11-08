"""
SBOM Storage Stack
S3 bucket for storing Software Bill of Materials with versioning and lifecycle policies
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    CfnOutput
)
from constructs import Construct


class SBOMStorageStack(Stack):
    """Stack for SBOM storage and management"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # KMS key for encryption
        self.kms_key = kms.Key(
            self, 'SBOMEncryptionKey',
            description='KMS key for SBOM bucket encryption',
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # S3 bucket for SBOM storage
        self.sbom_bucket = s3.Bucket(
            self, 'SBOMBucket',
            bucket_name=f'aquachain-sbom-{self.account}',
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            lifecycle_rules=[
                # Keep all versions for 90 days
                s3.LifecycleRule(
                    id='RetainVersions90Days',
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(90)
                ),
                # Transition old versions to Glacier after 30 days
                s3.LifecycleRule(
                    id='TransitionToGlacier',
                    enabled=True,
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30)
                        )
                    ]
                ),
                # Keep weekly SBOMs for 1 year
                s3.LifecycleRule(
                    id='RetainWeeklySBOMs',
                    enabled=True,
                    prefix='weekly/',
                    expiration=Duration.days(365)
                ),
                # Keep latest SBOMs indefinitely (no expiration)
                # Transition to Intelligent-Tiering after 90 days
                s3.LifecycleRule(
                    id='LatestSBOMsIntelligentTiering',
                    enabled=True,
                    prefix='latest/',
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(90)
                        )
                    ]
                ),
                # Delete incomplete multipart uploads after 7 days
                s3.LifecycleRule(
                    id='CleanupIncompleteUploads',
                    enabled=True,
                    abort_incomplete_multipart_upload_after=Duration.days(7)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Enable bucket logging
        self.access_logs_bucket = s3.Bucket(
            self, 'SBOMAccessLogsBucket',
            bucket_name=f'aquachain-sbom-logs-{self.account}',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id='DeleteOldLogs',
                    enabled=True,
                    expiration=Duration.days(90)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.sbom_bucket.enable_event_bridge_notification()
        
        # SNS topic for SBOM notifications
        self.sbom_topic = sns.Topic(
            self, 'SBOMNotificationTopic',
            topic_name='aquachain-sbom-notifications',
            display_name='AquaChain SBOM Notifications'
        )
        
        # Lambda function for SBOM comparison
        self.comparison_function = lambda_.Function(
            self, 'SBOMComparisonFunction',
            function_name='aquachain-sbom-comparison',
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler='index.handler',
            code=lambda_.Code.from_inline('''
import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

def handler(event, context):
    """Compare new SBOM with previous version and detect changes"""
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Only process complete SBOMs
    if not key.startswith('sbom-complete-') or not key.endswith('.json'):
        return {'statusCode': 200, 'body': 'Skipped non-complete SBOM'}
    
    try:
        # Get new SBOM
        response = s3.get_object(Bucket=bucket, Key=key)
        new_sbom = json.loads(response['Body'].read())
        
        # Get previous version
        versions = s3.list_object_versions(Bucket=bucket, Prefix=key, MaxKeys=2)
        
        if len(versions.get('Versions', [])) < 2:
            print("No previous version to compare")
            return {'statusCode': 200, 'body': 'First version'}
        
        prev_version_id = versions['Versions'][1]['VersionId']
        prev_response = s3.get_object(Bucket=bucket, Key=key, VersionId=prev_version_id)
        prev_sbom = json.loads(prev_response['Body'].read())
        
        # Compare packages
        new_packages = {pkg['name']: pkg.get('versionInfo', 'unknown') 
                       for pkg in new_sbom.get('packages', [])}
        prev_packages = {pkg['name']: pkg.get('versionInfo', 'unknown') 
                        for pkg in prev_sbom.get('packages', [])}
        
        # Detect changes
        added = set(new_packages.keys()) - set(prev_packages.keys())
        removed = set(prev_packages.keys()) - set(new_packages.keys())
        updated = {name for name in new_packages.keys() & prev_packages.keys()
                  if new_packages[name] != prev_packages[name]}
        
        # Create comparison report
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'sbom_key': key,
            'total_packages': len(new_packages),
            'changes': {
                'added': len(added),
                'removed': len(removed),
                'updated': len(updated)
            },
            'added_packages': list(added)[:10],  # Limit to 10
            'removed_packages': list(removed)[:10],
            'updated_packages': list(updated)[:10]
        }
        
        # Save comparison report
        report_key = key.replace('.json', '-comparison.json')
        s3.put_object(
            Bucket=bucket,
            Key=report_key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        
        # Send notification if significant changes
        if len(added) > 0 or len(removed) > 0 or len(updated) > 10:
            message = f"""
SBOM Change Detection

Total Packages: {len(new_packages)}
Added: {len(added)}
Removed: {len(removed)}
Updated: {len(updated)}

Comparison report: s3://{bucket}/{report_key}
"""
            
            topic_arn = f"arn:aws:sns:{context.invoked_function_arn.split(':')[3]}:{context.invoked_function_arn.split(':')[4]}:aquachain-sbom-notifications"
            
            try:
                sns.publish(
                    TopicArn=topic_arn,
                    Subject=f'SBOM Changes Detected: {len(added)} added, {len(removed)} removed, {len(updated)} updated',
                    Message=message
                )
            except Exception as e:
                print(f"Could not send SNS notification: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(report)
        }
        
    except Exception as e:
        print(f"Error comparing SBOMs: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }
'''),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                'SBOM_BUCKET': self.sbom_bucket.bucket_name,
                'SNS_TOPIC_ARN': self.sbom_topic.topic_arn
            }
        )
        
        # Grant permissions
        self.sbom_bucket.grant_read_write(self.comparison_function)
        self.sbom_topic.grant_publish(self.comparison_function)
        
        # Add S3 event trigger for new SBOMs
        self.comparison_function.add_event_source(
            lambda_events.S3EventSource(
                self.sbom_bucket,
                events=[s3.EventType.OBJECT_CREATED],
                filters=[s3.NotificationKeyFilter(prefix='sbom-complete-', suffix='.json')]
            )
        )
        
        # IAM policy for CI/CD to upload SBOMs
        self.cicd_policy = iam.ManagedPolicy(
            self, 'SBOMUploadPolicy',
            managed_policy_name='AquaChain-SBOM-Upload-Policy',
            description='Policy for CI/CD to upload SBOMs to S3',
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        's3:PutObject',
                        's3:PutObjectAcl',
                        's3:GetObject',
                        's3:ListBucket'
                    ],
                    resources=[
                        self.sbom_bucket.bucket_arn,
                        f'{self.sbom_bucket.bucket_arn}/*'
                    ]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'kms:Decrypt',
                        'kms:GenerateDataKey'
                    ],
                    resources=[self.kms_key.key_arn]
                )
            ]
        )
        
        # Outputs
        CfnOutput(
            self, 'SBOMBucketName',
            value=self.sbom_bucket.bucket_name,
            description='S3 bucket for SBOM storage',
            export_name='AquaChain-SBOM-Bucket'
        )
        
        CfnOutput(
            self, 'SBOMBucketArn',
            value=self.sbom_bucket.bucket_arn,
            description='ARN of SBOM bucket',
            export_name='AquaChain-SBOM-Bucket-Arn'
        )
        
        CfnOutput(
            self, 'SBOMTopicArn',
            value=self.sbom_topic.topic_arn,
            description='SNS topic for SBOM notifications',
            export_name='AquaChain-SBOM-Topic-Arn'
        )
        
        CfnOutput(
            self, 'SBOMComparisonFunctionArn',
            value=self.comparison_function.function_arn,
            description='Lambda function for SBOM comparison',
            export_name='AquaChain-SBOM-Comparison-Function-Arn'
        )
        
        CfnOutput(
            self, 'CICDPolicyArn',
            value=self.cicd_policy.managed_policy_arn,
            description='IAM policy for CI/CD SBOM uploads',
            export_name='AquaChain-SBOM-CICD-Policy-Arn'
        )
