#!/usr/bin/env python3
"""
Infrastructure validation script for AquaChain CDK deployment
"""

import boto3
import json
import time
import sys
from typing import Dict, List, Any, Tuple
from botocore.exceptions import ClientError, NoCredentialsError

class AquaChainInfrastructureValidator:
    """
    Validates deployed AquaChain infrastructure
    """
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=region)
            self.s3 = boto3.client('s3', region_name=region)
            self.lambda_client = boto3.client('lambda', region_name=region)
            self.apigateway = boto3.client('apigateway', region_name=region)
            self.cognito = boto3.client('cognito-idp', region_name=region)
            self.iot = boto3.client('iot', region_name=region)
            self.kms = boto3.client('kms', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.sns = boto3.client('sns', region_name=region)
            
        except NoCredentialsError:
            print("Error: AWS credentials not configured")
            sys.exit(1)
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks
        """
        print(f"Validating AquaChain infrastructure for environment: {self.environment}")
        print("=" * 70)
        
        results = {
            "environment": self.environment,
            "region": self.region,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "validations": {}
        }
        
        # Run validation checks
        validation_checks = [
            ("DynamoDB Tables", self.validate_dynamodb_tables),
            ("S3 Buckets", self.validate_s3_buckets),
            ("Lambda Functions", self.validate_lambda_functions),
            ("API Gateway", self.validate_api_gateway),
            ("Cognito User Pool", self.validate_cognito),
            ("IoT Core", self.validate_iot_core),
            ("KMS Keys", self.validate_kms_keys),
            ("CloudWatch Resources", self.validate_cloudwatch),
            ("SNS Topics", self.validate_sns_topics)
        ]
        
        overall_success = True
        
        for check_name, check_function in validation_checks:
            print(f"\n{check_name}:")
            print("-" * 40)
            
            try:
                success, details = check_function()
                results["validations"][check_name.lower().replace(" ", "_")] = {
                    "success": success,
                    "details": details
                }
                
                if success:
                    print(f"✓ {check_name} validation passed")
                else:
                    print(f"✗ {check_name} validation failed")
                    overall_success = False
                    
            except Exception as e:
                print(f"✗ {check_name} validation error: {e}")
                results["validations"][check_name.lower().replace(" ", "_")] = {
                    "success": False,
                    "error": str(e)
                }
                overall_success = False
        
        results["overall_success"] = overall_success
        
        print("\n" + "=" * 70)
        if overall_success:
            print("✓ All infrastructure validations passed")
        else:
            print("✗ Some infrastructure validations failed")
        
        return results
    
    def validate_dynamodb_tables(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate DynamoDB tables exist and are configured correctly
        """
        expected_tables = [
            f"aquachain-table-readings-{self.environment}",
            f"aquachain-table-ledger-{self.environment}",
            f"aquachain-table-sequence-{self.environment}",
            f"aquachain-table-users-{self.environment}",
            f"aquachain-table-service-requests-{self.environment}"
        ]
        
        details = {"tables": {}}
        success = True
        
        for table_name in expected_tables:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                table_status = response['Table']['TableStatus']
                
                details["tables"][table_name] = {
                    "status": table_status,
                    "encryption": response['Table'].get('SSEDescription', {}).get('Status', 'DISABLED'),
                    "streams": 'StreamSpecification' in response['Table'],
                    "billing_mode": response['Table']['BillingModeSummary']['BillingMode']
                }
                
                if table_status != 'ACTIVE':
                    success = False
                    print(f"  ✗ Table {table_name} is not ACTIVE (status: {table_status})")
                else:
                    print(f"  ✓ Table {table_name} is ACTIVE")
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"  ✗ Table {table_name} not found")
                    details["tables"][table_name] = {"status": "NOT_FOUND"}
                    success = False
                else:
                    raise e
        
        return success, details
    
    def validate_s3_buckets(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate S3 buckets exist and are configured correctly
        """
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        expected_buckets = [
            f"aquachain-bucket-data-lake-{self.environment}-{account_id}",
            f"aquachain-bucket-audit-trail-{self.environment}-{account_id}",
            f"aquachain-bucket-ml-models-{self.environment}-{account_id}"
        ]
        
        details = {"buckets": {}}
        success = True
        
        for bucket_name in expected_buckets:
            try:
                # Check if bucket exists
                self.s3.head_bucket(Bucket=bucket_name)
                
                # Check encryption
                try:
                    encryption = self.s3.get_bucket_encryption(Bucket=bucket_name)
                    encryption_status = "ENABLED"
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        encryption_status = "DISABLED"
                    else:
                        encryption_status = "UNKNOWN"
                
                # Check versioning
                versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
                versioning_status = versioning.get('Status', 'Disabled')
                
                # Check Object Lock (for audit bucket)
                object_lock_status = "N/A"
                if "audit-trail" in bucket_name:
                    try:
                        object_lock = self.s3.get_object_lock_configuration(Bucket=bucket_name)
                        object_lock_status = "ENABLED"
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'ObjectLockConfigurationNotFoundError':
                            object_lock_status = "DISABLED"
                
                details["buckets"][bucket_name] = {
                    "exists": True,
                    "encryption": encryption_status,
                    "versioning": versioning_status,
                    "object_lock": object_lock_status
                }
                
                print(f"  ✓ Bucket {bucket_name} exists and is configured")
                
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print(f"  ✗ Bucket {bucket_name} not found")
                    details["buckets"][bucket_name] = {"exists": False}
                    success = False
                else:
                    raise e
        
        return success, details
    
    def validate_lambda_functions(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate Lambda functions exist and are configured correctly
        """
        expected_functions = [
            f"aquachain-function-data-processing-{self.environment}",
            f"aquachain-function-ml-inference-{self.environment}",
            f"aquachain-function-alert-detection-{self.environment}",
            f"aquachain-function-user-management-{self.environment}",
            f"aquachain-function-service-request-{self.environment}",
            f"aquachain-function-audit-processor-{self.environment}",
            f"aquachain-function-websocket-{self.environment}",
            f"aquachain-function-notification-{self.environment}"
        ]
        
        details = {"functions": {}}
        success = True
        
        for function_name in expected_functions:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                
                config = response['Configuration']
                details["functions"][function_name] = {
                    "state": config['State'],
                    "runtime": config['Runtime'],
                    "timeout": config['Timeout'],
                    "memory_size": config['MemorySize'],
                    "tracing": config.get('TracingConfig', {}).get('Mode', 'PassThrough')
                }
                
                if config['State'] != 'Active':
                    success = False
                    print(f"  ✗ Function {function_name} is not Active (state: {config['State']})")
                else:
                    print(f"  ✓ Function {function_name} is Active")
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"  ✗ Function {function_name} not found")
                    details["functions"][function_name] = {"state": "NOT_FOUND"}
                    success = False
                else:
                    raise e
        
        return success, details
    
    def validate_api_gateway(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate API Gateway is configured correctly
        """
        details = {"apis": {}}
        success = True
        
        try:
            # Get REST APIs
            apis = self.apigateway.get_rest_apis()
            
            api_name = f"aquachain-api-rest-{self.environment}"
            api_found = False
            
            for api in apis['items']:
                if api['name'] == api_name:
                    api_found = True
                    api_id = api['id']
                    
                    # Get stages
                    stages = self.apigateway.get_stages(restApiId=api_id)
                    
                    details["apis"][api_name] = {
                        "id": api_id,
                        "name": api['name'],
                        "stages": [stage['stageName'] for stage in stages['item']]
                    }
                    
                    print(f"  ✓ REST API {api_name} found with stages: {details['apis'][api_name]['stages']}")
                    break
            
            if not api_found:
                print(f"  ✗ REST API {api_name} not found")
                success = False
                
        except ClientError as e:
            print(f"  ✗ Error validating API Gateway: {e}")
            success = False
        
        return success, details
    
    def validate_cognito(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate Cognito User Pool is configured correctly
        """
        details = {"user_pools": {}}
        success = True
        
        try:
            user_pools = self.cognito.list_user_pools(MaxResults=50)
            
            pool_name = f"aquachain-pool-users-{self.environment}"
            pool_found = False
            
            for pool in user_pools['UserPools']:
                if pool['Name'] == pool_name:
                    pool_found = True
                    pool_id = pool['Id']
                    
                    # Get pool details
                    pool_details = self.cognito.describe_user_pool(UserPoolId=pool_id)
                    
                    details["user_pools"][pool_name] = {
                        "id": pool_id,
                        "status": pool_details['UserPool']['Status'],
                        "mfa_configuration": pool_details['UserPool']['MfaConfiguration'],
                        "auto_verified_attributes": pool_details['UserPool'].get('AutoVerifiedAttributes', [])
                    }
                    
                    print(f"  ✓ User Pool {pool_name} found and configured")
                    break
            
            if not pool_found:
                print(f"  ✗ User Pool {pool_name} not found")
                success = False
                
        except ClientError as e:
            print(f"  ✗ Error validating Cognito: {e}")
            success = False
        
        return success, details
    
    def validate_iot_core(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate IoT Core resources are configured correctly
        """
        details = {"iot_resources": {}}
        success = True
        
        try:
            # Check Thing Types
            thing_types = self.iot.list_thing_types()
            
            expected_thing_type = f"aquachain-thing-type-device-{self.environment}"
            thing_type_found = False
            
            for thing_type in thing_types['thingTypes']:
                if thing_type['thingTypeName'] == expected_thing_type:
                    thing_type_found = True
                    details["iot_resources"]["thing_type"] = {
                        "name": thing_type['thingTypeName'],
                        "description": thing_type.get('thingTypeDescription', '')
                    }
                    print(f"  ✓ Thing Type {expected_thing_type} found")
                    break
            
            if not thing_type_found:
                print(f"  ✗ Thing Type {expected_thing_type} not found")
                success = False
            
            # Check Topic Rules
            topic_rules = self.iot.list_topic_rules()
            
            expected_rule = f"aquachain_rule_data_processing_{self.environment}"
            rule_found = False
            
            for rule in topic_rules['rules']:
                if rule['ruleName'] == expected_rule:
                    rule_found = True
                    details["iot_resources"]["topic_rule"] = {
                        "name": rule['ruleName'],
                        "created_at": rule['createdAt'].isoformat()
                    }
                    print(f"  ✓ Topic Rule {expected_rule} found")
                    break
            
            if not rule_found:
                print(f"  ✗ Topic Rule {expected_rule} not found")
                success = False
                
        except ClientError as e:
            print(f"  ✗ Error validating IoT Core: {e}")
            success = False
        
        return success, details
    
    def validate_kms_keys(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate KMS keys exist and are configured correctly
        """
        details = {"kms_keys": {}}
        success = True
        
        try:
            # List KMS keys
            keys = self.kms.list_keys()
            
            expected_aliases = [
                f"alias/aquachain-kms-data-{self.environment}",
                f"alias/aquachain-kms-signing-{self.environment}",
                f"alias/aquachain-kms-iot-{self.environment}"
            ]
            
            # Get aliases
            aliases = self.kms.list_aliases()
            
            for expected_alias in expected_aliases:
                alias_found = False
                
                for alias in aliases['Aliases']:
                    if alias.get('AliasName') == expected_alias:
                        alias_found = True
                        
                        # Get key details
                        key_id = alias['TargetKeyId']
                        key_details = self.kms.describe_key(KeyId=key_id)
                        
                        details["kms_keys"][expected_alias] = {
                            "key_id": key_id,
                            "key_state": key_details['KeyMetadata']['KeyState'],
                            "key_usage": key_details['KeyMetadata']['KeyUsage'],
                            "enabled": key_details['KeyMetadata']['Enabled']
                        }
                        
                        print(f"  ✓ KMS Key {expected_alias} found and enabled")
                        break
                
                if not alias_found:
                    print(f"  ✗ KMS Key {expected_alias} not found")
                    success = False
                    
        except ClientError as e:
            print(f"  ✗ Error validating KMS keys: {e}")
            success = False
        
        return success, details
    
    def validate_cloudwatch(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate CloudWatch resources are configured correctly
        """
        details = {"cloudwatch": {}}
        success = True
        
        try:
            # Check dashboards
            dashboards = self.cloudwatch.list_dashboards()
            
            expected_dashboards = [
                f"aquachain-dashboard-system-{self.environment}",
                f"aquachain-dashboard-performance-{self.environment}"
            ]
            
            found_dashboards = []
            for dashboard in dashboards['DashboardEntries']:
                if dashboard['DashboardName'] in expected_dashboards:
                    found_dashboards.append(dashboard['DashboardName'])
                    print(f"  ✓ Dashboard {dashboard['DashboardName']} found")
            
            missing_dashboards = set(expected_dashboards) - set(found_dashboards)
            if missing_dashboards:
                print(f"  ✗ Missing dashboards: {missing_dashboards}")
                success = False
            
            details["cloudwatch"]["dashboards"] = {
                "expected": expected_dashboards,
                "found": found_dashboards,
                "missing": list(missing_dashboards)
            }
            
            # Check alarms
            alarms = self.cloudwatch.describe_alarms()
            
            aquachain_alarms = [
                alarm for alarm in alarms['MetricAlarms']
                if f"aquachain-alarm-" in alarm['AlarmName'] and self.environment in alarm['AlarmName']
            ]
            
            details["cloudwatch"]["alarms"] = {
                "count": len(aquachain_alarms),
                "names": [alarm['AlarmName'] for alarm in aquachain_alarms]
            }
            
            print(f"  ✓ Found {len(aquachain_alarms)} CloudWatch alarms")
            
        except ClientError as e:
            print(f"  ✗ Error validating CloudWatch: {e}")
            success = False
        
        return success, details
    
    def validate_sns_topics(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate SNS topics are configured correctly
        """
        details = {"sns_topics": {}}
        success = True
        
        try:
            topics = self.sns.list_topics()
            
            expected_topics = [
                f"aquachain-topic-critical-alerts-{self.environment}",
                f"aquachain-topic-service-updates-{self.environment}",
                f"aquachain-topic-system-alerts-{self.environment}"
            ]
            
            found_topics = []
            
            for topic in topics['Topics']:
                topic_arn = topic['TopicArn']
                topic_name = topic_arn.split(':')[-1]
                
                if topic_name in expected_topics:
                    found_topics.append(topic_name)
                    
                    # Get topic attributes
                    attributes = self.sns.get_topic_attributes(TopicArn=topic_arn)
                    
                    details["sns_topics"][topic_name] = {
                        "arn": topic_arn,
                        "subscriptions_confirmed": attributes['Attributes'].get('SubscriptionsConfirmed', '0'),
                        "subscriptions_pending": attributes['Attributes'].get('SubscriptionsPending', '0')
                    }
                    
                    print(f"  ✓ SNS Topic {topic_name} found")
            
            missing_topics = set(expected_topics) - set(found_topics)
            if missing_topics:
                print(f"  ✗ Missing SNS topics: {missing_topics}")
                success = False
                
        except ClientError as e:
            print(f"  ✗ Error validating SNS topics: {e}")
            success = False
        
        return success, details

def main():
    """
    Main validation script
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate AquaChain infrastructure")
    parser.add_argument("--environment", "-e", required=True,
                       choices=["dev", "staging", "prod"],
                       help="Environment to validate")
    parser.add_argument("--region", "-r", default="us-east-1",
                       help="AWS region")
    parser.add_argument("--output", "-o", 
                       help="Output file for validation results (JSON)")
    
    args = parser.parse_args()
    
    # Run validation
    validator = AquaChainInfrastructureValidator(args.environment, args.region)
    results = validator.validate_all()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nValidation results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()