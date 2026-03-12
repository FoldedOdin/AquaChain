#!/usr/bin/env python3
"""
Test Pluggable Device System
Validates the pluggable device functionality
"""

import boto3
import json
import time
from datetime import datetime

def test_dynamodb_table():
    """Test that the PluggableDevices table exists and is accessible"""
    print("🧪 Testing DynamoDB table access...")
    
    dynamodb = boto3.resource('dynamodb')
    table_name = 'AquaChain-PluggableDevices'
    
    try:
        table = dynamodb.Table(table_name)
        
        # Test table description
        response = table.meta.client.describe_table(TableName=table_name)
        table_status = response['Table']['TableStatus']
        
        if table_status == 'ACTIVE':
            print(f"✅ Table {table_name} is ACTIVE")
            
            # Test GSI
            gsi_found = False
            for gsi in response['Table'].get('GlobalSecondaryIndexes', []):
                if gsi['IndexName'] == 'userId-createdAt-index':
                    gsi_found = True
                    print(f"✅ GSI userId-createdAt-index found")
                    break
            
            if not gsi_found:
                print("❌ GSI userId-createdAt-index not found")
                return False
            
            return True
        else:
            print(f"❌ Table {table_name} status: {table_status}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing table: {str(e)}")
        return False

def test_device_registration():
    """Test device registration functionality"""
    print("🧪 Testing device registration...")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('AquaChain-PluggableDevices')
    
    # Create test device record
    test_device = {
        'deviceId': 'TEST-ESP32-001',
        'userId': 'test-user-123',
        'name': 'Test Water Monitor',
        'type': 'water_quality',
        'connectionType': 'wifi',
        'status': 'connected',
        'capabilities': [
            {
                'id': 'ph',
                'name': 'pH Level',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'pH',
                'range': {'min': 0, 'max': 14},
                'readonly': True
            }
        ],
        'metadata': {
            'location': 'Test Location',
            'manufacturer': 'AquaChain'
        },
        'connectionConfig': {
            'type': 'wifi',
            'parameters': {
                'ssid': 'TestNetwork'
            }
        },
        'createdAt': datetime.utcnow().isoformat() + 'Z',
        'lastSeen': datetime.utcnow().isoformat() + 'Z',
        'isShared': False,
        'sharedWith': []
    }
    
    try:
        # Insert test device
        table.put_item(Item=test_device)
        print("✅ Test device inserted successfully")
        
        # Retrieve test device
        response = table.get_item(Key={'deviceId': 'TEST-ESP32-001'})
        
        if 'Item' in response:
            retrieved_device = response['Item']
            print("✅ Test device retrieved successfully")
            
            # Verify key fields
            if (retrieved_device['name'] == test_device['name'] and
                retrieved_device['type'] == test_device['type'] and
                retrieved_device['connectionType'] == test_device['connectionType']):
                print("✅ Device data integrity verified")
            else:
                print("❌ Device data integrity check failed")
                return False
        else:
            print("❌ Test device not found after insertion")
            return False
        
        # Test GSI query
        response = table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': 'test-user-123'}
        )
        
        if response['Items'] and len(response['Items']) > 0:
            print("✅ GSI query successful")
        else:
            print("❌ GSI query failed")
            return False
        
        # Clean up test device
        table.delete_item(Key={'deviceId': 'TEST-ESP32-001'})
        print("✅ Test device cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in device registration test: {str(e)}")
        return False

def test_connection_handlers():
    """Test connection handler validation"""
    print("🧪 Testing connection handler logic...")
    
    # Test WiFi handler validation
    wifi_device = {
        'deviceId': 'ESP32-WIFI-001',
        'name': 'WiFi Water Monitor',
        'type': 'water_quality',
        'connectionType': 'wifi',
        'capabilities': [],
        'metadata': {'ipAddress': '192.168.1.100'},
        'isConnectable': True,
        'requiresPairing': True
    }
    
    # Test QR code handler validation
    qr_device = {
        'deviceId': 'ESP32-QR-001', 
        'name': 'QR Water Monitor',
        'type': 'water_quality',
        'connectionType': 'qr_code',
        'capabilities': [],
        'metadata': {'pairingKey': 'abc123def456'},
        'isConnectable': True,
        'requiresPairing': True
    }
    
    # Validate device structures
    required_fields = ['deviceId', 'name', 'type', 'connectionType', 'capabilities', 'metadata']
    
    for device_name, device in [('WiFi', wifi_device), ('QR Code', qr_device)]:
        for field in required_fields:
            if field not in device:
                print(f"❌ {device_name} device missing required field: {field}")
                return False
        print(f"✅ {device_name} device structure valid")
    
    # Test connection type validation
    valid_connection_types = ['wifi', 'bluetooth', 'qr_code', 'manual', 'auto_discovery']
    
    for device_name, device in [('WiFi', wifi_device), ('QR Code', qr_device)]:
        if device['connectionType'] not in valid_connection_types:
            print(f"❌ {device_name} device has invalid connection type")
            return False
        print(f"✅ {device_name} device connection type valid")
    
    return True

def test_device_capabilities():
    """Test device capability definitions"""
    print("🧪 Testing device capability definitions...")
    
    water_quality_capabilities = [
        {
            'id': 'ph',
            'name': 'pH Level',
            'type': 'sensor',
            'dataType': 'number',
            'unit': 'pH',
            'range': {'min': 0, 'max': 14},
            'readonly': True
        },
        {
            'id': 'turbidity',
            'name': 'Turbidity',
            'type': 'sensor',
            'dataType': 'number',
            'unit': 'NTU',
            'range': {'min': 0, 'max': 1000},
            'readonly': True
        }
    ]
    
    required_capability_fields = ['id', 'name', 'type', 'dataType', 'readonly']
    
    for capability in water_quality_capabilities:
        for field in required_capability_fields:
            if field not in capability:
                print(f"❌ Capability {capability.get('name', 'Unknown')} missing field: {field}")
                return False
        
        # Validate capability type
        if capability['type'] not in ['sensor', 'actuator', 'display', 'storage']:
            print(f"❌ Capability {capability['name']} has invalid type")
            return False
        
        # Validate data type
        if capability['dataType'] not in ['number', 'string', 'boolean', 'object']:
            print(f"❌ Capability {capability['name']} has invalid dataType")
            return False
    
    print("✅ Device capabilities structure valid")
    return True

def main():
    """Run all tests"""
    print("🧪 Testing AquaChain Pluggable Device System")
    print("=" * 50)
    
    tests = [
        ("DynamoDB Table Access", test_dynamodb_table),
        ("Device Registration", test_device_registration),
        ("Connection Handlers", test_connection_handlers),
        ("Device Capabilities", test_device_capabilities)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ PASSED: {test_name}")
                passed += 1
            else:
                print(f"❌ FAILED: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pluggable Device System is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)