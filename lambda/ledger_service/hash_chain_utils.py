"""
Hash Chain Utilities for AquaChain Ledger System
Provides cryptographic functions for hash chaining and verification
"""

import hashlib
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

class HashChainUtils:
    """
    Utility class for hash chain operations
    """
    
    @staticmethod
    def create_data_hash(data: Dict[str, Any]) -> str:
        """
        Create SHA-256 hash of data for ledger entry
        """
        # Sort keys for consistent hashing
        normalized_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized_data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_chain_hash(data_hash: str, previous_hash: str, sequence_number: int) -> str:
        """
        Create chain hash linking current entry to previous
        """
        chain_data = f"{data_hash}{previous_hash}{sequence_number}"
        return hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_chain_integrity(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify the integrity of a chain of ledger entries
        """
        if not entries:
            return {'valid': True, 'message': 'No entries to verify'}
        
        # Sort entries by sequence number
        sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
        
        results = {
            'valid': True,
            'verified_count': 0,
            'total_count': len(sorted_entries),
            'errors': [],
            'chain_breaks': []
        }
        
        for i, entry in enumerate(sorted_entries):
            sequence_number = entry['sequenceNumber']
            
            # Verify individual entry hash
            expected_chain_hash = HashChainUtils.create_chain_hash(
                entry['dataHash'],
                entry['previousHash'],
                sequence_number
            )
            
            if entry['chainHash'] != expected_chain_hash:
                results['valid'] = False
                results['errors'].append({
                    'sequence': sequence_number,
                    'type': 'invalid_hash',
                    'expected': expected_chain_hash,
                    'actual': entry['chainHash']
                })
                continue
            
            # Verify chain linkage (except for first entry)
            if i > 0:
                previous_entry = sorted_entries[i-1]
                if entry['previousHash'] != previous_entry['chainHash']:
                    results['valid'] = False
                    results['chain_breaks'].append({
                        'sequence': sequence_number,
                        'previous_sequence': previous_entry['sequenceNumber'],
                        'expected_previous_hash': previous_entry['chainHash'],
                        'actual_previous_hash': entry['previousHash']
                    })
                    continue
            
            results['verified_count'] += 1
        
        return results
    
    @staticmethod
    def create_merkle_root(hashes: List[str]) -> str:
        """
        Create Merkle root hash for batch verification
        """
        if not hashes:
            return '0' * 64
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Ensure even number of hashes
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])  # Duplicate last hash
        
        # Build Merkle tree bottom-up
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
            hashes = next_level
        
        return hashes[0]
    
    @staticmethod
    def generate_audit_proof(entries: List[Dict[str, Any]], target_sequence: int) -> Dict[str, Any]:
        """
        Generate audit proof for a specific ledger entry
        """
        target_entry = None
        for entry in entries:
            if entry['sequenceNumber'] == target_sequence:
                target_entry = entry
                break
        
        if not target_entry:
            return {'error': 'Target entry not found'}
        
        # Create audit trail
        audit_proof = {
            'target_sequence': target_sequence,
            'target_hash': target_entry['chainHash'],
            'timestamp': target_entry['timestamp'],
            'device_id': target_entry['deviceId'],
            'data_hash': target_entry['dataHash'],
            'previous_hash': target_entry['previousHash'],
            'chain_position': None,
            'merkle_proof': [],
            'verification_data': {
                'total_entries': len(entries),
                'chain_start': min(e['sequenceNumber'] for e in entries),
                'chain_end': max(e['sequenceNumber'] for e in entries)
            }
        }
        
        # Find position in sorted chain
        sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
        for i, entry in enumerate(sorted_entries):
            if entry['sequenceNumber'] == target_sequence:
                audit_proof['chain_position'] = i
                break
        
        # Generate Merkle proof path
        hashes = [entry['chainHash'] for entry in sorted_entries]
        merkle_root = HashChainUtils.create_merkle_root(hashes)
        audit_proof['merkle_root'] = merkle_root
        
        return audit_proof
    
    @staticmethod
    def verify_audit_proof(proof: Dict[str, Any]) -> bool:
        """
        Verify an audit proof
        """
        try:
            # Basic validation
            required_fields = ['target_hash', 'data_hash', 'previous_hash', 'target_sequence']
            if not all(field in proof for field in required_fields):
                return False
            
            # Verify chain hash reconstruction
            expected_hash = HashChainUtils.create_chain_hash(
                proof['data_hash'],
                proof['previous_hash'],
                proof['target_sequence']
            )
            
            return proof['target_hash'] == expected_hash
            
        except Exception:
            return False
    
    @staticmethod
    def create_checkpoint(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a checkpoint for efficient verification
        """
        if not entries:
            return {'error': 'No entries provided'}
        
        sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
        
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'entry_count': len(sorted_entries),
            'sequence_range': {
                'start': sorted_entries[0]['sequenceNumber'],
                'end': sorted_entries[-1]['sequenceNumber']
            },
            'first_entry_hash': sorted_entries[0]['chainHash'],
            'last_entry_hash': sorted_entries[-1]['chainHash'],
            'merkle_root': HashChainUtils.create_merkle_root([e['chainHash'] for e in sorted_entries]),
            'integrity_verified': True
        }
        
        # Verify integrity before creating checkpoint
        verification = HashChainUtils.verify_chain_integrity(sorted_entries)
        checkpoint['integrity_verified'] = verification['valid']
        
        if not verification['valid']:
            checkpoint['errors'] = verification['errors']
            checkpoint['chain_breaks'] = verification['chain_breaks']
        
        return checkpoint
    
    @staticmethod
    def validate_checkpoint(checkpoint: Dict[str, Any], entries: List[Dict[str, Any]]) -> bool:
        """
        Validate entries against a checkpoint
        """
        try:
            if not entries:
                return False
            
            sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
            
            # Check entry count
            if len(sorted_entries) != checkpoint['entry_count']:
                return False
            
            # Check sequence range
            if (sorted_entries[0]['sequenceNumber'] != checkpoint['sequence_range']['start'] or
                sorted_entries[-1]['sequenceNumber'] != checkpoint['sequence_range']['end']):
                return False
            
            # Check first and last entry hashes
            if (sorted_entries[0]['chainHash'] != checkpoint['first_entry_hash'] or
                sorted_entries[-1]['chainHash'] != checkpoint['last_entry_hash']):
                return False
            
            # Check Merkle root
            merkle_root = HashChainUtils.create_merkle_root([e['chainHash'] for e in sorted_entries])
            if merkle_root != checkpoint['merkle_root']:
                return False
            
            return True
            
        except Exception:
            return False