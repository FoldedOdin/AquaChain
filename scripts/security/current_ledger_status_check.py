#!/usr/bin/env python3
"""
Current AquaChain Ledger Security Status Check
Real-time verification of ledger security implementation
"""

import boto3
import json
import hashlib
from datetime import datetime

def check_current_ledger_status():
    """Check the actual current status of ledger security"""
    print("🔍 CURRENT LEDGER SECURITY STATUS CHECK")
    print("=" * 50)
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    ledger_table = dynamodb.Table('aquachain-ledger')
    
    # 1. Check recent entries structure
    print("\n1. 📋 Checking Recent Ledger Entry Structure...")
    try:
        response = ledger_table.query(
            KeyConditionExpression='partition_key = :pk',
            ExpressionAttributeValues={':pk': 'READINGS'},
            Limit=1,
            ScanIndexForward=False
        )
        
        if response['Items']:
            entry = response['Items'][0]
            print(f"   Latest Entry Sequence: {entry['sequenceNumber']}")
            print(f"   Device ID: {entry['deviceId']}")
            print(f"   Timestamp: {entry['timestamp']}")
            
            # Check for security fields
            security_fields = ['dataHash', 'previousHash', 'chainHash', 'kmsSignature']
            missing_fields = []
            
            for field in security_fields:
                if field in entry:
                    print(f"   ✅ {field}: Present")
                else:
                    print(f"   ❌ {field}: MISSING")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   🚨 CRITICAL: Missing security fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ All security fields present")
        else:
            print("   ⚠️  No ledger entries found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking entry structure: {str(e)}")
        return False
    
    # 2. Test immutability
    print("\n2. 🛡️  Testing Current Immutability...")
    try:
        # Try to modify the latest entry
        sequence_number = entry['sequenceNumber']
        
        try:
            ledger_table.update_item(
                Key={
                    'partition_key': 'READINGS',
                    'sequenceNumber': sequence_number
                },
                UpdateExpression='SET immutability_test = :val',
                ExpressionAttributeValues={':val': 'BREACH_ATTEMPT'},
                ConditionExpression='attribute_not_exists(immutability_test)'
            )
            
            print("   ❌ CRITICAL: Ledger entry was modified - immutability FAILED")
            
            # Clean up the test modification
            ledger_table.update_item(
                Key={
                    'partition_key': 'READINGS',
                    'sequenceNumber': sequence_number
                },
                UpdateExpression='REMOVE immutability_test'
            )
            return False
            
        except Exception:
            print("   ✅ Ledger entry protected from modification")
            
    except Exception as e:
        print(f"   ❌ Error testing immutability: {str(e)}")
        return False
    
    # 3. Check KMS key availability
    print("\n3. 🔐 Checking KMS Key Status...")
    try:
        kms_client = boto3.client('kms', region_name='ap-south-1')
        key_info = kms_client.describe_key(KeyId='alias/aquachain-kms-signing-dev')
        key_state = key_info['KeyMetadata']['KeyState']
        
        if key_state == 'Enabled':
            print(f"   ✅ KMS signing key: {key_state}")
        else:
            print(f"   ❌ KMS signing key: {key_state}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking KMS key: {str(e)}")
        return False
    
    # 4. Check table configuration
    print("\n4. 🏗️  Checking Table Security Configuration...")
    try:
        client = boto3.client('dynamodb', region_name='ap-south-1')
        table_info = client.describe_table(TableName='aquachain-ledger')
        
        # Check deletion protection
        deletion_protection = table_info['Table'].get('DeletionProtectionEnabled', False)
        print(f"   Deletion Protection: {'✅ Enabled' if deletion_protection else '❌ Disabled'}")
        
        # Check point-in-time recovery
        backup_info = client.describe_continuous_backups(TableName='aquachain-ledger')
        pitr_status = backup_info['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus']
        print(f"   Point-in-Time Recovery: {'✅ Enabled' if pitr_status == 'ENABLED' else '❌ Disabled'}")
        
        # Check streams
        stream_enabled = table_info['Table'].get('StreamSpecification', {}).get('StreamEnabled', False)
        print(f"   DynamoDB Streams: {'✅ Enabled' if stream_enabled else '❌ Disabled'}")
        
    except Exception as e:
        print(f"   ❌ Error checking table configuration: {str(e)}")
        return False
    
    # 5. Check Lambda functions
    print("\n5. ⚡ Checking Lambda Function Deployment...")
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        expected_functions = [
            'aquachain-function-ledger-service-dev',
            'aquachain-function-ledger-backup-service-dev',
            'aquachain-function-ledger-verification-service-dev'
        ]
        
        for func_name in expected_functions:
            try:
                lambda_client.get_function(FunctionName=func_name)
                print(f"   ✅ {func_name}: Deployed")
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"   ❌ {func_name}: NOT DEPLOYED")
                
    except Exception as e:
        print(f"   ❌ Error checking Lambda functions: {str(e)}")
    
    # 6. Summary
    print("\n" + "=" * 50)
    print("📊 CURRENT SECURITY STATUS SUMMARY")
    print("=" * 50)
    
    return True

def main():
    """Main execution"""
    try:
        status = check_current_ledger_status()
        
        if status:
            print("🟢 Basic ledger infrastructure is operational")
        else:
            print("🔴 Critical security issues detected")
            
        print(f"\n📅 Check completed at: {datetime.utcnow().isoformat()}Z")
        
    except Exception as e:
        print(f"💥 Status check failed: {str(e)}")

if __name__ == "__main__":
    main()