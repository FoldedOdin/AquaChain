#!/usr/bin/env python3
"""
Restore System Configuration from Backup

This script restores a system configuration from a backup file created by
fix-system-config-thresholds.py

Usage:
    python scripts/maintenance/restore-config-backup.py config-backup-20260227-123456.json --region ap-south-1
"""

import boto3
import json
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
import argparse


def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert floats to Decimal for DynamoDB compatibility"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def main():
    parser = argparse.ArgumentParser(description='Restore system configuration from backup')
    parser.add_argument('backup_file', help='Path to backup JSON file')
    parser.add_argument('--region', default='ap-south-1', help='AWS region')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    config_table = 'AquaChain-SystemConfig'
    history_table = 'AquaChain-ConfigHistory'
    
    print("=" * 80)
    print("🔄 AquaChain - Restore Configuration from Backup")
    print("=" * 80)
    print()
    print(f"Backup file: {args.backup_file}")
    print(f"Region: {args.region}")
    print(f"Config Table: {config_table}")
    print()
    
    # Load backup file
    try:
        with open(args.backup_file, 'r') as f:
            backup_config = json.load(f)
        print("✅ Backup file loaded successfully")
    except FileNotFoundError:
        print(f"❌ Backup file not found: {args.backup_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in backup file: {e}")
        sys.exit(1)
    
    # Initialize AWS clients
    try:
        dynamodb = boto3.resource('dynamodb', region_name=args.region)
        print("✅ Connected to DynamoDB")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        sys.exit(1)
    
    # Confirmation
    if not args.yes:
        print("\n" + "=" * 80)
        print("⚠️  CONFIRMATION REQUIRED")
        print("=" * 80)
        print("\nThis will restore the system configuration from the backup.")
        print("All current settings will be replaced.")
        print()
        
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n❌ Restore cancelled by user")
            sys.exit(0)
    
    # Restore configuration
    print("\n" + "=" * 80)
    print("Restoring configuration...")
    print("=" * 80)
    
    try:
        config_table_obj = dynamodb.Table(config_table)
        history_table_obj = dynamodb.Table(history_table)
        
        # Generate version for restore
        version_timestamp = datetime.utcnow().isoformat()
        version_id = f"v_restore_{version_timestamp}"
        
        # Update configuration
        backup_config['version'] = version_id
        backup_config['updated_at'] = version_timestamp
        backup_config['updated_by'] = 'system-restore'
        
        config_for_db = convert_floats_to_decimal(backup_config)
        config_table_obj.put_item(Item=config_for_db)
        
        # Log to history
        history_entry = {
            'configId': 'SYSTEM_CONFIG',
            'version': version_id,
            'updatedBy': 'system-restore',
            'updatedAt': version_timestamp,
            'previousVersion': backup_config.get('version', 'unknown'),
            'changes': {'restore': f'Restored from backup: {args.backup_file}'},
            'fullConfig': config_for_db,
            'ipAddress': 'localhost-restore-script'
        }
        
        history_table_obj.put_item(Item=convert_floats_to_decimal(history_entry))
        
        print("✅ Configuration restored successfully")
        print(f"✅ Version: {version_id}")
        
    except Exception as e:
        print(f"\n❌ Failed to restore configuration: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS")
    print("=" * 80)
    print("\nConfiguration has been restored from backup!")
    print()


if __name__ == '__main__':
    main()
