#!/usr/bin/env python3
"""
Enhanced Consumer Ordering Stack Deployment Validation

This script validates that the Enhanced Consumer Ordering Stack has been deployed correctly
by checking AWS resources and their configurations.
"""

import boto3
import json
import sys
import time
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError


class EnhancedOrderingDeploymentValidator:
    """
    Validates Enhanced Consumer Ordering Stack deployment
    """
    
    def __init__(self, environment: str = "dev", region: str = "us-east-1"):
        """
        Initialize the validator
        
        Args:
            environment: Environment name (dev, staging, prod)
            region: AWS region
        """
        self.environment = environment
        self.region = region
        self.stack_name = f"AquaChain-EnhancedOrdering-{environment}"
        
        # Initialize AWS clients
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=region)
            self.lambda_client = boto3.client('lambda', region_name=region)
            self.events_client = boto3.client('events', region_name=region)
            self.apigatewayv2 = boto3.client('apigatewayv2', region_name=region)
            self.secretsmanager = boto3.client('secretsmanager', region_name=region)
            self.cloudformation = boto3.client('cloudformation', region_name=region)
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error initializing AWS clients: {e}")
            sys.exit(1)
    
    def validate_stack_deployment(self) -> bool:
        """
        Validate that the CloudFormation stack exists and is in a good state
        
        Returns:
            True if stack is deployed successfully
        """
        print(f"🔍 Validating CloudFormation stack: {self.stack_name}")
        
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            stack = response['Stacks'][0]
            
            stack_status = stack['StackStatus']
            if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                print(f"❌ Stack status is {stack_status}, expected CREATE_COMPLETE or UPDATE_COMPLETE")
                return False
            
            print(f"✅ Stack {self.stack_name} is in {stack_status} state")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                print(f"❌ Stack {self.stack_name} does not exist")
            else:
                print(f"❌ Error checking stack: {e}")
            return False
    
    def validate_dynamodb_tables(self) -> bool:
        """
        Validate that all required DynamoDB tables exist with proper configuration
        
        Returns:
            True if all tables are configured correctly
        """
        print("🔍 Validating DynamoDB tables...")
        
        expected_tables = [
            f"aquachain-table-orders-{self.environment}",
            f"aquachain-table-payments-{self.environment}",
            f"aquachain-table-technicians-{self.environment}",
            f"aquachain-table-order-simulations-{self.environment}",
            f"aquachain-table-websocket-connections-{self.environment}"
        ]
        
        validation_results = []
        
        for table_name in expected_tables:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                table = response['Table']
                
                # Check table status
                if table['TableStatus'] != 'ACTIVE':
                    print(f"❌ Table {table_name} is not ACTIVE (status: {table['TableStatus']})")
                    validation_results.append(False)
                    continue
                
                # Check billing mode
                if table['BillingModeSummary']['BillingMode'] != 'PAY_PER_REQUEST':
                    print(f"❌ Table {table_name} is not using PAY_PER_REQUEST billing")
                    validation_results.append(False)
                    continue
                
                # Check encryption
                if 'SSEDescription' not in table or table['SSEDescription']['Status'] != 'ENABLED':
                    print(f"❌ Table {table_name} does not have encryption enabled")
                    validation_results.append(False)
                    continue
                
                # Check specific table configurations
                if 'orders' in table_name:
                    # Orders table should have 2 GSIs and TTL
                    if len(table.get('GlobalSecondaryIndexes', [])) != 2:
                        print(f"❌ Orders table should have 2 GSIs, found {len(table.get('GlobalSecondaryIndexes', []))}")
                        validation_results.append(False)
                        continue
                    
                    if table.get('TimeToLiveDescription', {}).get('TimeToLiveStatus') != 'ENABLED':
                        print(f"❌ Orders table should have TTL enabled")
                        validation_results.append(False)
                        continue
                
                elif 'payments' in table_name:
                    # Payments table should have 1 GSI
                    if len(table.get('GlobalSecondaryIndexes', [])) != 1:
                        print(f"❌ Payments table should have 1 GSI, found {len(table.get('GlobalSecondaryIndexes', []))}")
                        validation_results.append(False)
                        continue
                
                elif 'technicians' in table_name:
                    # Technicians table should have 1 GSI
                    if len(table.get('GlobalSecondaryIndexes', [])) != 1:
                        print(f"❌ Technicians table should have 1 GSI, found {len(table.get('GlobalSecondaryIndexes', []))}")
                        validation_results.append(False)
                        continue
                
                elif 'websocket-connections' in table_name:
                    # WebSocket connections table should have 1 GSI and TTL
                    if len(table.get('GlobalSecondaryIndexes', [])) != 1:
                        print(f"❌ WebSocket connections table should have 1 GSI, found {len(table.get('GlobalSecondaryIndexes', []))}")
                        validation_results.append(False)
                        continue
                    
                    if table.get('TimeToLiveDescription', {}).get('TimeToLiveStatus') != 'ENABLED':
                        print(f"❌ WebSocket connections table should have TTL enabled")
                        validation_results.append(False)
                        continue
                
                print(f"✅ Table {table_name} is configured correctly")
                validation_results.append(True)
                
            except ClientError as e:
                print(f"❌ Error checking table {table_name}: {e}")
                validation_results.append(False)
        
        return all(validation_results)
    
    def validate_lambda_functions(self) -> bool:
        """
        Validate that all required Lambda functions exist with proper configuration
        
        Returns:
            True if all functions are configured correctly
        """
        print("🔍 Validating Lambda functions...")
        
        expected_functions = [
            f"aquachain-function-order-management-{self.environment}",
            f"aquachain-function-payment-service-{self.environment}",
            f"aquachain-function-technician-assignment-{self.environment}",
            f"aquachain-function-status-simulator-{self.environment}",
            f"aquachain-function-websocket-connect-{self.environment}",
            f"aquachain-function-websocket-disconnect-{self.environment}",
            f"aquachain-function-websocket-broadcast-{self.environment}"
        ]
        
        validation_results = []
        
        for function_name in expected_functions:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_config = response['Configuration']
                
                # Check runtime
                if function_config['Runtime'] != 'python3.11':
                    print(f"❌ Function {function_name} should use python3.11 runtime")
                    validation_results.append(False)
                    continue
                
                # Check timeout
                if function_config['Timeout'] != 30:
                    print(f"❌ Function {function_name} should have 30 second timeout")
                    validation_results.append(False)
                    continue
                
                # Check memory size
                if function_config['MemorySize'] != 512:
                    print(f"❌ Function {function_name} should have 512 MB memory")
                    validation_results.append(False)
                    continue
                
                # Check tracing
                if function_config.get('TracingConfig', {}).get('Mode') != 'Active':
                    print(f"❌ Function {function_name} should have X-Ray tracing enabled")
                    validation_results.append(False)
                    continue
                
                # Check environment variables
                env_vars = function_config.get('Environment', {}).get('Variables', {})
                required_env_vars = [
                    'ENVIRONMENT',
                    'REGION',
                    'ORDERS_TABLE_NAME',
                    'PAYMENTS_TABLE_NAME',
                    'TECHNICIANS_TABLE_NAME',
                    'ORDER_SIMULATIONS_TABLE_NAME'
                ]
                
                missing_vars = [var for var in required_env_vars if var not in env_vars]
                if missing_vars:
                    print(f"❌ Function {function_name} missing environment variables: {missing_vars}")
                    validation_results.append(False)
                    continue
                
                print(f"✅ Function {function_name} is configured correctly")
                validation_results.append(True)
                
            except ClientError as e:
                print(f"❌ Error checking function {function_name}: {e}")
                validation_results.append(False)
        
        return all(validation_results)
    
    def validate_eventbridge_resources(self) -> bool:
        """
        Validate EventBridge resources
        
        Returns:
            True if EventBridge resources are configured correctly
        """
        print("🔍 Validating EventBridge resources...")
        
        validation_results = []
        
        # Check custom event bus
        event_bus_name = f"aquachain-event-bus-ordering-{self.environment}"
        try:
            response = self.events_client.describe_event_bus(Name=event_bus_name)
            print(f"✅ Event bus {event_bus_name} exists")
            validation_results.append(True)
        except ClientError as e:
            print(f"❌ Error checking event bus {event_bus_name}: {e}")
            validation_results.append(False)
        
        # Check EventBridge rules
        expected_rules = [
            f"aquachain-rule-status-simulation-{self.environment}",
            f"aquachain-rule-order-status-update-{self.environment}"
        ]
        
        for rule_name in expected_rules:
            try:
                response = self.events_client.describe_rule(
                    Name=rule_name,
                    EventBusName=event_bus_name
                )
                
                if response['State'] != 'ENABLED':
                    print(f"❌ Rule {rule_name} is not enabled")
                    validation_results.append(False)
                    continue
                
                # Check rule has targets
                targets_response = self.events_client.list_targets_by_rule(
                    Rule=rule_name,
                    EventBusName=event_bus_name
                )
                
                if not targets_response['Targets']:
                    print(f"❌ Rule {rule_name} has no targets")
                    validation_results.append(False)
                    continue
                
                print(f"✅ Rule {rule_name} is configured correctly")
                validation_results.append(True)
                
            except ClientError as e:
                print(f"❌ Error checking rule {rule_name}: {e}")
                validation_results.append(False)
        
        return all(validation_results)
    
    def validate_websocket_api(self) -> bool:
        """
        Validate WebSocket API configuration
        
        Returns:
            True if WebSocket API is configured correctly
        """
        print("🔍 Validating WebSocket API...")
        
        try:
            # List APIs to find the ordering WebSocket API
            response = self.apigatewayv2.get_apis()
            ordering_api = None
            
            for api in response['Items']:
                if (api['ProtocolType'] == 'WEBSOCKET' and 
                    'ordering' in api['Name'].lower() and 
                    self.environment in api['Name']):
                    ordering_api = api
                    break
            
            if not ordering_api:
                print("❌ WebSocket API for ordering not found")
                return False
            
            api_id = ordering_api['ApiId']
            
            # Check API stage
            stages_response = self.apigatewayv2.get_stages(ApiId=api_id)
            stage_found = False
            
            for stage in stages_response['Items']:
                if stage['StageName'] == self.environment:
                    stage_found = True
                    if not stage.get('AutoDeploy', False):
                        print(f"❌ WebSocket API stage {self.environment} should have auto-deploy enabled")
                        return False
                    break
            
            if not stage_found:
                print(f"❌ WebSocket API stage {self.environment} not found")
                return False
            
            # Check routes
            routes_response = self.apigatewayv2.get_routes(ApiId=api_id)
            route_keys = [route['RouteKey'] for route in routes_response['Items']]
            
            expected_routes = ['$connect', '$disconnect']
            missing_routes = [route for route in expected_routes if route not in route_keys]
            
            if missing_routes:
                print(f"❌ WebSocket API missing routes: {missing_routes}")
                return False
            
            print(f"✅ WebSocket API {ordering_api['Name']} is configured correctly")
            return True
            
        except ClientError as e:
            print(f"❌ Error checking WebSocket API: {e}")
            return False
    
    def validate_secrets_manager(self) -> bool:
        """
        Validate Secrets Manager configuration
        
        Returns:
            True if secrets are configured correctly
        """
        print("🔍 Validating Secrets Manager...")
        
        secret_name = f"aquachain-secret-razorpay-credentials-{self.environment}"
        
        try:
            response = self.secretsmanager.describe_secret(SecretId=secret_name)
            
            # Check encryption
            if 'KmsKeyId' not in response:
                print(f"❌ Secret {secret_name} should be encrypted with KMS")
                return False
            
            print(f"✅ Secret {secret_name} is configured correctly")
            return True
            
        except ClientError as e:
            print(f"❌ Error checking secret {secret_name}: {e}")
            return False
    
    def run_validation(self) -> bool:
        """
        Run complete validation suite
        
        Returns:
            True if all validations pass
        """
        print(f"🚀 Starting Enhanced Consumer Ordering Stack validation for {self.environment} environment")
        print("=" * 80)
        
        validations = [
            ("CloudFormation Stack", self.validate_stack_deployment),
            ("DynamoDB Tables", self.validate_dynamodb_tables),
            ("Lambda Functions", self.validate_lambda_functions),
            ("EventBridge Resources", self.validate_eventbridge_resources),
            ("WebSocket API", self.validate_websocket_api),
            ("Secrets Manager", self.validate_secrets_manager)
        ]
        
        results = []
        
        for validation_name, validation_func in validations:
            print(f"\n📋 {validation_name}")
            print("-" * 40)
            
            try:
                result = validation_func()
                results.append(result)
                
                if result:
                    print(f"✅ {validation_name} validation passed")
                else:
                    print(f"❌ {validation_name} validation failed")
                    
            except Exception as e:
                print(f"❌ {validation_name} validation error: {e}")
                results.append(False)
        
        print("\n" + "=" * 80)
        
        if all(results):
            print("🎉 All validations passed! Enhanced Consumer Ordering Stack is deployed correctly.")
            return True
        else:
            failed_count = len([r for r in results if not r])
            print(f"❌ {failed_count} validation(s) failed. Please check the deployment.")
            return False


def main():
    """
    Main function to run validation
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Enhanced Consumer Ordering Stack deployment")
    parser.add_argument("--environment", "-e", default="dev", 
                       help="Environment to validate (dev, staging, prod)")
    parser.add_argument("--region", "-r", default="us-east-1",
                       help="AWS region")
    
    args = parser.parse_args()
    
    validator = EnhancedOrderingDeploymentValidator(
        environment=args.environment,
        region=args.region
    )
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()