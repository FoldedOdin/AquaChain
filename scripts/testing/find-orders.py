#!/usr/bin/env python3
"""
Find Orders in Database
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

    print("🔍 Searching for all orders...")
    print("=" * 50)
    
    try:
        # Scan for all orders
        response = orders_table.scan()
        
        if response['Items']:
            print(f'✅ Found {len(response["Items"])} orders:')
            print()
            
            for item in response['Items']:
                order_id = item.get('PK', '').replace('ORDER#', '')
                status = item.get('status', 'N/A')
                customer = item.get('customerName', 'N/A')
                phone = item.get('phone', 'N/A')
                tech_name = item.get('assignedTechnicianName', 'N/A')
                tech_id = item.get('assignedTechnicianId', 'N/A')
                
                print(f"📋 Order: {order_id}")
                print(f"   Status: {status}")
                print(f"   Customer: {customer}")
                print(f"   Phone: {phone}")
                print(f"   Technician: {tech_name}")
                print(f"   Tech ID: {tech_id}")
                print()
                
                # Check if this matches the order from the image
                if phone == '+918547613649' or customer == 'Karthik K Pradeep':
                    print("🎯 FOUND MATCHING ORDER!")
                    print("   This appears to be the order from the image")
                    
                    # Check technician assignment
                    if not tech_name or tech_name == 'N/A':
                        print("❌ ISSUE: No technician assigned!")
                        print("🔧 FIXING: Assigning Sidharth Lenin...")
                        
                        # Update with technician assignment
                        orders_table.update_item(
                            Key={
                                'PK': item['PK'],
                                'SK': item['SK']
                            },
                            UpdateExpression='SET assignedTechnicianId = :tech_id, assignedTechnicianName = :tech_name, technicianPhone = :tech_phone',
                            ExpressionAttributeValues={
                                ':tech_id': '31333d7a-7031-703b-2e21-966a49444222',
                                ':tech_name': 'Sidharth Lenin',
                                ':tech_phone': '+911234567890'
                            }
                        )
                        
                        print("✅ Order updated with technician assignment!")
                    else:
                        print("✅ Order already has technician assigned")
                    
                    print("-" * 30)
        else:
            print('❌ No orders found in database')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    main()