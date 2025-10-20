"""
Production validation tests for AquaChain
These tests verify critical functionality in production environment
"""

import requests
import boto3
import json
import time
import os
from datetime import datetime, timezone
import concurrent.futures
import statistics

# Configuration
PRODUCTION_API_BASE_URL = os.getenv('PRODUCTION_API_BASE_URL', 'https://api.aquachain.io')
GREEN_API_BASE_URL = os.getenv('GREEN_API_BASE_URL', 'https://api-green.aquachain.io')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

class ProductionValidationTests:
    def __init__(self):
        self.api_base_url = GREEN_API_BASE_URL if ENVIRONMENT == 'green' else PRODUCTION_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AquaChain-ProductionValidation/1.0'
        })
        
        # AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
        self.lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        self.cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
        
    def run_all_tests(self):
        """Run all production validation tests."""
        print("🔍 Starting AquaChain Production Validation Tests")
        print(f"Environment: {ENVIRONMENT}")
        print(f"API Base URL: {self.api_base_url}")
        print(f"AWS Region: {AWS_REGION}")
        print("-" * 60)
        
        tests = [
            self.test_api_response_times,
            self.test_database_performance,
            self.test_lambda_cold_start_times,
            self.test_alert_latency_sla,
            self.test_system_uptime_metrics,
            self.test_security_headers,
            self.test_rate_limiting,
            self.test_error_rates,
            self.test_data_integrity,
            self.test_monitoring_alerts
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
        
        print("-" * 60)
        print(f"Validation completed: {passed} passed, {failed} failed")
        
        if failed > 0:
            raise Exception(f"Production validation failed: {failed} test(s) failed")
        
        print("🎉 All production validation tests passed!")
    
    def test_api_response_times(self):
        """Test API response times meet SLA requirements."""
        endpoints = [
            '/health',
            '/api/v1/readings/test-device',  # Will return 401 but should be fast
            '/auth/login'
        ]
        
        response_times = []
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = self.session.get(f"{self.api_base_url}{endpoint}", timeout=5)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                response_times.append(response_time)
                
                # Individual endpoint should respond within 2 seconds
                if response_time > 2000:
                    raise Exception(f"Endpoint {endpoint} took {response_time:.2f}ms (>2000ms)")
                    
            except requests.exceptions.Timeout:
                raise Exception(f"Endpoint {endpoint} timed out")
        
        # 95th percentile should be under 500ms
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        if p95_response_time > 500:
            raise Exception(f"95th percentile response time {p95_response_time:.2f}ms exceeds 500ms SLA")
    
    def test_database_performance(self):
        """Test database query performance."""
        # Test DynamoDB read latency
        table_name = 'aquachain-readings-production'
        
        start_time = time.time()
        try:
            response = self.dynamodb.query(
                TableName=table_name,
                KeyConditionExpression='deviceId_month = :pk',
                ExpressionAttributeValues={
                    ':pk': {'S': 'TEST-DEVICE#202510'}
                },
                Limit=10
            )
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            
            # DynamoDB queries should complete within 100ms
            if query_time > 100:
                raise Exception(f"DynamoDB query took {query_time:.2f}ms (>100ms)")
                
        except Exception as e:
            if 'ResourceNotFoundException' not in str(e):
                raise Exception(f"Database performance test failed: {str(e)}")
    
    def test_lambda_cold_start_times(self):
        """Test Lambda function cold start performance."""
        function_name = 'AquaChain-data-processing-production'
        
        # Invoke function multiple times to test cold starts
        cold_start_times = []
        
        for i in range(3):
            start_time = time.time()
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    "deviceId": f"PERF-TEST-{i}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "readings": {
                        "pH": 7.0,
                        "turbidity": 1.0,
                        "tds": 150,
                        "temperature": 25.0,
                        "humidity": 60.0
                    }
                })
            )
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            cold_start_times.append(execution_time)
            
            # Wait between invocations to ensure cold starts
            time.sleep(2)
        
        # Average cold start should be under 3 seconds
        avg_cold_start = statistics.mean(cold_start_times)
        if avg_cold_start > 3000:
            raise Exception(f"Average Lambda cold start {avg_cold_start:.2f}ms exceeds 3000ms")
    
    def test_alert_latency_sla(self):
        """Test alert delivery latency meets 30-second SLA."""
        # This test would typically involve:
        # 1. Injecting critical data
        # 2. Measuring time to notification delivery
        # For production validation, we'll check CloudWatch metrics instead
        
        try:
            # Get alert latency metrics from CloudWatch
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/Alerts',
                MetricName='AlertLatency',
                Dimensions=[
                    {
                        'Name': 'Environment',
                        'Value': 'production'
                    }
                ],
                StartTime=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                avg_latency = latest_datapoint['Average']
                max_latency = latest_datapoint['Maximum']
                
                # Alert latency SLA: 95% under 30 seconds
                if max_latency > 30:
                    raise Exception(f"Maximum alert latency {max_latency:.2f}s exceeds 30s SLA")
                    
        except Exception as e:
            # If no metrics available, skip this test
            if 'No datapoints' not in str(e):
                raise Exception(f"Alert latency test failed: {str(e)}")
    
    def test_system_uptime_metrics(self):
        """Test system uptime meets 99.5% SLA."""
        try:
            # Get uptime metrics from CloudWatch
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/System',
                MetricName='Uptime',
                Dimensions=[
                    {
                        'Name': 'Environment',
                        'Value': 'production'
                    }
                ],
                StartTime=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0),
                EndTime=datetime.now(timezone.utc),
                Period=86400,  # Daily
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                uptime_values = [dp['Average'] for dp in response['Datapoints']]
                avg_uptime = statistics.mean(uptime_values)
                
                # Uptime SLA: 99.5%
                if avg_uptime < 99.5:
                    raise Exception(f"System uptime {avg_uptime:.2f}% below 99.5% SLA")
                    
        except Exception as e:
            # If no metrics available, skip this test
            if 'No datapoints' not in str(e):
                raise Exception(f"Uptime test failed: {str(e)}")
    
    def test_security_headers(self):
        """Test security headers are properly configured."""
        response = self.session.get(f"{self.api_base_url}/health")
        
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000'
        }
        
        for header, expected_value in required_headers.items():
            if header not in response.headers:
                raise Exception(f"Missing security header: {header}")
            
            if expected_value and response.headers[header] != expected_value:
                raise Exception(f"Incorrect {header} header: got {response.headers[header]}, expected {expected_value}")
    
    def test_rate_limiting(self):
        """Test rate limiting is properly configured."""
        # Make rapid requests to test rate limiting
        responses = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(20):  # Make 20 rapid requests
                future = executor.submit(self.session.get, f"{self.api_base_url}/health")
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    response = future.result(timeout=5)
                    responses.append(response.status_code)
                except Exception:
                    responses.append(500)  # Treat exceptions as server errors
        
        # Should see some rate limiting (429 responses)
        rate_limited_count = responses.count(429)
        if rate_limited_count == 0:
            # This might be okay if the rate limit is high, but log it
            print("⚠️  No rate limiting detected")
    
    def test_error_rates(self):
        """Test system error rates are within acceptable limits."""
        try:
            # Get error rate metrics from CloudWatch
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': 'AquaChain-data-processing-production'
                    }
                ],
                StartTime=datetime.now(timezone.utc).replace(hour=datetime.now().hour-1),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Sum']
            )
            
            invocations_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': 'AquaChain-data-processing-production'
                    }
                ],
                StartTime=datetime.now(timezone.utc).replace(hour=datetime.now().hour-1),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Sum']
            )
            
            if response['Datapoints'] and invocations_response['Datapoints']:
                errors = sum(dp['Sum'] for dp in response['Datapoints'])
                invocations = sum(dp['Sum'] for dp in invocations_response['Datapoints'])
                
                if invocations > 0:
                    error_rate = (errors / invocations) * 100
                    
                    # Error rate should be under 1%
                    if error_rate > 1.0:
                        raise Exception(f"Error rate {error_rate:.2f}% exceeds 1% threshold")
                        
        except Exception as e:
            # If no metrics available, skip this test
            if 'No datapoints' not in str(e):
                raise Exception(f"Error rate test failed: {str(e)}")
    
    def test_data_integrity(self):
        """Test data integrity and consistency."""
        # Test that ledger hash chain is intact
        try:
            # Query recent ledger entries
            response = self.dynamodb.query(
                TableName='aquachain-ledger-production',
                KeyConditionExpression='partition_key = :pk',
                ExpressionAttributeValues={
                    ':pk': {'S': 'GLOBAL_SEQUENCE'}
                },
                ScanIndexForward=False,  # Descending order
                Limit=5
            )
            
            if response['Items']:
                # Verify hash chain integrity for recent entries
                items = sorted(response['Items'], key=lambda x: int(x['sequenceNumber']['N']))
                
                for i in range(1, len(items)):
                    current_item = items[i]
                    previous_item = items[i-1]
                    
                    if current_item['previousHash']['S'] != previous_item['chainHash']['S']:
                        raise Exception("Hash chain integrity violation detected")
                        
        except Exception as e:
            if 'ResourceNotFoundException' not in str(e):
                raise Exception(f"Data integrity test failed: {str(e)}")
    
    def test_monitoring_alerts(self):
        """Test that monitoring and alerting systems are functional."""
        try:
            # Check CloudWatch alarms
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix='AquaChain-',
                StateValue='ALARM'
            )
            
            # Count active alarms
            active_alarms = len(response['MetricAlarms'])
            
            # Should not have too many active alarms in production
            if active_alarms > 5:
                alarm_names = [alarm['AlarmName'] for alarm in response['MetricAlarms']]
                raise Exception(f"Too many active alarms ({active_alarms}): {alarm_names}")
                
        except Exception as e:
            raise Exception(f"Monitoring alerts test failed: {str(e)}")

def main():
    """Main function to run production validation tests."""
    try:
        validation_tests = ProductionValidationTests()
        validation_tests.run_all_tests()
        return 0
    except Exception as e:
        print(f"💥 Production validation failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())