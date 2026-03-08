#!/usr/bin/env python3
"""
Fix IoT Rule topic pattern to match ESP32 publishing topic
"""

import boto3
import json

def fix_iot_rule():
    """Update IoT Rule to match correct topic pattern"""
    print("Fixing IoT Rule topic pattern...")
    
    iot_client = boto3.client('iot', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    rule_name = 'aquachain_data_ingestion_dev'
    
    # Get Lambda ARN
    lambda_response = lambda_client.get_function(
        FunctionName='aquachain-function-data-processing-dev'
    )
    lambda_arn = lambda_response['Configuration']['FunctionArn']
    
    print(f"Lambda ARN: {lambda_arn}")
    
    # Delete old rule
    try:
        print(f"\nDeleting old rule: {rule_name}")
        iot_client.delete_topic_rule(ruleName=rule_name)
        print("✓ Old rule deleted")
    except Exception as e:
        print(f"Note: {str(e)}")
    
    # Create new rule with correct topic pattern
    print(f"\nCreating new rule with topic: aquachain/devices/+/data")
    
    rule_payload = {
        "sql": "SELECT * FROM 'aquachain/devices/+/data'",
        "description": "Route IoT sensor readings from ESP32 devices to data processing Lambda",
        "actions": [
            {
                "lambda": {
                    "functionArn": lambda_arn
                }
            }
        ],
        "ruleDisabled": False
    }
    
    iot_client.create_topic_rule(
        ruleName=rule_name,
        topicRulePayload=rule_payload
    )
    
    print("✓ New rule created")
    
    # Grant IoT permission to invoke Lambda
    print("\nGranting IoT permission to invoke Lambda...")
    
    try:
        lambda_client.add_permission(
            FunctionName='aquachain-function-data-processing-dev',
            StatementId='AllowIoTInvoke',
            Action='lambda:InvokeFunction',
            Principal='iot.amazonaws.com',
            SourceArn=f'arn:aws:iot:ap-south-1:758346259059:rule/{rule_name}'
        )
        print("✓ Permission granted")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists")
    
    print("\n" + "=" * 60)
    print("IoT Rule Fixed!")
    print("=" * 60)
    print(f"\nRule: {rule_name}")
    print(f"Topic: aquachain/devices/+/data")
    print(f"Action: Invoke Lambda {lambda_arn}")
    print("\nYour ESP32 should now automatically trigger the Lambda!")

if __name__ == "__main__":
    fix_iot_rule()
