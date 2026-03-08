#!/usr/bin/env python3
"""
Update IoT Rule to handle flat ESP32 data format
Transforms flat sensor values into nested structure expected by Lambda
"""

import boto3
import json
import sys

def update_iot_rule():
    """Update IoT Rule SQL to transform flat ESP32 data"""
    
    iot_client = boto3.client('iot')
    
    # New SQL that transforms flat format to nested structure
    # Converts UNIX epoch timestamp to ISO 8601 format
    new_sql = """
    SELECT 
      deviceId,
      parse_time("yyyy-MM-dd'T'HH:mm:ss'Z'", timestamp * 1000) as timestamp,
      {
        'latitude': 0.0,
        'longitude': 0.0
      } as location,
      {
        'pH': ph,
        'turbidity': turbidity,
        'tds': tds,
        'temperature': temperature
      } as readings,
      {
        'batteryLevel': 100.0,
        'signalStrength': -50,
        'sensorStatus': 'normal'
      } as diagnostics
    FROM 'aquachain/+/data'
    WHERE ph IS NOT NULL AND turbidity IS NOT NULL
    """
    
    rule_name = 'AquaChainDataProcessing'
    
    try:
        # Get current rule
        response = iot_client.get_topic_rule(ruleName=rule_name)
        current_rule = response['rule']
        
        print(f"📋 Current IoT Rule: {rule_name}")
        print(f"   Current SQL: {current_rule['sql']}")
        
        # Update the rule
        iot_client.replace_topic_rule(
            ruleName=rule_name,
            topicRulePayload={
                'sql': new_sql.strip(),
                'description': current_rule.get('description', 'Route water quality sensor data to processing Lambda'),
                'actions': current_rule['actions'],
                'errorAction': current_rule.get('errorAction'),
                'ruleDisabled': False
            }
        )
        
        print(f"\n✅ Successfully updated IoT Rule!")
        print(f"   New SQL: {new_sql.strip()}")
        print(f"\n📊 Data Flow:")
        print(f"   ESP32 sends: {{deviceId, ph, turbidity, tds, temperature, timestamp}}")
        print(f"   IoT Rule transforms to: {{deviceId, location, readings, diagnostics, timestamp}}")
        print(f"   Lambda receives: Nested structure matching schema")
        
        return True
        
    except iot_client.exceptions.ResourceNotFoundException:
        print(f"❌ Error: IoT Rule '{rule_name}' not found")
        print(f"   Create the rule first using infrastructure/iot/core_setup.py")
        return False
        
    except Exception as e:
        print(f"❌ Error updating IoT Rule: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("Update IoT Rule for Flat ESP32 Data Format")
    print("="*60)
    
    success = update_iot_rule()
    
    if success:
        print("\n" + "="*60)
        print("✅ IoT Rule Updated Successfully!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Test with ESP32: Send data to 'aquachain/ESP32-001/data'")
        print("2. Check CloudWatch Logs: /aws/lambda/AquaChainDataProcessor")
        print("3. Verify DynamoDB: Check AquaChain-Readings table")
        print("4. Verify Ledger: Check AquaChain-Ledger table")
        sys.exit(0)
    else:
        print("\n❌ Failed to update IoT Rule")
        sys.exit(1)
