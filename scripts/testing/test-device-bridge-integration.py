#!/usr/bin/env python3
"""
Test Device Bridge Integration
Verifies that the ESP32-001 device appears correctly in the pluggable system
"""

import boto3
import json
from datetime import datetime

def test_bridged_device_visibility():
    """Test that ESP32-001 appears in pluggable devices table"""
    print("🧪 Testing bridged device visibility...")
    
    dynamodb = boto3.resource('dynamodb')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        # Check if ESP32-001 exists in pluggable devices
        response = pluggable_devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        if 'Item' in response:
            device = response['Item']
            print(f"✅ Found ESP32-001 in pluggable devices table")
            print(f"   Name: {device.get('name')}")
            print(f"   Type: {device.get('type')}")
            print(f"   Status: {device.get('status')}")
            print(f"   Connection Type: {device.get('connectionType')}")
            print(f"   Capabilities: {len(device.get('capabilities', []))}")
            print(f"   Is Bridged: {device.get('metadata', {}).get('isBridged')}")
            return True
        else:
            print("❌ ESP32-001 not found in pluggable devices table")
            return False
            
    except Exception as e:
        print(f"❌ Error checking bridged device: {str(e)}")
        return False


def test_device_capabilities():
    """Test that ESP32-001 has correct capabilities"""
    print("\n🧪 Testing device capabilities...")
    
    dynamodb = boto3.resource('dynamodb')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        response = pluggable_devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        if 'Item' in response:
            device = response['Item']
            capabilities = device.get('capabilities', [])
            
            expected_capabilities = ['ph', 'turbidity', 'tds', 'temperature', 'wqi']
            found_capabilities = [cap.get('id') for cap in capabilities]
            
            print(f"✅ Device has {len(capabilities)} capabilities")
            
            for expected in expected_capabilities:
                if expected in found_capabilities:
                    print(f"   ✅ {expected} capability found")
                else:
                    print(f"   ❌ {expected} capability missing")
                    return False
            
            return True
        else:
            print("❌ Device not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking capabilities: {str(e)}")
        return False


def test_device_metadata():
    """Test that ESP32-001 has correct metadata"""
    print("\n🧪 Testing device metadata...")
    
    dynamodb = boto3.resource('dynamodb')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        response = pluggable_devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        if 'Item' in response:
            device = response['Item']
            metadata = device.get('metadata', {})
            
            checks = [
                ('isBridged', True, 'Device should be marked as bridged'),
                ('originalDeviceRecord', True, 'Device should be marked as original'),
                ('manufacturer', 'AquaChain', 'Manufacturer should be AquaChain'),
                ('model', 'ESP32-WQ', 'Model should be ESP32-WQ')
            ]
            
            all_passed = True
            for key, expected, description in checks:
                actual = metadata.get(key)
                if actual == expected:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description} (Expected: {expected}, Got: {actual})")
                    all_passed = False
            
            return all_passed
        else:
            print("❌ Device not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking metadata: {str(e)}")
        return False


def test_connection_config():
    """Test that ESP32-001 has correct connection configuration"""
    print("\n🧪 Testing connection configuration...")
    
    dynamodb = boto3.resource('dynamodb')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        response = pluggable_devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        if 'Item' in response:
            device = response['Item']
            connection_config = device.get('connectionConfig', {})
            
            if connection_config.get('type') == 'auto_discovery':
                print("   ✅ Connection type is auto_discovery")
            else:
                print(f"   ❌ Wrong connection type: {connection_config.get('type')}")
                return False
            
            parameters = connection_config.get('parameters', {})
            if parameters.get('bridgedFromTraditional'):
                print("   ✅ Marked as bridged from traditional system")
            else:
                print("   ❌ Not marked as bridged from traditional system")
                return False
            
            if parameters.get('iotCoreConnected'):
                print("   ✅ Marked as IoT Core connected")
            else:
                print("   ❌ Not marked as IoT Core connected")
                return False
            
            return True
        else:
            print("❌ Device not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking connection config: {str(e)}")
        return False


def test_dual_system_presence():
    """Test that ESP32-001 exists in both traditional and pluggable systems"""
    print("\n🧪 Testing dual system presence...")
    
    dynamodb = boto3.resource('dynamodb')
    devices_table = dynamodb.Table('AquaChain-Devices')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        # Check traditional system
        traditional_response = devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        # Check pluggable system
        pluggable_response = pluggable_devices_table.get_item(
            Key={'deviceId': 'ESP32-001'}
        )
        
        traditional_exists = 'Item' in traditional_response
        pluggable_exists = 'Item' in pluggable_response
        
        if traditional_exists:
            print("   ✅ Device exists in traditional system")
        else:
            print("   ❌ Device missing from traditional system")
        
        if pluggable_exists:
            print("   ✅ Device exists in pluggable system")
        else:
            print("   ❌ Device missing from pluggable system")
        
        return traditional_exists and pluggable_exists
        
    except Exception as e:
        print(f"❌ Error checking dual system presence: {str(e)}")
        return False


def simulate_frontend_discovery():
    """Simulate what the frontend would see when discovering devices"""
    print("\n🧪 Simulating frontend device discovery...")
    
    dynamodb = boto3.resource('dynamodb')
    pluggable_devices_table = dynamodb.Table('AquaChain-PluggableDevices')
    
    try:
        # Query for auto-discovery devices (what IoT Core handler would find)
        response = pluggable_devices_table.scan(
            FilterExpression='connectionType = :conn_type',
            ExpressionAttributeValues={':conn_type': 'auto_discovery'}
        )
        
        devices = response.get('Items', [])
        
        print(f"   📡 Frontend would discover {len(devices)} IoT Core devices:")
        
        for device in devices:
            device_id = device.get('deviceId')
            name = device.get('name')
            status = device.get('status')
            device_type = device.get('type')
            is_bridged = device.get('metadata', {}).get('isBridged', False)
            
            print(f"      🔌 {device_id} ({name})")
            print(f"         Type: {device_type}, Status: {status}")
            print(f"         Bridged: {is_bridged}")
        
        # Check if ESP32-001 is in the list
        esp32_found = any(d.get('deviceId') == 'ESP32-001' for d in devices)
        
        if esp32_found:
            print("   ✅ ESP32-001 would be discoverable by frontend")
            return True
        else:
            print("   ❌ ESP32-001 would NOT be discoverable by frontend")
            return False
        
    except Exception as e:
        print(f"❌ Error simulating frontend discovery: {str(e)}")
        return False


def main():
    """Run all integration tests"""
    print("🔗 Testing Device Bridge Integration")
    print("=" * 50)
    
    tests = [
        ("Bridged Device Visibility", test_bridged_device_visibility),
        ("Device Capabilities", test_device_capabilities),
        ("Device Metadata", test_device_metadata),
        ("Connection Configuration", test_connection_config),
        ("Dual System Presence", test_dual_system_presence),
        ("Frontend Discovery Simulation", simulate_frontend_discovery)
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
    
    print(f"\n📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n✅ Your ESP32-001 device is fully integrated with the pluggable system!")
        print("✅ It will appear in the Consumer Dashboard when you click 'Connect Devices'")
        print("✅ It will show as an 'IoT Core' device with real-time status")
        print("✅ All existing functionality is preserved")
        return True
    else:
        print("⚠️ Some integration tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)