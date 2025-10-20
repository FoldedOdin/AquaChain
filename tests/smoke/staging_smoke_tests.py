"""
Smoke tests for AquaChain staging environment
These tests verify basic functionality after deployment
"""

import requests
import boto3
import json
import time
import os
from datetime import datetime, timezone

# Configuration
STAGING_API_BASE_URL = os.getenv('STAGING_API_BASE_URL', 'https://api-staging.aquachain.io')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
ENVIRONMENT = 'staging'

class StagingSmokeTests:
    def __init__(self):
        self.api_base_url = STAGING_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AquaChain-SmokeTest/1.0'
        })
        
        # AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
        self.lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        self.s3 = boto3.client('s3', region_name=AWS_REGION)
        
    def run_all_tests(self):
        """Run all smoke tests."""
        print("🚀 Starting AquaChain Staging Smoke Tests")
        print(f"Environment: {ENVIRONMENT}")
        print(f"API Base URL: {self.api_base_url}")
        print(f"AWS Region: {AWS_REGION}")
        print("-" * 50)
        
        tests = [
            self.test_api_health_check,
            self.test_dynamodb_tables_exist,
            self.test_lambda_functions_deployed,
            self.test_s3_buckets_exist,
            self.test_api_authentication,
            self.test_data_processing_pipeline,
            self.test_notification_system,
            self.test_frontend_deployment
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                print(f"Running {test.__name__}...", end=" ")
                test()
                print("✅ PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ FAILED: {str(e)}")
                failed += 1
        
        print("-" * 50)
        print(f"Tests completed: {passed} passed, {failed} failed")
        
        if failed > 0:
            raise Exception(f"Smoke tests failed: {failed} test(s) failed")
        
        print("🎉 All smoke tests passed!")
    
    def test_api_health_check(self):
        """Test API health endpoint."""
        response = self.session.get(f"{self.api_base_url}/health")
        
        if response.status_code != 200:
            raise Exception(f"Health check failed with status {response.status_code}")
        
        health_data = response.json()
        if health_data.get('status') != 'healthy':
            raise Exception(f"API reports unhealthy status: {health_data}")
    
    def test_dynamodb_tables_exist(self):
        """Test that all required DynamoDB tables exist."""
        required_tables = [
            f'aquachain-readings-{ENVIRONMENT}',
            f'aquachain-ledger-{ENVIRONMENT}',
            f'aquachain-sequence-{ENVIRONMENT}',
            f'aquachain-users-{ENVIRONMENT}',
            f'aquachain-service-requests-{ENVIRONMENT}'
        ]
        
        existing_tables = self.dynamodb.list_tables()['TableNames']
        
        for table in required_tables:
            if table not in existing_tables:
                raise Exception(f"Required table {table} not found")
            
            # Check table status
            table_info = self.dynamodb.describe_table(TableName=table)
            if table_info['Table']['TableStatus'] != 'ACTIVE':
                raise Exception(f"Table {table} is not active")
    
    def test_lambda_functions_deployed(self):
        """Test that all Lambda functions are deployed and active."""
        required_functions = [
            f'AquaChain-data-processing-{ENVIRONMENT}',
            f'AquaChain-ml-inference-{ENVIRONMENT}',
            f'AquaChain-ledger-service-{ENVIRONMENT}',
            f'AquaChain-audit-trail-processor-{ENVIRONMENT}',
            f'AquaChain-alert-detection-{ENVIRONMENT}',
            f'AquaChain-notification-service-{ENVIRONMENT}',
            f'AquaChain-auth-service-{ENVIRONMENT}',
            f'AquaChain-user-management-{ENVIRONMENT}',
            f'AquaChain-technician-service-{ENVIRONMENT}',
            f'AquaChain-api-gateway-{ENVIRONMENT}',
            f'AquaChain-websocket-api-{ENVIRONMENT}'
        ]
        
        for function_name in required_functions:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                if response['Configuration']['State'] != 'Active':
                    raise Exception(f"Function {function_name} is not active")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                raise Exception(f"Function {function_name} not found")
    
    def test_s3_buckets_exist(self):
        """Test that all required S3 buckets exist."""
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        required_buckets = [
            f'aquachain-data-lake-{ENVIRONMENT}-{account_id}',
            f'aquachain-audit-trail-{ENVIRONMENT}-{account_id}',
            f'aquachain-frontend-{ENVIRONMENT}-{account_id}'
        ]
        
        for bucket_name in required_buckets:
            try:
                self.s3.head_bucket(Bucket=bucket_name)
            except Exception:
                raise Exception(f"Bucket {bucket_name} not found or not accessible")
    
    def test_api_authentication(self):
        """Test API authentication endpoints."""
        # Test unauthenticated request (should fail)
        response = self.session.get(f"{self.api_base_url}/api/v1/readings/test-device")
        
        if response.status_code not in [401, 403]:
            raise Exception(f"Unauthenticated request should return 401/403, got {response.status_code}")
        
        # Test authentication endpoint exists
        auth_response = self.session.post(f"{self.api_base_url}/auth/login", json={
            "email": "test@example.com",
            "password": "invalid"
        })
        
        # Should return 400/401 for invalid credentials, not 500
        if auth_response.status_code >= 500:
            raise Exception(f"Auth endpoint returned server error: {auth_response.status_code}")
    
    def test_data_processing_pipeline(self):
        """Test data processing pipeline with synthetic data."""
        # Create test IoT message
        test_message = {
            "deviceId": "SMOKE-TEST-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 9.9312,
                "longitude": 76.2673
            },
            "readings": {
                "pH": 7.2,
                "turbidity": 1.5,
                "tds": 145,
                "temperature": 24.5,
                "humidity": 68.2
            },
            "diagnostics": {
                "batteryLevel": 85,
                "signalStrength": -65,
                "sensorStatus": "normal"
            }
        }
        
        # Invoke data processing function directly
        function_name = f'AquaChain-data-processing-{ENVIRONMENT}'
        
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_message)
        )
        
        if response['StatusCode'] != 200:
            raise Exception(f"Data processing function failed with status {response['StatusCode']}")
        
        # Check for errors in response
        payload = json.loads(response['Payload'].read())
        if 'errorMessage' in payload:
            raise Exception(f"Data processing function error: {payload['errorMessage']}")
    
    def test_notification_system(self):
        """Test notification system functionality."""
        # Test SNS topic exists
        sns = boto3.client('sns', region_name=AWS_REGION)
        
        try:
            topics = sns.list_topics()['Topics']
            critical_alerts_topic = None
            
            for topic in topics:
                if f'aquachain-critical-alerts-{ENVIRONMENT}' in topic['TopicArn']:
                    critical_alerts_topic = topic['TopicArn']
                    break
            
            if not critical_alerts_topic:
                raise Exception("Critical alerts SNS topic not found")
            
            # Test topic attributes
            attrs = sns.get_topic_attributes(TopicArn=critical_alerts_topic)
            if not attrs['Attributes']:
                raise Exception("SNS topic has no attributes")
                
        except Exception as e:
            raise Exception(f"Notification system test failed: {str(e)}")
    
    def test_frontend_deployment(self):
        """Test frontend deployment."""
        # Test if frontend is accessible
        frontend_url = f"https://app-{ENVIRONMENT}.aquachain.io"
        
        try:
            response = self.session.get(frontend_url, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"Frontend not accessible: {response.status_code}")
            
            # Check if it's actually the React app (look for React-specific content)
            content = response.text.lower()
            if 'react' not in content and 'aquachain' not in content:
                raise Exception("Frontend doesn't appear to be the AquaChain React app")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Frontend accessibility test failed: {str(e)}")

def main():
    """Main function to run smoke tests."""
    try:
        smoke_tests = StagingSmokeTests()
        smoke_tests.run_all_tests()
        return 0
    except Exception as e:
        print(f"💥 Smoke tests failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())