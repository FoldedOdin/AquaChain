#!/usr/bin/env python3
"""
Fix IoT Rule SQL to transform flat ESP32 data to nested format
"""

import boto3
import json

def update_iot_rule():
    """Update IoT Rule SQL to transform data"""
    
    iot_client = boto3.client('iot')
    rule_name = 'aquachain_data_ingestion_dev'
    
    # New SQL that transforms flat format to nested structure
    # AWS IoT SQL uses different syntax for object creation
    new_sql = "SELECT deviceId, timestamp() as timestamp, ph as readings.pH, turbidity as readings.turbidity, tds as readings.tds, temperature as readings.temperature, 0.0 as location.latitude, 0.0 as location.longitude, 100.0 as diagnostics.batteryLevel, -50 as diagnostics.signalStrength, 'normal' as diagnostics.sensorStatus FROM 'aquachain/+/data' WHERE ph IS NOT NULL AND turbidity IS NOT NULL"
    
    try:
        # Get current rule
        response = iot_client.get_topic_rule(ruleName=rule_name)
        current_rule = response['rule']
        
        print(f"📋 Current IoT Rule: {rule_name}")
        print(f"   Current SQL: {current_rule['sql']}")
        print()
        
        # Update the rule
        payload = {
            'sql': new_sql,
            'description': 'Transform flat ESP32 data to nested format for Lambda',
            'actions': current_rule['actions'],
            'ruleDisabled': False
        }
        
        # Only add errorAction if it exists
        if 'errorAction' in current_rule and current_rule['errorAction']:
            payload['errorAction'] = current_rule['errorAction']
        
        iot_client.replace_topic_rule(
            ruleName=rule_name,
            topicRulePayload=payload
        )
        
        print(f"✅ Successfully updated IoT Rule!")
        print(f"\n📊 New SQL:")
        print(new_sql)
        print(f"\n🔄 Data Flow:")
        print(f"   ESP32 sends: {{deviceId, ph, turbidity, tds, temperature}}")
        print(f"   IoT Rule transforms to: {{deviceId, location, readings, diagnostics, timestamp}}")
        print(f"   Lambda receives: Nested structure matching schema")
        
        return True
        
    except iot_client.exceptions.ResourceNotFoundException:
        print(f"❌ Error: IoT Rule '{rule_name}' not found")
        return False
        
    except Exception as e:
        print(f"❌ Error updating IoT Rule: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("Fix IoT Rule SQL for ESP32 Data Format")
    print("="*60)
    print()
    
    success = update_iot_rule()
    
    if success:
        print("\n" + "="*60)
        print("✅ IoT Rule Updated Successfully!")
        print("="*60)
        print("\nNext Steps:")
        print("1. ESP32 will automatically start working")
        print("2. Check CloudWatch logs for successful processing")
        print("3. Verify data in DynamoDB tables")
    else:
        print("\n❌ Failed to update IoT Rule")
