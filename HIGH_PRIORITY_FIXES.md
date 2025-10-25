# 🟠 HIGH PRIORITY FIXES - Implementation Guide

**Status:** In Progress  
**Target Completion:** Week 2-3

---

## Overview

This document tracks the implementation of 15 HIGH priority issues identified in the security audit.

---

## ✅ Fix #1: CDK Cyclic Dependencies RESOLVED

### Status: COMPLETED ✅

### What Was Fixed
- Removed circular dependency between ComputeStack, APIStack, and WebSocketAPI
- Updated `infrastructure/cdk/app.py` to use proper dependency chain
- Created comprehensive guide: `infrastructure/cdk/CDK_DEPENDENCY_FIX.md`

### Solution Implemented
```python
# Use CloudFormation exports instead of direct references
CfnOutput(
    self, "FunctionArn",
    value=function.function_arn,
    export_name=f"{Stack.of(self).stack_name}-FunctionArn"
)

# Import in dependent stack
function_arn = Fn.import_value("StackName-FunctionArn")
```

### Deployment
```bash
# Deploy all stacks (CDK handles order automatically)
cd infrastructure/cdk
cdk deploy --all

# Or deploy individually
cdk deploy AquaChain-Security-dev
cdk deploy AquaChain-Core-dev
cdk deploy AquaChain-Data-dev
cdk deploy AquaChain-Compute-dev
cdk deploy AquaChain-API-dev
cdk deploy AquaChain-Monitoring-dev
```

### Files Created/Modified
- `infrastructure/cdk/app.py` - Fixed dependency chain
- `infrastructure/cdk/CDK_DEPENDENCY_FIX.md` - Implementation guide

---

## ✅ Fix #2: VPC Configuration for Lambda IMPLEMENTED

### Status: COMPLETED ✅

### What Was Created
- New VPC stack with public, private, and isolated subnets
- Security groups for Lambda functions and RDS
- VPC endpoints for AWS services (DynamoDB, S3, Secrets Manager, KMS)
- VPC Flow Logs for security monitoring

### Architecture
```
VPC (10.0.0.0/16)
├── Public Subnets (3 AZs)
│   └── NAT Gateways
├── Private Subnets (3 AZs)
│   └── Lambda Functions
└── Isolated Subnets (3 AZs)
    └── RDS Databases (future)
```

### Implementation
```python
# In ComputeStack, deploy Lambda in VPC
lambda_function = _lambda.Function(
    self, "DataProcessingFunction",
    # ... other config
    vpc=vpc,
    vpc_subnets=ec2.SubnetSelection(
        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
    ),
    security_groups=[lambda_security_group]
)
```

### Cost Optimization
- Gateway endpoints (DynamoDB, S3): **FREE**
- Interface endpoints: ~$7/month each
- NAT Gateways: ~$32/month each (2 for HA)
- **Total VPC Cost:** ~$85/month

### Files Created
- `infrastructure/cdk/stacks/vpc_stack.py` - Complete VPC implementation

---

## 🔄 Fix #3: DynamoDB Backup Strategy ENHANCED

### Status: IN PROGRESS 🔄

### Current State
- Point-in-time recovery enabled
- Manual backups possible

### What Needs to Be Added
1. **Automated Daily Backups**
2. **Cross-Region Replication (Global Tables)**
3. **Backup Verification**
4. **Automated Restore Testing**

### Implementation Plan

#### Step 1: Enable Global Tables
```python
# In DataStack
from aws_cdk import aws_dynamodb as dynamodb

readings_table = dynamodb.Table(
    self, "ReadingsTable",
    # ... existing config
    replication_regions=["us-west-2", "eu-west-1"],  # Multi-region
    replication_timeout=Duration.hours(2)
)
```

#### Step 2: Automated Backup Lambda
```python
# lambda/backup/automated_backup.py
import boto3
from datetime import datetime

def lambda_handler(event, context):
    dynamodb = boto3.client('dynamodb')
    
    tables = ['aquachain-readings', 'aquachain-devices', 'aquachain-users']
    
    for table in tables:
        backup_name = f"{table}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        dynamodb.create_backup(
            TableName=table,
            BackupName=backup_name
        )
        
        print(f"Created backup: {backup_name}")
```

#### Step 3: Backup Verification
```python
# lambda/backup/verify_backup.py
def verify_backup(backup_arn):
    """Verify backup integrity"""
    dynamodb = boto3.client('dynamodb')
    
    # Describe backup
    response = dynamodb.describe_backup(BackupArn=backup_arn)
    
    # Check status
    if response['BackupDescription']['BackupDetails']['BackupStatus'] != 'AVAILABLE':
        raise Exception(f"Backup not available: {backup_arn}")
    
    # Verify size
    backup_size = response['BackupDescription']['BackupDetails']['BackupSizeBytes']
    if backup_size == 0:
        raise Exception(f"Backup is empty: {backup_arn}")
    
    return True
```

#### Step 4: EventBridge Schedule
```python
# In DataStack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets

# Daily backup at 2 AM UTC
backup_rule = events.Rule(
    self, "DailyBackupRule",
    schedule=events.Schedule.cron(hour="2", minute="0"),
    description="Daily DynamoDB backup"
)

backup_rule.add_target(
    targets.LambdaFunction(backup_lambda)
)
```

### Estimated Effort
- Implementation: 8 hours
- Testing: 4 hours
- Documentation: 2 hours
- **Total: 14 hours**

---

## 🔄 Fix #4: API Gateway Throttling CONFIGURED

### Status: IN PROGRESS 🔄

### Implementation

```python
# In APIStack
from aws_cdk import aws_apigateway as apigateway

rest_api = apigateway.RestApi(
    self, "AquaChainAPI",
    rest_api_name=f"aquachain-api-{config['environment']}",
    
    # Global throttling
    deploy_options=apigateway.StageOptions(
        throttling_rate_limit=100,  # requests per second
        throttling_burst_limit=200,  # burst capacity
        logging_level=apigateway.MethodLoggingLevel.INFO,
        data_trace_enabled=True,
        metrics_enabled=True
    ),
    
    # Default method options
    default_method_options=apigateway.MethodOptions(
        throttling=apigateway.ThrottleSettings(
            rate_limit=100,
            burst_limit=200
        )
    )
)

# Per-endpoint throttling for critical paths
readings_resource = rest_api.root.add_resource("readings")
readings_method = readings_resource.add_method(
    "POST",
    integration,
    method_responses=[
        apigateway.MethodResponse(
            status_code="200",
            response_models={
                "application/json": apigateway.Model.EMPTY_MODEL
            }
        ),
        apigateway.MethodResponse(
            status_code="429",
            response_models={
                "application/json": apigateway.Model.ERROR_MODEL
            }
        )
    ],
    request_validator=apigateway.RequestValidator(
        self, "ReadingsValidator",
        rest_api=rest_api,
        validate_request_body=True,
        validate_request_parameters=True
    )
)

# Usage plan for API keys
usage_plan = rest_api.add_usage_plan(
    "StandardUsagePlan",
    name="Standard",
    throttle=apigateway.ThrottleSettings(
        rate_limit=100,
        burst_limit=200
    ),
    quota=apigateway.QuotaSettings(
        limit=10000,  # 10k requests per day
        period=apigateway.Period.DAY
    )
)
```

### Throttling Tiers

| Tier | Rate Limit | Burst | Quota/Day |
|------|------------|-------|-----------|
| Free | 10 req/s | 20 | 1,000 |
| Standard | 100 req/s | 200 | 10,000 |
| Premium | 1000 req/s | 2000 | 100,000 |

### Estimated Effort
- Implementation: 4 hours
- Testing: 2 hours
- **Total: 6 hours**

---

## 🔄 Fix #5: CloudFront Distribution for Frontend

### Status: READY TO IMPLEMENT 🔄

### Architecture
```
User → CloudFront → S3 (Origin) → React App
         ↓
       AWS WAF (DDoS Protection)
         ↓
       Lambda@Edge (Auth)
```

### Implementation

```python
# infrastructure/cdk/stacks/frontend_stack.py
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_wafv2 as waf,
    RemovalPolicy
)

class AquaChainFrontendStack(Stack):
    def __init__(self, scope, id, config, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # S3 bucket for frontend
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"aquachain-frontend-{config['environment']}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY if config['environment'] == 'dev' else RemovalPolicy.RETAIN,
            auto_delete_objects=config['environment'] == 'dev'
        )
        
        # Origin Access Identity
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment="OAI for AquaChain frontend"
        )
        
        frontend_bucket.grant_read(oai)
        
        # SSL Certificate (must be in us-east-1 for CloudFront)
        certificate = acm.Certificate(
            self, "Certificate",
            domain_name=config.get('domain_name', 'aquachain.example.com'),
            validation=acm.CertificateValidation.from_dns()
        )
        
        # CloudFront distribution
        distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    frontend_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                )
            ],
            certificate=certificate,
            domain_names=[config.get('domain_name')],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # US, Canada, Europe
            enable_logging=True,
            log_bucket=logs_bucket,
            log_file_prefix="cloudfront/"
        )
```

### Deployment Script
```bash
#!/bin/bash
# frontend/deploy-to-cloudfront.sh

# Build React app
npm run build

# Sync to S3
aws s3 sync build/ s3://aquachain-frontend-prod/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"

echo "✅ Frontend deployed to CloudFront"
```

### Cost Estimate
- CloudFront: ~$0.085/GB (first 10TB)
- S3 Storage: ~$0.023/GB
- Certificate: FREE (ACM)
- **Estimated:** ~$10-50/month depending on traffic

### Estimated Effort
- Implementation: 12 hours
- Testing: 4 hours
- DNS Configuration: 2 hours
- **Total: 18 hours**

---

## 🔄 Fix #6: ML Model Versioning System

### Status: READY TO IMPLEMENT 🔄

### Implementation

```python
# lambda/ml_inference/model_registry.py
import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ModelRegistry:
    """
    Centralized model version management
    """
    
    def __init__(self, s3_bucket: str, dynamodb_table: str):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.bucket = s3_bucket
        self.registry_table = self.dynamodb.Table(dynamodb_table)
    
    def register_model(self, model_name: str, version: str, 
                      model_path: str, metrics: Dict[str, float],
                      metadata: Dict[str, Any]) -> str:
        """Register a new model version"""
        
        model_id = f"{model_name}-v{version}"
        
        # Store model metadata in DynamoDB
        self.registry_table.put_item(
            Item={
                'model_id': model_id,
                'model_name': model_name,
                'version': version,
                'model_path': model_path,
                'metrics': metrics,
                'metadata': metadata,
                'status': 'registered',
                'registered_at': datetime.utcnow().isoformat(),
                'is_production': False
            }
        )
        
        return model_id
    
    def promote_to_production(self, model_id: str) -> bool:
        """Promote model to production"""
        
        # Get model info
        response = self.registry_table.get_item(Key={'model_id': model_id})
        if 'Item' not in response:
            raise ValueError(f"Model not found: {model_id}")
        
        model = response['Item']
        model_name = model['model_name']
        
        # Demote current production model
        self._demote_current_production(model_name)
        
        # Promote new model
        self.registry_table.update_item(
            Key={'model_id': model_id},
            UpdateExpression='SET is_production = :true, promoted_at = :now',
            ExpressionAttributeValues={
                ':true': True,
                ':now': datetime.utcnow().isoformat()
            }
        )
        
        return True
    
    def rollback_model(self, model_name: str) -> str:
        """Rollback to previous production model"""
        
        # Get previous production model
        response = self.registry_table.query(
            IndexName='ModelNameIndex',
            KeyConditionExpression='model_name = :name',
            FilterExpression='is_production = :false',
            ExpressionAttributeValues={
                ':name': model_name,
                ':false': False
            },
            ScanIndexForward=False,  # Most recent first
            Limit=1
        )
        
        if not response['Items']:
            raise ValueError(f"No previous version found for {model_name}")
        
        previous_model = response['Items'][0]
        return self.promote_to_production(previous_model['model_id'])
    
    def get_production_model(self, model_name: str) -> Dict[str, Any]:
        """Get current production model"""
        
        response = self.registry_table.query(
            IndexName='ModelNameIndex',
            KeyConditionExpression='model_name = :name',
            FilterExpression='is_production = :true',
            ExpressionAttributeValues={
                ':name': model_name,
                ':true': True
            }
        )
        
        if not response['Items']:
            raise ValueError(f"No production model found for {model_name}")
        
        return response['Items'][0]
```

### A/B Testing Support
```python
class ABTestingManager:
    """
    Manage A/B testing of ML models
    """
    
    def create_ab_test(self, model_a_id: str, model_b_id: str, 
                       traffic_split: float = 0.5) -> str:
        """
        Create A/B test between two models
        
        Args:
            model_a_id: Control model ID
            model_b_id: Treatment model ID
            traffic_split: Percentage of traffic to model B (0.0-1.0)
        """
        test_id = f"ab-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        self.registry_table.put_item(
            Item={
                'test_id': test_id,
                'model_a_id': model_a_id,
                'model_b_id': model_b_id,
                'traffic_split': traffic_split,
                'status': 'active',
                'started_at': datetime.utcnow().isoformat(),
                'metrics': {
                    'model_a': {'requests': 0, 'errors': 0},
                    'model_b': {'requests': 0, 'errors': 0}
                }
            }
        )
        
        return test_id
    
    def route_request(self, test_id: str) -> str:
        """Route request to model A or B based on traffic split"""
        import random
        
        # Get test configuration
        response = self.registry_table.get_item(Key={'test_id': test_id})
        test = response['Item']
        
        # Route based on traffic split
        if random.random() < test['traffic_split']:
            return test['model_b_id']
        else:
            return test['model_a_id']
```

### Estimated Effort
- Implementation: 16 hours
- Testing: 6 hours
- Documentation: 2 hours
- **Total: 24 hours**

---

## 📊 Progress Summary

| Fix | Status | Effort | Priority |
|-----|--------|--------|----------|
| CDK Dependencies | ✅ Complete | 16h | HIGH |
| VPC Configuration | ✅ Complete | 12h | HIGH |
| DynamoDB Backup | 🔄 In Progress | 14h | HIGH |
| API Throttling | 🔄 In Progress | 6h | HIGH |
| CloudFront CDN | 📋 Ready | 18h | HIGH |
| Model Versioning | 📋 Ready | 24h | HIGH |

**Total Completed:** 28 hours  
**Total Remaining:** 62 hours  
**Overall Progress:** 31%

---

## Next Steps

### This Week
1. ✅ Complete DynamoDB backup automation
2. ✅ Deploy API Gateway throttling
3. ✅ Test VPC Lambda deployment

### Next Week
1. Deploy CloudFront distribution
2. Implement model versioning
3. Security testing of all fixes

---

**Last Updated:** October 24, 2025  
**Next Review:** October 31, 2025
