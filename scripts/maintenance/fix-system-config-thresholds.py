#!/usr/bin/env python3
"""
Fix System Configuration Thresholds in DynamoDB

This script updates the system configuration with correct threshold values:
- Turbidity: Critical Max = 4 NTU, Warning Max = 8 NTU
- TDS: Critical Max = 300 ppm, Warning Max = 450 ppm  
- Temperature: Warning Min = 0°C, Critical Min = 10°C, Critical Max = 40°C, Warning Max = 50°C

SAFETY FEATURES:
- Creates backup before making changes
- Validates new configuration against backend rules
- Logs changes to audit trail
- Requires explicit confirmation
- Can be rolled back if needed

Usage:
    python scripts/maintenance/fix-system-config-thresholds.py --environment dev --region ap-south-1
"""

import boto3
import json
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
import argparse


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert floats to Decimal for DynamoDB compatibility"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def validate_thresholds(config: Dict) -> tuple[bool, list[str]]:
    """
    Validate threshold configuration against backend rules
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if 'alertThresholds' not in config or 'global' not in config['alertThresholds']:
        errors.append('Missing alertThresholds.global in configuration')
        return (False, errors)
    
    thresholds = config['alertThresholds']['global']
    
    # Turbidity validation
    if 'turbidity' in thresholds:
        turb = thresholds['turbidity']
        if 'critical' in turb and 'warning' in turb:
            c_max = float(turb['critical'].get('max', 0))
            w_max = float(turb['warning'].get('max', 0))
            
            if not (0 <= c_max <= 100):
                errors.append(f'Turbidity critical.max must be between 0 and 100 NTU (got {c_max})')
            if not (0 <= w_max <= 100):
                errors.append(f'Turbidity warning.max must be between 0 and 100 NTU (got {w_max})')
            if c_max >= w_max:
                errors.append(f'Turbidity: critical.max ({c_max}) must be < warning.max ({w_max})')
    
    # TDS validation
    if 'tds' in thresholds:
        tds = thresholds['tds']
        if 'critical' in tds and 'warning' in tds:
            c_max = float(tds['critical'].get('max', 0))
            w_max = float(tds['warning'].get('max', 0))
            
            if not (0 <= c_max <= 5000):
                errors.append(f'TDS critical.max must be between 0 and 5000 ppm (got {c_max})')
            if not (0 <= w_max <= 5000):
                errors.append(f'TDS warning.max must be between 0 and 5000 ppm (got {w_max})')
            if c_max >= w_max:
                errors.append(f'TDS: critical.max ({c_max}) must be < warning.max ({w_max})')
    
    # Temperature validation
    if 'temperature' in thresholds:
        temp = thresholds['temperature']
        if 'critical' in temp and 'warning' in temp:
            w_min = float(temp['warning'].get('min', 0))
            c_min = float(temp['critical'].get('min', 0))
            c_max = float(temp['critical'].get('max', 0))
            w_max = float(temp['warning'].get('max', 0))
            
            if not (-10 <= w_min <= 100):
                errors.append(f'Temperature warning.min must be between -10 and 100°C (got {w_min})')
            if not (-10 <= c_min <= 100):
                errors.append(f'Temperature critical.min must be between -10 and 100°C (got {c_min})')
            if not (-10 <= c_max <= 100):
                errors.append(f'Temperature critical.max must be between -10 and 100°C (got {c_max})')
            if not (-10 <= w_max <= 100):
                errors.append(f'Temperature warning.max must be between -10 and 100°C (got {w_max})')
            
            if not (w_min < c_min < c_max < w_max):
                errors.append(
                    f'Temperature thresholds must satisfy: warning.min ({w_min}) < '
                    f'critical.min ({c_min}) < critical.max ({c_max}) < warning.max ({w_max})'
                )
    
    return (len(errors) == 0, errors)


def backup_current_config(dynamodb, table_name: str, backup_file: str) -> Dict:
    """Create a backup of the current configuration"""
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'configKey': 'system_config'})
    
    if 'Item' not in response:
        raise Exception('No system configuration found in database')
    
    current_config = response['Item']
    
    # Save backup to file
    with open(backup_file, 'w') as f:
        json.dump(current_config, f, indent=2, cls=DecimalEncoder)
    
    print(f"✅ Backup saved to: {backup_file}")
    return current_config


def update_configuration(dynamodb, config_table_name: str, history_table_name: str, 
                        new_config: Dict, admin_id: str = 'system-maintenance') -> None:
    """Update configuration with versioning and audit logging"""
    
    config_table = dynamodb.Table(config_table_name)
    history_table = dynamodb.Table(history_table_name)
    
    # Generate version identifier
    version_timestamp = datetime.utcnow().isoformat()
    version_id = f"v_{version_timestamp}"
    
    # Get previous version
    previous_version = new_config.get('version', 'v_initial')
    
    # Convert to Decimal for DynamoDB
    config_for_db = convert_floats_to_decimal(new_config)
    config_for_db['configKey'] = 'system_config'
    config_for_db['version'] = version_id
    config_for_db['updated_at'] = version_timestamp
    config_for_db['updated_by'] = admin_id
    
    # Save version to history
    history_entry = {
        'configId': 'SYSTEM_CONFIG',
        'version': version_id,
        'updatedBy': admin_id,
        'updatedAt': version_timestamp,
        'previousVersion': previous_version,
        'changes': {
            'turbidity': 'Updated critical and warning thresholds',
            'tds': 'Updated critical and warning thresholds',
            'temperature': 'Updated critical and warning thresholds'
        },
        'fullConfig': config_for_db,
        'ipAddress': 'localhost-maintenance-script'
    }
    
    history_table.put_item(Item=convert_floats_to_decimal(history_entry))
    print(f"✅ Version history saved: {version_id}")
    
    # Update current configuration
    config_table.put_item(Item=config_for_db)
    print(f"✅ Configuration updated successfully")


def main():
    parser = argparse.ArgumentParser(description='Fix system configuration thresholds')
    parser.add_argument('--environment', default='dev', help='Environment (dev/staging/prod)')
    parser.add_argument('--region', default='ap-south-1', help='AWS region')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Table names
    config_table = f'AquaChain-SystemConfig'
    history_table = f'AquaChain-ConfigHistory'
    backup_file = f'config-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    
    print("=" * 80)
    print("🔧 AquaChain - Fix System Configuration Thresholds")
    print("=" * 80)
    print()
    print(f"Environment: {args.environment}")
    print(f"Region: {args.region}")
    print(f"Config Table: {config_table}")
    print(f"History Table: {history_table}")
    print()
    
    # Initialize AWS clients
    try:
        dynamodb = boto3.resource('dynamodb', region_name=args.region)
        print("✅ Connected to DynamoDB")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        print("\nMake sure you have AWS credentials configured:")
        print("  aws configure")
        sys.exit(1)
    
    # Step 1: Backup current configuration
    print("\n" + "=" * 80)
    print("STEP 1: Backing up current configuration")
    print("=" * 80)
    
    try:
        current_config = backup_current_config(dynamodb, config_table, backup_file)
    except Exception as e:
        print(f"❌ Failed to backup configuration: {e}")
        sys.exit(1)
    
    # Step 2: Show current values
    print("\n" + "=" * 80)
    print("STEP 2: Current threshold values")
    print("=" * 80)
    
    thresholds = current_config.get('alertThresholds', {}).get('global', {})
    
    print("\n📊 Turbidity:")
    print(f"  Current Critical Max: {thresholds.get('turbidity', {}).get('critical', {}).get('max', 'N/A')} NTU")
    print(f"  Current Warning Max:  {thresholds.get('turbidity', {}).get('warning', {}).get('max', 'N/A')} NTU")
    
    print("\n📊 TDS:")
    print(f"  Current Critical Max: {thresholds.get('tds', {}).get('critical', {}).get('max', 'N/A')} ppm")
    print(f"  Current Warning Max:  {thresholds.get('tds', {}).get('warning', {}).get('max', 'N/A')} ppm")
    
    print("\n📊 Temperature:")
    print(f"  Current Warning Min:  {thresholds.get('temperature', {}).get('warning', {}).get('min', 'N/A')}°C")
    print(f"  Current Critical Min: {thresholds.get('temperature', {}).get('critical', {}).get('min', 'N/A')}°C")
    print(f"  Current Critical Max: {thresholds.get('temperature', {}).get('critical', {}).get('max', 'N/A')}°C")
    print(f"  Current Warning Max:  {thresholds.get('temperature', {}).get('warning', {}).get('max', 'N/A')}°C")
    
    # Step 3: Apply new values
    print("\n" + "=" * 80)
    print("STEP 3: New threshold values (scientifically correct)")
    print("=" * 80)
    
    print("\n📊 Turbidity:")
    print(f"  New Critical Max: 4 NTU")
    print(f"  New Warning Max:  8 NTU")
    
    print("\n📊 TDS:")
    print(f"  New Critical Max: 300 ppm")
    print(f"  New Warning Max:  450 ppm")
    
    print("\n📊 Temperature:")
    print(f"  New Warning Min:  0°C")
    print(f"  New Critical Min: 10°C")
    print(f"  New Critical Max: 40°C")
    print(f"  New Warning Max:  50°C")
    
    # Update the configuration
    new_config = dict(current_config)
    new_config['alertThresholds']['global']['turbidity'] = {
        'critical': {'max': 4},
        'warning': {'max': 8}
    }
    new_config['alertThresholds']['global']['tds'] = {
        'critical': {'max': 300},
        'warning': {'max': 450}
    }
    new_config['alertThresholds']['global']['temperature'] = {
        'warning': {'min': 0, 'max': 50},
        'critical': {'min': 10, 'max': 40}
    }
    
    # Step 4: Validate new configuration
    print("\n" + "=" * 80)
    print("STEP 4: Validating new configuration")
    print("=" * 80)
    
    is_valid, errors = validate_thresholds(new_config)
    
    if not is_valid:
        print("\n❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        print("\n⚠️  Configuration update aborted")
        sys.exit(1)
    
    print("✅ Validation passed - configuration is correct")
    
    # Step 5: Confirmation
    if not args.yes:
        print("\n" + "=" * 80)
        print("⚠️  CONFIRMATION REQUIRED")
        print("=" * 80)
        print("\nThis will update the system configuration in DynamoDB.")
        print("All devices and users will be affected immediately.")
        print(f"\nBackup file: {backup_file}")
        print("\nTo restore from backup, run:")
        print(f"  python scripts/maintenance/restore-config-backup.py {backup_file}")
        print()
        
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n❌ Update cancelled by user")
            sys.exit(0)
    
    # Step 6: Update configuration
    print("\n" + "=" * 80)
    print("STEP 5: Updating configuration")
    print("=" * 80)
    
    try:
        update_configuration(dynamodb, config_table, history_table, new_config)
    except Exception as e:
        print(f"\n❌ Failed to update configuration: {e}")
        print(f"\n⚠️  To restore from backup:")
        print(f"  python scripts/maintenance/restore-config-backup.py {backup_file}")
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 80)
    print("✅ SUCCESS")
    print("=" * 80)
    print("\nSystem configuration has been updated successfully!")
    print(f"Backup saved to: {backup_file}")
    print("\nThe new thresholds are now active for all devices and users.")
    print()


if __name__ == '__main__':
    main()
