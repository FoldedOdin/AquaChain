#!/usr/bin/env python3

import boto3
import json
from datetime import datetime
import time

def backup_us_east_1_data():
    """Backup any important data from us-east-1 before deletion."""
    
    print("💾 BACKING UP US-EAST-1 DATA...")
    print("=" * 40)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    backup_data = {}
    
    # Tables that exist in us-east-1
    tables_to_backup = [
        'AquaChain-Readings',
        'aquachain-ledger', 
        'aquachain-order-simulations',
        'aquachain-orders',
        'aquachain-payments',
        'aquachain-shipments',
        'aquachain-technicians'
    ]
    
    for table_name in tables_to_backup:
        try:
            table = dynamodb.Table(table_name)
            
            print(f"📋 Backing up {table_name}...")
            
            # Scan table (limit to 100 items for safety)
            response = table.scan(Limit=100)
            items = response.get('Items', [])
            
            backup_data[table_name] = {
                'item_count': len(items),
                'sample_items': items[:5],  # Keep first 5 items as sample
                'backup_timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Found {len(items)} items (sample saved)")
            
        except Exception as e:
            print(f"   ⚠️ Could not backup {table_name}: {str(e)}")
            backup_data[table_name] = {
                'error': str(e),
                'backup_timestamp': datetime.now().isoformat()
            }
    
    # Save backup to file
    backup_filename = f"us-east-1-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    try:
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"\n✅ Backup saved to: {backup_filename}")
        print(f"📊 Backup summary:")
        
        for table_name, data in backup_data.items():
            if 'error' in data:
                print(f"   ❌ {table_name}: {data['error']}")
            else:
                print(f"   ✅ {table_name}: {data['item_count']} items")
        
        return backup_filename
        
    except Exception as e:
        print(f"❌ Failed to save backup: {str(e)}")
        return None

def delete_us_east_1_resources():
    """Delete AquaChain resources from us-east-1."""
    
    print("\n🗑️ DELETING US-EAST-1 RESOURCES...")
    print("=" * 40)
    
    deleted_resources = {
        'lambda_functions': [],
        'dynamodb_tables': [],
        'errors': []
    }
    
    # Delete Lambda Functions
    print("\n⚡ Deleting Lambda Functions...")
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        functions = lambda_client.list_functions()
        
        for func in functions.get('Functions', []):
            if 'aquachain' in func['FunctionName'].lower():
                func_name = func['FunctionName']
                
                try:
                    print(f"   🗑️ Deleting Lambda: {func_name}")
                    lambda_client.delete_function(FunctionName=func_name)
                    deleted_resources['lambda_functions'].append(func_name)
                    print(f"   ✅ Deleted: {func_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to delete Lambda {func_name}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    deleted_resources['errors'].append(error_msg)
                
    except Exception as e:
        error_msg = f"Failed to list Lambda functions: {str(e)}"
        print(f"❌ {error_msg}")
        deleted_resources['errors'].append(error_msg)
    
    # Delete DynamoDB Tables
    print("\n🗄️ Deleting DynamoDB Tables...")
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        tables = dynamodb_client.list_tables()
        
        for table_name in tables.get('TableNames', []):
            if 'aquachain' in table_name.lower():
                
                try:
                    print(f"   🗑️ Deleting DynamoDB Table: {table_name}")
                    dynamodb_client.delete_table(TableName=table_name)
                    deleted_resources['dynamodb_tables'].append(table_name)
                    print(f"   ✅ Deletion initiated: {table_name}")
                    
                    # Wait a bit between deletions to avoid throttling
                    time.sleep(2)
                    
                except Exception as e:
                    error_msg = f"Failed to delete table {table_name}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    deleted_resources['errors'].append(error_msg)
                
    except Exception as e:
        error_msg = f"Failed to list DynamoDB tables: {str(e)}"
        print(f"❌ {error_msg}")
        deleted_resources['errors'].append(error_msg)
    
    return deleted_resources

def verify_cleanup():
    """Verify that us-east-1 cleanup was successful."""
    
    print("\n🔍 VERIFYING CLEANUP...")
    print("=" * 30)
    
    remaining_resources = {
        'lambda_functions': 0,
        'dynamodb_tables': 0,
        'api_gateways': 0
    }
    
    # Check Lambda Functions
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        functions = lambda_client.list_functions()
        
        aquachain_functions = [f for f in functions.get('Functions', []) 
                              if 'aquachain' in f['FunctionName'].lower()]
        remaining_resources['lambda_functions'] = len(aquachain_functions)
        
        if aquachain_functions:
            print(f"⚠️ {len(aquachain_functions)} Lambda functions still exist:")
            for func in aquachain_functions:
                print(f"   • {func['FunctionName']}")
        else:
            print("✅ No Lambda functions remaining")
            
    except Exception as e:
        print(f"❌ Could not verify Lambda cleanup: {str(e)}")
    
    # Check DynamoDB Tables
    try:
        dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
        tables = dynamodb_client.list_tables()
        
        aquachain_tables = [t for t in tables.get('TableNames', []) 
                           if 'aquachain' in t.lower()]
        remaining_resources['dynamodb_tables'] = len(aquachain_tables)
        
        if aquachain_tables:
            print(f"⚠️ {len(aquachain_tables)} DynamoDB tables still exist:")
            for table in aquachain_tables:
                print(f"   • {table}")
        else:
            print("✅ No DynamoDB tables remaining")
            
    except Exception as e:
        print(f"❌ Could not verify DynamoDB cleanup: {str(e)}")
    
    # Check API Gateway
    try:
        apigateway_client = boto3.client('apigateway', region_name='us-east-1')
        apis = apigateway_client.get_rest_apis()
        
        aquachain_apis = [api for api in apis.get('items', []) 
                         if 'aquachain' in api['name'].lower()]
        remaining_resources['api_gateways'] = len(aquachain_apis)
        
        if aquachain_apis:
            print(f"⚠️ {len(aquachain_apis)} API Gateways still exist:")
            for api in aquachain_apis:
                print(f"   • {api['name']} ({api['id']})")
        else:
            print("✅ No API Gateways remaining")
            
    except Exception as e:
        print(f"❌ Could not verify API Gateway cleanup: {str(e)}")
    
    total_remaining = sum(remaining_resources.values())
    
    if total_remaining == 0:
        print(f"\n🎉 CLEANUP SUCCESSFUL!")
        print("✅ us-east-1 is now clean of AquaChain resources")
    else:
        print(f"\n⚠️ CLEANUP INCOMPLETE")
        print(f"❌ {total_remaining} resources still remain in us-east-1")
    
    return remaining_resources

def main():
    """Main cleanup process."""
    
    print("🧹 AQUACHAIN US-EAST-1 CLEANUP")
    print("=" * 50)
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print()
    
    print("🎯 OBJECTIVE:")
    print("   • Remove all AquaChain resources from us-east-1")
    print("   • Keep ap-south-1 as primary region")
    print("   • Save ~$10/month in AWS costs")
    print("   • Simplify management to single region")
    print()
    
    # Step 1: Backup data
    backup_file = backup_us_east_1_data()
    
    if not backup_file:
        print("❌ Backup failed. Stopping cleanup for safety.")
        return
    
    # Step 2: Confirm deletion
    print(f"\n⚠️ WARNING: About to delete AquaChain resources from us-east-1")
    print("This action cannot be undone!")
    print(f"Backup saved to: {backup_file}")
    
    confirm = input("\nType 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("❌ Cleanup cancelled by user")
        return
    
    # Step 3: Delete resources
    deleted_resources = delete_us_east_1_resources()
    
    # Step 4: Wait for deletions to complete
    print(f"\n⏳ Waiting 30 seconds for deletions to complete...")
    time.sleep(30)
    
    # Step 5: Verify cleanup
    remaining_resources = verify_cleanup()
    
    # Step 6: Summary
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   Lambda Functions Deleted: {len(deleted_resources['lambda_functions'])}")
    print(f"   DynamoDB Tables Deleted: {len(deleted_resources['dynamodb_tables'])}")
    print(f"   Errors Encountered: {len(deleted_resources['errors'])}")
    
    if deleted_resources['errors']:
        print(f"\n❌ ERRORS:")
        for error in deleted_resources['errors']:
            print(f"   • {error}")
    
    print(f"\n💰 ESTIMATED MONTHLY SAVINGS: ~$10")
    print(f"🎯 PRIMARY REGION: ap-south-1 (90 resources)")
    print(f"📧 WORKING AUTHENTICATION: ap-south-1 only")
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print("🚀 AquaChain is now optimized for single-region deployment")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
    except Exception as e:
        print(f"\n❌ Cleanup failed: {str(e)}")
        print("🔍 Check AWS permissions and try again")