#!/usr/bin/env python3
"""
Check AWS IoT Thing Configuration
Diagnoses common issues causing MQTT connection failures
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
REGION = 'ap-south-1'
THING_NAME = 'ESP32-001'
EXPECTED_TOPIC = 'aquachain/devices/ESP32-001/data'

def check_thing_exists():
    """Check if IoT Thing exists"""
    print("\n1. Checking if Thing exists...")
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        response = iot.describe_thing(thingName=THING_NAME)
        print(f"   ✓ Thing '{THING_NAME}' exists")
        print(f"   Thing ARN: {response['thingArn']}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   ✗ Thing '{THING_NAME}' NOT FOUND")
            print(f"   Create it with: aws iot create-thing --thing-name {THING_NAME}")
            return False
        raise

def check_certificates():
    """Check if Thing has certificates attached"""
    print("\n2. Checking certificates...")
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        response = iot.list_thing-principals(thingName=THING_NAME)
        principals = response.get('principals', [])
        
        if not principals:
            print(f"   ✗ No certificates attached to Thing '{THING_NAME}'")
            print("   Attach a certificate with:")
            print(f"   aws iot attach-thing-principal --thing-name {THING_NAME} --principal <cert-arn>")
            return False
        
        print(f"   ✓ Found {len(principals)} certificate(s)")
        for principal in principals:
            cert_id = principal.split('/')[-1]
            print(f"   Certificate: {cert_id}")
            
            # Check if certificate is active
            try:
                cert_response = iot.describe_certificate(certificateId=cert_id)
                status = cert_response['certificateDescription']['status']
                print(f"   Status: {status}")
                
                if status != 'ACTIVE':
                    print(f"   ✗ Certificate is {status}, should be ACTIVE")
                    return False
            except:
                pass
        
        return True
    except Exception as e:
        print(f"   ✗ Error checking certificates: {e}")
        return False

def check_policy():
    """Check if certificate has policy attached"""
    print("\n3. Checking IoT policies...")
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        # Get principals (certificates)
        response = iot.list_thing_principals(thingName=THING_NAME)
        principals = response.get('principals', [])
        
        if not principals:
            print("   ✗ No certificates to check policies")
            return False
        
        for principal in principals:
            cert_id = principal.split('/')[-1]
            
            # Get policies attached to certificate
            policy_response = iot.list_principal_policies(principal=principal)
            policies = policy_response.get('policies', [])
            
            if not policies:
                print(f"   ✗ No policies attached to certificate {cert_id}")
                print("   Attach a policy with:")
                print(f"   aws iot attach-policy --policy-name <policy-name> --target {principal}")
                return False
            
            print(f"   ✓ Found {len(policies)} policy/policies")
            
            for policy in policies:
                policy_name = policy['policyName']
                print(f"   Policy: {policy_name}")
                
                # Get policy document
                policy_doc_response = iot.get_policy(policyName=policy_name)
                policy_document = json.loads(policy_doc_response['policyDocument'])
                
                # Check if policy allows publishing to our topic
                allows_publish = False
                for statement in policy_document.get('Statement', []):
                    if statement.get('Effect') == 'Allow':
                        actions = statement.get('Action', [])
                        if isinstance(actions, str):
                            actions = [actions]
                        
                        resources = statement.get('Resource', [])
                        if isinstance(resources, str):
                            resources = [resources]
                        
                        # Check if allows iot:Publish
                        if 'iot:Publish' in actions or 'iot:*' in actions:
                            # Check if allows our topic
                            for resource in resources:
                                if '*' in resource or EXPECTED_TOPIC in resource or 'aquachain/devices/' in resource:
                                    allows_publish = True
                                    break
                
                if allows_publish:
                    print(f"   ✓ Policy allows publishing to {EXPECTED_TOPIC}")
                else:
                    print(f"   ✗ Policy does NOT allow publishing to {EXPECTED_TOPIC}")
                    print(f"   Policy document:")
                    print(json.dumps(policy_document, indent=2))
                    return False
        
        return True
    except Exception as e:
        print(f"   ✗ Error checking policies: {e}")
        return False

def check_endpoint():
    """Check IoT endpoint"""
    print("\n4. Checking IoT endpoint...")
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        response = iot.describe_endpoint(endpointType='iot:Data-ATS')
        endpoint = response['endpointAddress']
        print(f"   ✓ IoT endpoint: {endpoint}")
        print(f"   Expected in config.h: {endpoint}")
        return endpoint
    except Exception as e:
        print(f"   ✗ Error getting endpoint: {e}")
        return None

def check_iot_rule():
    """Check if IoT Rule exists and is configured correctly"""
    print("\n5. Checking IoT Rule...")
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        response = iot.get_topic_rule(ruleName='aquachain_data_ingestion_dev')
        rule = response['rule']
        
        print(f"   ✓ Rule 'aquachain_data_ingestion_dev' exists")
        print(f"   SQL: {rule['sql']}")
        print(f"   Status: {'Enabled' if not rule.get('ruleDisabled', False) else 'Disabled'}")
        
        # Check if rule is listening to correct topic
        sql = rule['sql']
        if 'aquachain/devices/' in sql:
            print(f"   ✓ Rule is listening to correct topic pattern")
        else:
            print(f"   ✗ Rule SQL may not match device topic")
        
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   ✗ Rule 'aquachain_data_ingestion_dev' NOT FOUND")
            return False
        raise

def main():
    print("=" * 60)
    print("AWS IoT Thing Configuration Diagnostic")
    print("=" * 60)
    print(f"Region: {REGION}")
    print(f"Thing Name: {THING_NAME}")
    print(f"Expected Topic: {EXPECTED_TOPIC}")
    
    results = {
        'thing_exists': check_thing_exists(),
        'certificates_ok': check_certificates(),
        'policy_ok': check_policy(),
        'endpoint': check_endpoint(),
        'rule_ok': check_iot_rule()
    }
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_ok = all([
        results['thing_exists'],
        results['certificates_ok'],
        results['policy_ok'],
        results['endpoint'] is not None,
        results['rule_ok']
    ])
    
    if all_ok:
        print("✓ All checks passed!")
        print("\nIf ESP32 still shows 'rc=-4', check:")
        print("1. WiFi connection is stable")
        print("2. Certificates in config.h match AWS IoT Thing")
        print("3. ESP32 can reach internet (try ping 8.8.8.8)")
        print("4. Firewall allows outbound port 8883")
    else:
        print("✗ Some checks failed - see details above")
        print("\nCommon fixes:")
        print("1. Ensure Thing exists and has certificate attached")
        print("2. Ensure certificate is ACTIVE")
        print("3. Ensure policy allows iot:Publish to aquachain/devices/*")
        print("4. Ensure IoT Rule is enabled and listening to correct topic")

if __name__ == '__main__':
    main()
