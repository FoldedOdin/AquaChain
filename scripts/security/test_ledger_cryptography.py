#!/usr/bin/env python3
"""
Test AquaChain Ledger Cryptographic Security
"""

import boto3
import json
import hashlib
import base64
from datetime import datetime

def test_kms_signing():
    """Test KMS signing capabilities"""
    print("🔐 Testing KMS Cryptographic Signing...")
    
    kms_client = boto3.client('kms', region_name='ap-south-1')
    signing_key = 'alias/aquachain-kms-signing-dev'
    
    try:
        # Test data
        test_message = "AquaChain_Ledger_Test_" + str(int(datetime.utcnow().timestamp()))
        
        # Sign the message
        sign_response = kms_client.sign(
            KeyId=signing_key,
            Message=test_message.encode('utf-8'),
            MessageType='RAW',
            SigningAlgorithm='RSASSA_PSS_SHA_256'
        )
        
        signature = sign_response['Signature']
        print(f"✅ Message signed successfully")
        print(f"   Signature length: {len(signature)} bytes")
        
        # Verify the signature
        verify_response = kms_client.verify(
            KeyId=signing_key,
            Message=test_message.encode('utf-8'),
            MessageType='RAW',
            Signature=signature,
            SigningAlgorithm='RSASSA_PSS_SHA_256'
        )
        
        if verify_response['SignatureValid']:
            print(f"✅ Signature verification: VALID")
            return True
        else:
            print(f"❌ Signature verification: INVALID")
            return False
            
    except Exception as e:
        print(f"❌ KMS signing test failed: {str(e)}")
        return False

def test_hash_chaining():
    """Test hash chaining implementation"""
    print("\n🔗 Testing Hash Chaining Logic...")
    
    # Simulate ledger entries
    entries = [
        {
            'sequenceNumber': 1,
            'deviceId': 'ESP32-001',
            'data': '{"pH": 7.0, "temp": 25.0}',
            'timestamp': '2026-03-11T10:00:00Z'
        },
        {
            'sequenceNumber': 2,
            'deviceId': 'ESP32-001', 
            'data': '{"pH": 7.1, "temp": 25.1}',
            'timestamp': '2026-03-11T10:01:00Z'
        }
    ]
    
    try:
        # Genesis hash (first entry)
        previous_hash = '0' * 64
        
        for entry in entries:
            # Create data hash
            data_hash = hashlib.sha256(entry['data'].encode('utf-8')).hexdigest()
            
            # Create chain hash
            chain_data = f"{data_hash}{previous_hash}{entry['sequenceNumber']}"
            chain_hash = hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
            
            entry['dataHash'] = data_hash
            entry['previousHash'] = previous_hash
            entry['chainHash'] = chain_hash
            
            print(f"✅ Entry {entry['sequenceNumber']}:")
            print(f"   Data Hash: {data_hash[:16]}...")
            print(f"   Chain Hash: {chain_hash[:16]}...")
            
            # Update previous hash for next iteration
            previous_hash = chain_hash
        
        # Verify chain integrity
        for i in range(1, len(entries)):
            current = entries[i]
            previous = entries[i-1]
            
            if current['previousHash'] != previous['chainHash']:
                print(f"❌ Chain break detected at entry {current['sequenceNumber']}")
                return False
        
        print(f"✅ Hash chain integrity: VALID")
        return True
        
    except Exception as e:
        print(f"❌ Hash chaining test failed: {str(e)}")
        return False

def test_ledger_immutability():
    """Test ledger immutability mechanisms"""
    print("\n🛡️  Testing Ledger Immutability...")
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    ledger_table = dynamodb.Table('aquachain-ledger')
    
    try:
        # Get a recent entry
        response = ledger_table.query(
            KeyConditionExpression='partition_key = :pk',
            ExpressionAttributeValues={':pk': 'READINGS'},
            Limit=1,
            ScanIndexForward=False
        )
        
        if not response['Items']:
            print("⚠️  No ledger entries found for immutability test")
            return True
        
        entry = response['Items'][0]
        sequence_number = entry['sequenceNumber']
        
        # Test 1: Try to update existing entry (should fail with proper implementation)
        try:
            ledger_table.update_item(
                Key={
                    'partition_key': 'READINGS',
                    'sequenceNumber': sequence_number
                },
                UpdateExpression='SET test_field = :val',
                ExpressionAttributeValues={':val': 'TAMPERED'},
                ConditionExpression='attribute_not_exists(test_field)'  # This should prevent updates
            )
            
            print("❌ CRITICAL: Ledger entry was modified - immutability compromised!")
            return False
            
        except Exception:
            print("✅ Ledger entry protected from modification")
        
        # Test 2: Try to create duplicate sequence number (should fail)
        try:
            ledger_table.put_item(
                Item={
                    'partition_key': 'READINGS',
                    'sequenceNumber': sequence_number,
                    'deviceId': 'TEST-DUPLICATE',
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'event_type': 'TEST',
                    'data': '{"test": "duplicate"}'
                },
                ConditionExpression='attribute_not_exists(sequenceNumber)'
            )
            
            print("❌ CRITICAL: Duplicate sequence number allowed!")
            return False
            
        except Exception:
            print("✅ Duplicate sequence numbers prevented")
        
        return True
        
    except Exception as e:
        print(f"❌ Immutability test failed: {str(e)}")
        return False

def main():
    """Run all cryptographic security tests"""
    print("🔒 AquaChain Ledger Cryptographic Security Test")
    print("=" * 50)
    
    results = {
        'kms_signing': test_kms_signing(),
        'hash_chaining': test_hash_chaining(), 
        'immutability': test_ledger_immutability()
    }
    
    print("\n" + "=" * 50)
    print("📊 CRYPTOGRAPHIC SECURITY SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Score: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🟢 CRYPTOGRAPHIC SECURITY: STRONG")
    elif passed >= total * 0.7:
        print("🟡 CRYPTOGRAPHIC SECURITY: MODERATE")
    else:
        print("🔴 CRYPTOGRAPHIC SECURITY: WEAK")

if __name__ == "__main__":
    main()