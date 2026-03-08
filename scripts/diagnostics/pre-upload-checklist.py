#!/usr/bin/env python3
"""
Pre-Upload Checklist for ESP32 Firmware

Verifies all AWS IoT configuration is correct before uploading firmware.
"""

import boto3
import json

def check_thing_exists():
    """Check if Thing exists"""
    iot = boto3.client('iot', region_name='ap-south-1')
    try:
        response = iot.describe_thing(thingName='ESP32-001')
        print("✓ Thing 'ESP32-001' exists")
        return True
    except:
        print("✗ Thing 'ESP32-001' not found")
        return False

def check_certificate():
    """Check certificate is attached and active"""
    iot = boto3.client('iot', region_name='ap-south-1')
    try:
        principals = iot.list_thing_principals(thingName='ESP32-001')
        if not principals['principals']:
            print("✗ No certificate attached to Thing")
            return False
        
        cert_arn = principals['principals'][0]
        cert_id = cert_arn.split('/')[-1]
        
        cert = iot.describe_certificate(certificateId=cert_id)
        if cert['certificateDescription']['status'] == 'ACTIVE':
            print("✓ Certificate is ACTIVE")
            return True
        else:
            print(f"✗ Certificate status: {cert['certificateDescription']['status']}")
            return False
    except Exception as e:
        print(f"✗ Error checking certificate: {e}")
        return False

def check_policy():
    """Check policy allows required topics"""
    iot = boto3.client('iot', region_name='ap-south-1')
    try:
        policy = iot.get_policy(policyName='aquachain-device-policy-dev')
        policy_doc = json.loads(policy['policyDocument'])
        
        # Check for status topic
        publish_statement = None
        for statement in policy_doc['Statement']:
            if 'iot:Publish' in statement.get('Action', []):
                publish_statement = statement
                break
        
        if not publish_statement:
            print("✗ No Publish action in policy")
            return False
        
        resources = publish_statement.get('Resource', [])
        if isinstance(resources, str):
            resources = [resources]
        
        has_status = any('/status' in r for r in resources)
        has_data = any('/data' in r for r in resources)
        
        if has_status and has_data:
            print("✓ Policy allows /data and /status topics")
            return True
        else:
            print(f"✗ Policy missing topics - data:{has_data}, status:{has_status}")
            return False
            
    except Exception as e:
        print(f"✗ Error checking policy: {e}")
        return False

def check_endpoint():
    """Check IoT endpoint"""
    iot = boto3.client('iot', region_name='ap-south-1')
    try:
        endpoint = iot.describe_endpoint(endpointType='iot:Data-ATS')
        expected = 'a1k580yq47qhzi-ats.iot.ap-south-1.amazonaws.com'
        if endpoint['endpointAddress'] == expected:
            print(f"✓ IoT endpoint correct: {expected}")
            return True
        else:
            print(f"✗ Endpoint mismatch: {endpoint['endpointAddress']}")
            return False
    except Exception as e:
        print(f"✗ Error checking endpoint: {e}")
        return False

def check_iot_rule():
    """Check IoT Rule is enabled"""
    iot = boto3.client('iot', region_name='ap-south-1')
    try:
        rule = iot.get_topic_rule(ruleName='aquachain_data_ingestion_dev')
        if rule['rule']['ruleDisabled']:
            print("✗ IoT Rule is disabled")
            return False
        else:
            print("✓ IoT Rule is enabled")
            return True
    except Exception as e:
        print(f"✗ Error checking IoT Rule: {e}")
        return False

def main():
    print("=" * 60)
    print("ESP32 Firmware Pre-Upload Checklist")
    print("=" * 60)
    print()
    
    checks = [
        ("Thing Configuration", check_thing_exists),
        ("Certificate Status", check_certificate),
        ("IoT Policy", check_policy),
        ("IoT Endpoint", check_endpoint),
        ("IoT Rule", check_iot_rule)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        results.append(check_func())
    
    print()
    print("=" * 60)
    if all(results):
        print("✓ ALL CHECKS PASSED - Ready to upload firmware!")
        print()
        print("Next steps:")
        print("1. Open Arduino IDE or PlatformIO")
        print("2. Upload iot-firmware/aquachain-esp32/aquachain-esp32-improved/")
        print("3. Open Serial Monitor (115200 baud)")
        print("4. Watch for 'AWS Connected!' message")
        print("5. Verify in AWS IoT MQTT test client")
    else:
        print("✗ SOME CHECKS FAILED - Fix issues before uploading")
        print()
        print("Run these scripts to fix:")
        print("- python scripts/deployment/fix-iot-policy-status-topic.py")
        print("- python scripts/diagnostics/verify-thing-certificates.py")
    print("=" * 60)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
