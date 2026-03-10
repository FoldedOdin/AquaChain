#!/usr/bin/env python3
"""
Clean up test orders from DynamoDB
Removes:
- All CANCELLED orders
- Orders older than 7 days
- Optionally: all orders (with --all flag)
"""
import boto3
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
TABLE_NAME = 'aquachain-orders'
REGION = 'ap-south-1'

def cleanup_orders(delete_all=False, dry_run=True):
    """
    Clean up test orders from DynamoDB
    
    Args:
        delete_all: If True, delete ALL orders (use with caution!)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    
    print(f"{'DRY RUN - ' if dry_run else ''}Scanning orders table...")
    
    # Scan all orders
    response = table.scan()
    orders = response.get('Items', [])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        orders.extend(response.get('Items', []))
    
    print(f"Found {len(orders)} total orders")
    
    # Filter orders to delete
    orders_to_delete = []
    cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
    
    for order in orders:
        order_id = order.get('orderId')
        status = order.get('status', '')
        created_at = order.get('createdAt', '')
        
        should_delete = False
        reason = ''
        
        if delete_all:
            should_delete = True
            reason = 'Delete all flag'
        elif status == 'CANCELLED':
            should_delete = True
            reason = 'Status: CANCELLED'
        elif created_at < cutoff_date:
            should_delete = True
            reason = f'Older than 7 days (created: {created_at})'
        
        if should_delete:
            orders_to_delete.append({
                'orderId': order_id,
                'status': status,
                'createdAt': created_at,
                'reason': reason
            })
    
    print(f"\n{'Would delete' if dry_run else 'Deleting'} {len(orders_to_delete)} orders:")
    print("-" * 80)
    
    for i, order in enumerate(orders_to_delete, 1):
        print(f"{i}. {order['orderId'][:20]}... | {order['status']:15} | {order['createdAt'][:10]} | {order['reason']}")
    
    if not orders_to_delete:
        print("No orders to delete!")
        return
    
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - No orders were actually deleted")
        print("Run with --execute flag to actually delete these orders")
        print("=" * 80)
        return
    
    # Confirm deletion
    if not delete_all:
        confirm = input(f"\nAre you sure you want to delete {len(orders_to_delete)} orders? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled")
            return
    else:
        confirm = input(f"\n⚠️  WARNING: You are about to delete ALL {len(orders_to_delete)} orders! Type 'DELETE ALL' to confirm: ")
        if confirm != 'DELETE ALL':
            print("Deletion cancelled")
            return
    
    # Delete orders
    deleted_count = 0
    failed_count = 0
    
    for order in orders_to_delete:
        try:
            table.delete_item(Key={'orderId': order['orderId']})
            deleted_count += 1
            print(f"✓ Deleted {order['orderId']}")
        except Exception as e:
            failed_count += 1
            print(f"✗ Failed to delete {order['orderId']}: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"Cleanup complete!")
    print(f"  Deleted: {deleted_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Remaining: {len(orders) - deleted_count}")
    print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up test orders from DynamoDB')
    parser.add_argument('--execute', action='store_true', help='Actually delete orders (default is dry-run)')
    parser.add_argument('--all', action='store_true', help='Delete ALL orders (use with extreme caution!)')
    
    args = parser.parse_args()
    
    if args.all and not args.execute:
        print("ERROR: --all flag requires --execute flag")
        sys.exit(1)
    
    cleanup_orders(delete_all=args.all, dry_run=not args.execute)
