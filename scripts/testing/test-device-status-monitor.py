#!/usr/bin/env python3
"""
Test Device Status Monitor Functionality
Tests the device online/offline status monitoring system
"""

import os
import sys
import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
LAMBDA_FUNCTION = os.environ.get('STATUS_MONITOR_LAMBDA', 'AquaChain-DeviceStatusMon-DeviceStatusMonitorFunct-jbstDx1pJpMY')


def create_test_devices() -> List[Dict[str, Any]]:
    """Create test devices with different status scenarios"""
    
    devices_table = dynamodb.Table(DEVICES_TABLE)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    test_devices = [
        {
            'deviceId': 'TEST-ONLINE-001',
            'userId': 'test-user-1',
            'deviceName': 'Test Online Device',
            'location': 'Test Location 1',
            'status': 'active',
            'connectionStatus': 'unknown',
            'createdAt': timestamp,
            'lastSeen': timestamp,  # Just seen - should be online
            'statusUpdatedAt': timestamp
        },
        {
            'deviceId': 'TEST-OFFLINE-001',
            'userId': 'test-user-1',
            'deviceName': 'Test Offline Device',
            'location': 'Test Location 2',
            'status': 'active',
            'connectionStatus': 'unknown',
            'createdAt': timestamp,
            'lastSeen': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z',  # 10 minutes ago - should be offline
            'statusUpdatedAt': timestamp
        },
        {
            'deviceId': 'TEST-UNKNOWN-001',
            'userId': 'test-user-1',
            'deviceName': 'Test Unknown Device',
            'location': 'Test Location 3',
            'status': 'active',
            'connectionStatus': 'unknown',
            'createdAt': timestamp,
            # No lastSeen - should remain unknown
            'statusUpdatedAt': timestamp
        }
    ]
    
    print("📱 Creating test devices...")
    for device in test_devices:
        try:
            devices_table.put_item(Item=device)
            print(f"  ✅ Created device: {device['deviceId']}")
        except Exception as e:
            print(f"  ❌ Error creating device {device['deviceId']}: {e}")
    
    return test_devices


def invoke_status_monitor() -> Dict[str, Any]:
    """Invoke the device status monitor Lambda function"""
    
    print("🔍 Invoking device status monitor...")
    
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("  ✅ Lambda invocation successful")
            
            # Parse response body if it's a string
            if isinstance(payload.get('body'), str):
                body = json.loads(payload['body'])
            else:
                body = payload.get('body', {})
            
            print(f"  📊 Devices checked: {body.get('devicesChecked', 0)}")
            print(f"  🔄 Status updates: {body.get('statusUpdates', 0)}")
            
            # Print status updates
            updates = body.get('updates', [])
            for update in updates:
                print(f"    • {update['deviceId']}: {update['oldStatus']} → {update['newStatus']}")
            
            return body
        else:
            print(f"  ❌ Lambda invocation failed: {payload}")
            return {}
            
    except Exception as e:
        print(f"  ❌ Error invoking Lambda: {e}")
        return {}


def verify_device_status(test_devices: List[Dict[str, Any]]) -> bool:
    """Verify that device statuses were updated correctly"""
    
    print("🔍 Verifying device status updates...")
    devices_table = dynamodb.Table(DEVICES_TABLE)
    
    all_correct = True
    
    for device in test_devices:
        device_id = device['deviceId']
        
        try:
            response = devices_table.get_item(Key={'deviceId': device_id})
            updated_device = response.get('Item')
            
            if not updated_device:
                print(f"  ❌ Device {device_id} not found")
                all_correct = False
                continue
            
            connection_status = updated_device.get('connectionStatus', 'unknown')
            last_seen = updated_device.get('lastSeen')
            
            print(f"  📱 {device_id}:")
            print(f"    Connection Status: {connection_status}")
            print(f"    Last Seen: {last_seen}")
            
            # Verify expected status
            if device_id == 'TEST-ONLINE-001':
                expected = 'online'
            elif device_id == 'TEST-OFFLINE-001':
                expected = 'offline'
            else:  # TEST-UNKNOWN-001
                expected = 'unknown'
            
            if connection_status == expected:
                print(f"    ✅ Status correct: {connection_status}")
            else:
                print(f"    ❌ Status incorrect: expected {expected}, got {connection_status}")
                all_correct = False
                
        except Exception as e:
            print(f"  ❌ Error checking device {device_id}: {e}")
            all_correct = False
    
    return all_correct


def check_cloudwatch_metrics() -> bool:
    """Check if CloudWatch metrics were published"""
    
    print("📊 Checking CloudWatch metrics...")
    
    try:
        # Get metrics from the last 10 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        metrics_to_check = [
            'DevicesCountOnline',
            'DevicesCountOffline', 
            'DevicesCountUnknown',
            'DevicesTotal',
            'DeviceStatusChanges'
        ]
        
        metrics_found = 0
        
        for metric_name in metrics_to_check:
            response = cloudwatch.get_metric_statistics(
                Namespace='AquaChain/DeviceStatus',
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=['Average', 'Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                value = latest.get('Average', latest.get('Sum', 0))
                print(f"  📈 {metric_name}: {value}")
                metrics_found += 1
            else:
                print(f"  ⚠️  {metric_name}: No data")
        
        if metrics_found > 0:
            print(f"  ✅ Found {metrics_found}/{len(metrics_to_check)} metrics")
            return True
        else:
            print("  ❌ No metrics found")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking metrics: {e}")
        return False


def cleanup_test_devices(test_devices: List[Dict[str, Any]]) -> None:
    """Clean up test devices"""
    
    print("🧹 Cleaning up test devices...")
    devices_table = dynamodb.Table(DEVICES_TABLE)
    
    for device in test_devices:
        device_id = device['deviceId']
        try:
            devices_table.delete_item(Key={'deviceId': device_id})
            print(f"  ✅ Deleted device: {device_id}")
        except Exception as e:
            print(f"  ❌ Error deleting device {device_id}: {e}")


def main():
    """Run device status monitor tests"""
    
    print("🧪 Testing Device Status Monitor")
    print("=" * 50)
    
    # Check if Lambda function exists
    try:
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION)
        print(f"✅ Lambda function found: {LAMBDA_FUNCTION}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"❌ Lambda function not found: {LAMBDA_FUNCTION}")
        print("Please deploy the device status monitor first:")
        print("  python scripts/deployment/deploy-device-status-monitor.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking Lambda function: {e}")
        sys.exit(1)
    
    print()
    
    # Create test devices
    test_devices = create_test_devices()
    
    # Wait a moment for DynamoDB consistency
    print("⏳ Waiting for DynamoDB consistency...")
    time.sleep(2)
    
    try:
        # Invoke status monitor
        result = invoke_status_monitor()
        
        # Wait for updates to propagate
        print("⏳ Waiting for status updates...")
        time.sleep(3)
        
        # Verify device status
        status_correct = verify_device_status(test_devices)
        
        # Check CloudWatch metrics
        metrics_ok = check_cloudwatch_metrics()
        
        print()
        print("📋 Test Results:")
        print(f"  Device Status Updates: {'✅ PASS' if status_correct else '❌ FAIL'}")
        print(f"  CloudWatch Metrics: {'✅ PASS' if metrics_ok else '❌ FAIL'}")
        
        if status_correct and metrics_ok:
            print("\n🎉 All tests passed! Device status monitoring is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above for details.")
        
    finally:
        # Clean up test devices
        print()
        cleanup_test_devices(test_devices)
    
    print("\n✅ Test completed")


if __name__ == "__main__":
    main()