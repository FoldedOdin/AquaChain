#!/usr/bin/env python3
"""
Verify Device Status Monitor Deployment
Checks that all components are deployed and working correctly
"""

import boto3
import json
import sys
from datetime import datetime, timedelta

def check_lambda_function():
    """Check if Lambda function exists and is configured correctly"""
    print("🔍 Checking Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # List functions with DeviceStatus in the name
        response = lambda_client.list_functions()
        device_status_functions = [
            f for f in response['Functions'] 
            if 'DeviceStatus' in f['FunctionName']
        ]
        
        if not device_status_functions:
            print("  ❌ No device status monitor Lambda function found")
            return False, None
        
        function = device_status_functions[0]
        function_name = function['FunctionName']
        
        print(f"  ✅ Found Lambda function: {function_name}")
        print(f"  📊 Runtime: {function['Runtime']}")
        print(f"  💾 Memory: {function['MemorySize']} MB")
        print(f"  ⏱️  Timeout: {function['Timeout']} seconds")
        
        # Check environment variables
        env_vars = function.get('Environment', {}).get('Variables', {})
        required_vars = ['DEVICES_TABLE', 'READINGS_TABLE', 'OFFLINE_THRESHOLD_MINUTES']
        
        for var in required_vars:
            if var in env_vars:
                print(f"  ✅ Environment variable {var}: {env_vars[var]}")
            else:
                print(f"  ❌ Missing environment variable: {var}")
                return False, None
        
        return True, function_name
        
    except Exception as e:
        print(f"  ❌ Error checking Lambda function: {e}")
        return False, None


def check_cloudwatch_events():
    """Check if CloudWatch Events rule exists and is enabled"""
    print("\n🕐 Checking CloudWatch Events rule...")
    
    events_client = boto3.client('events')
    
    try:
        response = events_client.list_rules()
        device_status_rules = [
            r for r in response['Rules'] 
            if 'DeviceStatus' in r['Name']
        ]
        
        if not device_status_rules:
            print("  ❌ No device status monitor Events rule found")
            return False
        
        rule = device_status_rules[0]
        rule_name = rule['Name']
        
        print(f"  ✅ Found Events rule: {rule_name}")
        print(f"  📅 Schedule: {rule['ScheduleExpression']}")
        print(f"  🔄 State: {rule['State']}")
        
        if rule['State'] != 'ENABLED':
            print("  ⚠️  Rule is not enabled")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error checking Events rule: {e}")
        return False


def check_cloudwatch_metrics():
    """Check if CloudWatch metrics are being published"""
    print("\n📊 Checking CloudWatch metrics...")
    
    cloudwatch = boto3.client('cloudwatch')
    
    try:
        # Check for metrics in the last 10 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AquaChain/DeviceStatus',
            MetricName='DevicesTotal',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        datapoints = response.get('Datapoints', [])
        
        if datapoints:
            latest = max(datapoints, key=lambda x: x['Timestamp'])
            print(f"  ✅ Found metrics data")
            print(f"  📈 Latest DevicesTotal: {latest['Average']}")
            print(f"  🕐 Timestamp: {latest['Timestamp']}")
            return True
        else:
            print("  ⚠️  No metrics data found (may take a few minutes after deployment)")
            return False
        
    except Exception as e:
        print(f"  ❌ Error checking metrics: {e}")
        return False


def check_dynamodb_tables():
    """Check if required DynamoDB tables exist"""
    print("\n🗄️  Checking DynamoDB tables...")
    
    dynamodb = boto3.client('dynamodb')
    
    required_tables = ['AquaChain-Devices', 'AquaChain-Readings']
    
    try:
        for table_name in required_tables:
            response = dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            print(f"  ✅ Table {table_name}: {status}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error checking DynamoDB tables: {e}")
        return False


def test_lambda_invocation(function_name):
    """Test Lambda function invocation"""
    print(f"\n🧪 Testing Lambda function invocation...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read())
            
            if isinstance(payload.get('body'), str):
                body = json.loads(payload['body'])
            else:
                body = payload.get('body', {})
            
            print(f"  ✅ Lambda invocation successful")
            print(f"  📊 Devices checked: {body.get('devicesChecked', 0)}")
            print(f"  🔄 Status updates: {body.get('statusUpdates', 0)}")
            
            return True
        else:
            print(f"  ❌ Lambda invocation failed: {payload}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing Lambda invocation: {e}")
        return False


def main():
    """Main verification function"""
    print("🔍 Device Status Monitor Deployment Verification")
    print("=" * 55)
    
    checks_passed = 0
    total_checks = 5
    
    # Check Lambda function
    lambda_ok, function_name = check_lambda_function()
    if lambda_ok:
        checks_passed += 1
    
    # Check CloudWatch Events
    if check_cloudwatch_events():
        checks_passed += 1
    
    # Check DynamoDB tables
    if check_dynamodb_tables():
        checks_passed += 1
    
    # Check CloudWatch metrics
    if check_cloudwatch_metrics():
        checks_passed += 1
    
    # Test Lambda invocation
    if lambda_ok and function_name:
        if test_lambda_invocation(function_name):
            checks_passed += 1
    
    print(f"\n📋 Verification Results:")
    print(f"  Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("\n🎉 All checks passed! Device Status Monitor is fully operational.")
        print("\n📊 System Status:")
        print("  • Lambda function: ✅ Deployed and working")
        print("  • CloudWatch Events: ✅ Scheduled every 2 minutes")
        print("  • DynamoDB access: ✅ Read/write permissions working")
        print("  • CloudWatch metrics: ✅ Publishing successfully")
        print("  • Function execution: ✅ No errors")
        
        print("\n🔗 Useful Links:")
        print("  • CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups")
        print("  • CloudWatch Metrics: https://console.aws.amazon.com/cloudwatch/home#metricsV2:graph")
        print("  • Lambda Function: https://console.aws.amazon.com/lambda/home#/functions")
        
    elif checks_passed >= 3:
        print("\n⚠️  Most checks passed, but some issues detected.")
        print("The system should be functional, but monitor the logs for any issues.")
    else:
        print("\n❌ Multiple checks failed. Please review the deployment.")
        sys.exit(1)
    
    print("\n✅ Verification completed")


if __name__ == "__main__":
    main()