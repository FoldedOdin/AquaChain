#!/usr/bin/env python3
"""
Verification script for Enhanced Consumer Ordering System DynamoDB tables
Validates table structure, GSIs, and configuration
"""

import boto3
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class OrderingTablesValidator:
    def __init__(self, region_name='us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
        self.validation_results = []
    
    def validate_table_structure(self, table_name: str, expected_structure: Dict[str, Any]) -> bool:
        """
        Validate a table's structure against expected configuration
        """
        try:
            response = self.dynamodb.describe_table(TableName=table_name)
            table = response['Table']
            
            print(f"\nValidating {table_name}...")
            
            # Check table status
            if table['TableStatus'] != 'ACTIVE':
                self.validation_results.append(f"❌ {table_name}: Table status is {table['TableStatus']}, expected ACTIVE")
                return False
            
            # Check partition key
            key_schema = {item['AttributeName']: item['KeyType'] for item in table['KeySchema']}
            expected_pk = expected_structure['partition_key']
            if expected_pk not in key_schema or key_schema[expected_pk] != 'HASH':
                self.validation_results.append(f"❌ {table_name}: Partition key mismatch")
                return False
            
            # Check sort key if expected
            if 'sort_key' in expected_structure:
                expected_sk = expected_structure['sort_key']
                if expected_sk not in key_schema or key_schema[expected_sk] != 'RANGE':
                    self.validation_results.append(f"❌ {table_name}: Sort key mismatch")
                    return False
            
            # Check GSIs
            if 'gsi_count' in expected_structure:
                expected_gsi_count = expected_structure['gsi_count']
                actual_gsi_count = len(table.get('GlobalSecondaryIndexes', []))
                if actual_gsi_count != expected_gsi_count:
                    self.validation_results.append(f"❌ {table_name}: Expected {expected_gsi_count} GSIs, found {actual_gsi_count}")
                    return False
                
                # Validate each GSI
                for gsi in table.get('GlobalSecondaryIndexes', []):
                    if gsi['IndexStatus'] != 'ACTIVE':
                        self.validation_results.append(f"❌ {table_name}: GSI {gsi['IndexName']} status is {gsi['IndexStatus']}")
                        return False
            
            # Check billing mode
            if table['BillingModeSummary']['BillingMode'] != 'PAY_PER_REQUEST':
                self.validation_results.append(f"❌ {table_name}: Expected PAY_PER_REQUEST billing mode")
                return False
            
            # Check stream
            if 'StreamSpecification' not in table:
                self.validation_results.append(f"❌ {table_name}: DynamoDB stream not enabled")
                return False
            
            # Check TTL if expected
            if expected_structure.get('has_ttl', False):
                try:
                    ttl_response = self.dynamodb.describe_time_to_live(TableName=table_name)
                    if ttl_response['TimeToLiveDescription']['TimeToLiveStatus'] != 'ENABLED':
                        self.validation_results.append(f"❌ {table_name}: TTL not enabled")
                        return False
                except Exception:
                    self.validation_results.append(f"❌ {table_name}: TTL configuration error")
                    return False
            
            self.validation_results.append(f"✅ {table_name}: All validations passed")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ {table_name}: Validation error - {e}")
            return False
    
    def validate_all_tables(self) -> bool:
        """
        Validate all Enhanced Consumer Ordering System tables
        """
        print("Validating Enhanced Consumer Ordering System DynamoDB tables...")
        print(f"Region: {self.region_name}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("-" * 60)
        
        # Define expected table structures
        expected_tables = {
            'aquachain-orders': {
                'partition_key': 'PK',
                'sort_key': 'SK',
                'gsi_count': 2,
                'has_ttl': True
            },
            'aquachain-payments': {
                'partition_key': 'PK',
                'sort_key': 'SK',
                'gsi_count': 1,
                'has_ttl': False
            },
            'aquachain-technicians': {
                'partition_key': 'PK',
                'sort_key': 'SK',
                'gsi_count': 1,
                'has_ttl': False
            },
            'aquachain-order-simulations': {
                'partition_key': 'PK',
                'sort_key': 'SK',
                'gsi_count': 0,
                'has_ttl': True
            }
        }
        
        all_valid = True
        
        for table_name, expected_structure in expected_tables.items():
            is_valid = self.validate_table_structure(table_name, expected_structure)
            if not is_valid:
                all_valid = False
        
        return all_valid
    
    def check_table_data(self, table_name: str, sample_size: int = 5) -> Dict[str, Any]:
        """
        Check if table has data and show sample items
        """
        try:
            response = self.dynamodb.scan(
                TableName=table_name,
                Limit=sample_size
            )
            
            item_count = response['Count']
            items = response.get('Items', [])
            
            return {
                'table_name': table_name,
                'item_count': item_count,
                'has_data': item_count > 0,
                'sample_items': items[:3]  # Show first 3 items
            }
            
        except Exception as e:
            return {
                'table_name': table_name,
                'error': str(e)
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'region': self.region_name,
            'validation_results': self.validation_results,
            'table_data_summary': []
        }
        
        # Check data in each table
        table_names = [
            'aquachain-orders',
            'aquachain-payments',
            'aquachain-technicians',
            'aquachain-order-simulations'
        ]
        
        for table_name in table_names:
            data_info = self.check_table_data(table_name)
            report['table_data_summary'].append(data_info)
        
        return report

def main():
    """
    Main validation function
    """
    region = 'us-east-1'
    if len(sys.argv) > 1:
        region = sys.argv[1]
    
    validator = OrderingTablesValidator(region)
    
    # Run validation
    is_valid = validator.validate_all_tables()
    
    # Generate report
    report = validator.generate_report()
    
    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    for result in validator.validation_results:
        print(result)
    
    print("\n" + "-" * 60)
    print("TABLE DATA SUMMARY")
    print("-" * 60)
    
    for table_info in report['table_data_summary']:
        if 'error' in table_info:
            print(f"❌ {table_info['table_name']}: {table_info['error']}")
        else:
            status = "✅ Has data" if table_info['has_data'] else "⚠️  Empty"
            print(f"{status} {table_info['table_name']}: {table_info['item_count']} items")
    
    print("\n" + "=" * 60)
    
    if is_valid:
        print("✅ ALL VALIDATIONS PASSED")
        print("Enhanced Consumer Ordering System tables are properly configured")
    else:
        print("❌ VALIDATION FAILED")
        print("Please check the error messages above and fix the issues")
        sys.exit(1)
    
    print("=" * 60)
    
    # Save detailed report
    report_filename = f"ordering_tables_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Detailed report saved to: {report_filename}")

if __name__ == "__main__":
    main()