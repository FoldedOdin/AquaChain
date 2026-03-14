#!/usr/bin/env python3
"""
Check Order Assignment Status
"""

import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def main():
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    orders_table = dynamodb.Table('aquachain-orders')

    # Get the specific order from the image
    order_id = 'ord_17734098'
    
    print(f"🔍 Checking Order: {order_id}")
    print("=" * 50)
    
    try:
        response = orders_table.get_item(
            Key={
                'PK': f'ORDER#{order_id}',
                'SK': f'ORDER#{order_id}'
            }
        )
        
        if 'Item' in response:
            order = response['Item']
            print('✅ Order Found!')
            print(f'Order ID: {order_id}')
            print(f'Status: {order.get("status", "N/A")}')
            print(f'Assigned Technician ID: {order.get("assignedTechnicianId", "N/A")}')
            print(f'Assigned Technician Name: {order.get("assignedTechnicianName", "N/A")}')
            print(f'Technician Phone: {order.get("technicianPhone", "N/A")}')
            print(f'Customer: {order.get("customerName", "N/A")}')
            print(f'Phone: {order.get("phone", "N/A")}')
            print()
            
            # Check if technician assignment fields exist
            has_technician_id = bool(order.get("assignedTechnicianId"))
            has_technician_name = bool(order.get("assignedTechnicianName"))
            has_technician_phone = bool(order.get("technicianPhone"))
            
            print("🔧 Technician Assignment Status:")
            print(f"  Has Technician ID: {'✅' if has_technician_id else '❌'}")
            print(f"  Has Technician Name: {'✅' if has_technician_name else '❌'}")
            print(f"  Has Technician Phone: {'✅' if has_technician_phone else '❌'}")
            
            if not (has_technician_id and has_technician_name):
                print("\n❌ ISSUE IDENTIFIED:")
                print("   Order is missing technician assignment details!")
                print("   This is why the 'Technician Assigned' step appears grayed out.")
                
                # Let's assign Sidharth to this order
                print("\n🔧 FIXING: Assigning Sidharth Lenin to this order...")
                
                # Update the order with technician assignment
                orders_table.update_item(
                    Key={
                        'PK': f'ORDER#{order_id}',
                        'SK': f'ORDER#{order_id}'
                    },
                    UpdateExpression='SET assignedTechnicianId = :tech_id, assignedTechnicianName = :tech_name, technicianPhone = :tech_phone, #status = :status',
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':tech_id': '31333d7a-7031-703b-2e21-966a49444222',
                        ':tech_name': 'Sidharth Lenin',
                        ':tech_phone': '+911234567890',
                        ':status': 'assigned'
                    }
                )
                
                print("✅ Order updated with technician assignment!")
                print("   - Technician: Sidharth Lenin")
                print("   - Phone: +911234567890")
                print("   - Status: assigned")
                
            else:
                print("\n✅ Order has proper technician assignment")
            
        else:
            print(f'❌ Order {order_id} not found')
            
            # Try to find orders with similar ID
            print('\n🔍 Searching for similar orders...')
            response = orders_table.scan(
                FilterExpression='contains(PK, :order_prefix)',
                ExpressionAttributeValues={':order_prefix': 'ord_177340'}
            )
            
            if response['Items']:
                print(f'Found {len(response["Items"])} similar orders:')
                for item in response['Items']:
                    order_pk = item['PK'].replace('ORDER#', '')
                    print(f'  - {order_pk} (Status: {item.get("status", "N/A")})')
            else:
                print('No similar orders found')
                
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    main()