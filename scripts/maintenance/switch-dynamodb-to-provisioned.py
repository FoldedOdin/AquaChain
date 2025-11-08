#!/usr/bin/env python3
"""
Switch DynamoDB Tables from On-Demand to Provisioned Capacity

This script updates all AquaChain DynamoDB tables from on-demand billing
to provisioned capacity mode to save costs in development environments.

Cost Savings: ~$5-10/month for low-traffic development workloads

Usage:
    python switch-dynamodb-to-provisioned.py --region ap-south-1
    python switch-dynamodb-to-provisioned.py --region ap-south-1 --dry-run
"""

import boto3
import argparse
import time
from typing import List, Dict
from botocore.exceptions import ClientError

# Configuration
DEFAULT_READ_CAPACITY = 5
DEFAULT_WRITE_CAPACITY = 5
GSI_READ_CAPACITY = 5
GSI_WRITE_CAPACITY = 5

def get_aquachain_tables(dynamodb_client, region: str) -> List[str]:
    """Get all AquaChain DynamoDB tables"""
    try:
        response = dynamodb_client.list_tables()
        all_tables = response.get('TableNames', [])
        
        # Filter for AquaChain tables
        aquachain_tables = [
            table for table in all_tables 
            if 'aquachain' in table.lower()
        ]
        
        print(f"\n✅ Found {len(aquachain_tables)} AquaChain tables in {region}")
        for table in aquachain_tables:
            print(f"   - {table}")
        
        return aquachain_tables
    
    except ClientError as e:
        print(f"❌ Error listing tables: {e}")
        return []

def get_table_info(dynamodb_client, table_name: str) -> Dict:
    """Get current table configuration"""
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        table = response['Table']
        
        billing_mode = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        
        info = {
            'name': table_name,
            'billing_mode': billing_mode,
            'status': table['TableStatus'],
            'size_bytes': table.get('TableSizeBytes', 0),
            'item_count': table.get('ItemCount', 0),
            'gsis': []
        }
        
        # Get GSI information
        if 'GlobalSecondaryIndexes' in table:
            for gsi in table['GlobalSecondaryIndexes']:
                info['gsis'].append({
                    'name': gsi['IndexName'],
                    'status': gsi['IndexStatus']
                })
        
        return info
    
    except ClientError as e:
        print(f"❌ Error describing table {table_name}: {e}")
        return None

def switch_to_provisioned(dynamodb_client, table_name: str, dry_run: bool = False) -> bool:
    """Switch a table from on-demand to provisioned capacity"""
    
    # Get current table info
    table_info = get_table_info(dynamodb_client, table_name)
    if not table_info:
        return False
    
    current_mode = table_info['billing_mode']
    
    print(f"\n📊 Table: {table_name}")
    print(f"   Current mode: {current_mode}")
    print(f"   Status: {table_info['status']}")
    print(f"   Size: {table_info['size_bytes'] / 1024 / 1024:.2f} MB")
    print(f"   Items: {table_info['item_count']:,}")
    print(f"   GSIs: {len(table_info['gsis'])}")
    
    # Check if already provisioned
    if current_mode == 'PROVISIONED':
        print(f"   ✅ Already in PROVISIONED mode - skipping")
        return True
    
    # Check if table is in a state that can be modified
    if table_info['status'] != 'ACTIVE':
        print(f"   ⚠️  Table status is {table_info['status']} - cannot modify now")
        return False
    
    if dry_run:
        print(f"   🔍 DRY RUN: Would switch to PROVISIONED mode")
        print(f"      - Table RCU: {DEFAULT_READ_CAPACITY}")
        print(f"      - Table WCU: {DEFAULT_WRITE_CAPACITY}")
        if table_info['gsis']:
            print(f"      - GSI RCU: {GSI_READ_CAPACITY} each")
            print(f"      - GSI WCU: {GSI_WRITE_CAPACITY} each")
        return True
    
    try:
        # Prepare update parameters
        update_params = {
            'TableName': table_name,
            'BillingMode': 'PROVISIONED',
            'ProvisionedThroughput': {
                'ReadCapacityUnits': DEFAULT_READ_CAPACITY,
                'WriteCapacityUnits': DEFAULT_WRITE_CAPACITY
            }
        }
        
        # Add GSI updates if they exist
        if table_info['gsis']:
            gsi_updates = []
            for gsi in table_info['gsis']:
                gsi_updates.append({
                    'Update': {
                        'IndexName': gsi['name'],
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': GSI_READ_CAPACITY,
                            'WriteCapacityUnits': GSI_WRITE_CAPACITY
                        }
                    }
                })
            update_params['GlobalSecondaryIndexUpdates'] = gsi_updates
        
        # Update the table
        print(f"   🔄 Switching to PROVISIONED mode...")
        response = dynamodb_client.update_table(**update_params)
        
        print(f"   ✅ Successfully initiated switch to PROVISIONED mode")
        print(f"      - Table RCU: {DEFAULT_READ_CAPACITY}")
        print(f"      - Table WCU: {DEFAULT_WRITE_CAPACITY}")
        if table_info['gsis']:
            print(f"      - {len(table_info['gsis'])} GSIs updated")
        
        return True
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        if error_code == 'ResourceInUseException':
            print(f"   ⚠️  Table is being updated - try again later")
        elif error_code == 'LimitExceededException':
            print(f"   ⚠️  Rate limit exceeded - wait before retrying")
        else:
            print(f"   ❌ Error: {error_code} - {error_msg}")
        
        return False

def calculate_cost_savings(num_tables: int, num_gsis: int) -> Dict:
    """Calculate estimated cost savings"""
    
    # On-demand pricing (ap-south-1)
    on_demand_write_cost = 1.4625  # per million writes
    on_demand_read_cost = 0.285    # per million reads
    
    # Estimated monthly usage for dev environment
    monthly_writes = 200000  # 200K writes
    monthly_reads = 500000   # 500K reads
    
    # On-demand cost
    on_demand_cost = (
        (monthly_writes / 1000000) * on_demand_write_cost +
        (monthly_reads / 1000000) * on_demand_read_cost
    ) * (num_tables + num_gsis)
    
    # Provisioned cost (5 RCU/WCU per table/GSI)
    # ap-south-1 pricing: $0.000735/hour per RCU, $0.000735/hour per WCU
    hours_per_month = 730
    provisioned_cost_per_unit = 0.000735 * hours_per_month
    
    provisioned_cost = (
        (DEFAULT_READ_CAPACITY + DEFAULT_WRITE_CAPACITY) * provisioned_cost_per_unit * num_tables +
        (GSI_READ_CAPACITY + GSI_WRITE_CAPACITY) * provisioned_cost_per_unit * num_gsis
    )
    
    savings = on_demand_cost - provisioned_cost
    savings_percent = (savings / on_demand_cost * 100) if on_demand_cost > 0 else 0
    
    return {
        'on_demand_usd': on_demand_cost,
        'provisioned_usd': provisioned_cost,
        'savings_usd': savings,
        'savings_percent': savings_percent,
        'on_demand_inr': on_demand_cost * 83,
        'provisioned_inr': provisioned_cost * 83,
        'savings_inr': savings * 83
    }

def main():
    parser = argparse.ArgumentParser(
        description='Switch DynamoDB tables from on-demand to provisioned capacity'
    )
    parser.add_argument(
        '--region',
        default='ap-south-1',
        help='AWS region (default: ap-south-1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--table',
        help='Specific table name to update (optional)'
    )
    parser.add_argument(
        '--rcu',
        type=int,
        default=DEFAULT_READ_CAPACITY,
        help=f'Read capacity units (default: {DEFAULT_READ_CAPACITY})'
    )
    parser.add_argument(
        '--wcu',
        type=int,
        default=DEFAULT_WRITE_CAPACITY,
        help=f'Write capacity units (default: {DEFAULT_WRITE_CAPACITY})'
    )
    
    args = parser.parse_args()
    
    # Update capacity settings if provided
    read_capacity = args.rcu
    write_capacity = args.wcu
    
    print("=" * 70)
    print("🔄 DynamoDB Capacity Mode Switcher")
    print("=" * 70)
    print(f"\nRegion: {args.region}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    print(f"Target capacity: {read_capacity} RCU / {write_capacity} WCU")
    
    # Initialize DynamoDB client
    dynamodb_client = boto3.client('dynamodb', region_name=args.region)
    
    # Get tables to update
    if args.table:
        tables = [args.table]
        print(f"\nUpdating specific table: {args.table}")
    else:
        tables = get_aquachain_tables(dynamodb_client, args.region)
    
    if not tables:
        print("\n❌ No tables found to update")
        return
    
    # Count total GSIs
    total_gsis = 0
    for table in tables:
        info = get_table_info(dynamodb_client, table)
        if info:
            total_gsis += len(info['gsis'])
    
    # Calculate cost savings
    print("\n" + "=" * 70)
    print("💰 Cost Savings Estimate")
    print("=" * 70)
    
    savings = calculate_cost_savings(len(tables), total_gsis)
    
    print(f"\nCurrent (On-Demand):")
    print(f"  ${savings['on_demand_usd']:.2f} USD/month")
    print(f"  ₹{savings['on_demand_inr']:.2f} INR/month")
    
    print(f"\nAfter Switch (Provisioned {DEFAULT_READ_CAPACITY}/{DEFAULT_WRITE_CAPACITY}):")
    print(f"  ${savings['provisioned_usd']:.2f} USD/month")
    print(f"  ₹{savings['provisioned_inr']:.2f} INR/month")
    
    print(f"\n💵 Monthly Savings:")
    print(f"  ${savings['savings_usd']:.2f} USD ({savings['savings_percent']:.1f}%)")
    print(f"  ₹{savings['savings_inr']:.2f} INR ({savings['savings_percent']:.1f}%)")
    
    # Confirm before proceeding
    if not args.dry_run:
        print("\n" + "=" * 70)
        response = input("\n⚠️  Proceed with switching tables to PROVISIONED mode? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("\n❌ Operation cancelled")
            return
    
    # Update tables
    print("\n" + "=" * 70)
    print("🔄 Updating Tables")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for table in tables:
        result = switch_to_provisioned(dynamodb_client, table, args.dry_run)
        
        if result:
            success_count += 1
        else:
            # Check if it was skipped or failed
            info = get_table_info(dynamodb_client, table)
            if info and info['billing_mode'] == 'PROVISIONED':
                skipped_count += 1
            else:
                failed_count += 1
        
        # Wait between updates to avoid throttling
        if not args.dry_run and result:
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"\nTotal tables: {len(tables)}")
    print(f"✅ Successfully updated: {success_count}")
    print(f"⏭️  Already provisioned: {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    
    if not args.dry_run and success_count > 0:
        print(f"\n💰 Estimated monthly savings: ${savings['savings_usd']:.2f} USD / ₹{savings['savings_inr']:.2f} INR")
        print("\n⏳ Note: Table updates may take a few minutes to complete.")
        print("   Check AWS Console to verify the changes.")
    
    if args.dry_run:
        print("\n🔍 This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to apply changes")
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()
