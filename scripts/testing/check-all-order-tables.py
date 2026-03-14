#!/usr/bin/env python3
"""
Check All Order Tables
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
    
    # List all tables
    client = boto3.client('dynamodb', region_name='ap-south-1')
    tables = client.list_tables()['TableNames']
    
    print("🔍 Available DynamoDB Tables:")
    print("=" * 50)
    for table in tables:
        print(f"  - {table}")
    print()
    
    # Check order-related tables
    order_tables = [t for t in tables if 'order' in t.lower()]
    
    print("📋 Order-related tables:")
    for table_name in order_tables:
        print(f"\n🔍 Checking table: {table_name}")
        print("-" * 30)
        
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Limit=10)  # Limit to first 10 items
            
            if response['Items']:
                print(f'✅ Found {len(response["Items"])} items (showing first 10):')
                
                for i, item in enumerate(response['Items']):
                    print(f"\n📄 Item {i+1}:")
                    
                    # Show key fields
                    for key, value in item.items():
                        if key in ['PK', 'SK', 'orderId', 'status', 'customerName', 'phone', 'assignedTechnicianName', 'assignedTechnicianId', 'technicianPhone']:
                            print(f"   {key}: {value}")
                    
                    # Check if this looks like the order from the image
                    phone = str(item.get('phone', ''))
                    customer = str(item.get('customerName', ''))
                    
                    if '+918547613649' in phone or 'Karthik' in customer:
                        print("   🎯 POTENTIAL MATCH - This might be the order from the image!")
                        
                        # Show full item for this match
                        print("   📋 Full item data:")
                        print(json.dumps(item, indent=6, cls=DecimalEncoder))
                        
                        # Check technician assignment
                        tech_name = item.get('assignedTechnicianName')
                        tech_id = item.get('assignedTechnicianId')
                        
                        if not tech_name:
                            print("   ❌ ISSUE: No technician assigned!")
                            print("   🔧 FIXING: Assigning Sidharth Lenin...")
                            
                            # Update with technician assignment
                            update_expr = 'SET assignedTechnicianId = :tech_id, assignedTechnicianName = :tech_name, technicianPhone = :tech_phone'
                            
                            table.update_item(
                                Key={
                                    'PK': item['PK'],
                                    'SK': item['SK']
                                },
                                UpdateExpression=update_expr,
                                ExpressionAttributeValues={
                                    ':tech_id': '31333d7a-7031-703b-2e21-966a49444222',
                                    ':tech_name': 'Sidharth Lenin',
                                    ':tech_phone': '+911234567890'
                                }
                            )
                            
                            print("   ✅ Order updated with technician assignment!")
                        else:
                            print(f"   ✅ Order already has technician: {tech_name}")
            else:
                print('❌ No items found in this table')
                
        except Exception as e:
            print(f'❌ Error accessing table {table_name}: {e}')

if __name__ == '__main__':
    main()