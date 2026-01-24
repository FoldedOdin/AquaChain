"""
Verify that shipment_id and tracking_number fields can be added to DeviceOrders
"""
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

def verify_shipment_fields_integration():
    """
    Verify that shipment fields can be added to DeviceOrders table
    This demonstrates DynamoDB's schema-less nature
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    orders_table = dynamodb.Table('DeviceOrders')
    
    print("="*60)
    print("Shipment Fields Integration Verification")
    print("="*60)
    
    # Test order ID
    test_order_id = f"test_order_{int(datetime.now().timestamp() * 1000)}"
    test_shipment_id = f"ship_{int(datetime.now().timestamp() * 1000)}"
    test_tracking_number = "TEST_TRACK_123456"
    
    try:
        # Step 1: Create a test order WITHOUT shipment fields
        print("\n1. Creating test order without shipment fields...")
        orders_table.put_item(
            Item={
                'orderId': test_order_id,
                'userId': 'test_user_123',
                'status': 'PENDING',
                'deviceSKU': 'AQC-001',
                'address': '123 Test St, Test City',
                'phone': '+1234567890',
                'paymentMethod': 'COD',
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            }
        )
        print(f"   ✓ Created order: {test_order_id}")
        
        # Step 2: Verify order exists without shipment fields
        print("\n2. Verifying order exists without shipment fields...")
        response = orders_table.get_item(Key={'orderId': test_order_id})
        order = response.get('Item', {})
        
        if 'shipment_id' not in order and 'tracking_number' not in order:
            print("   ✓ Order exists without shipment fields (as expected)")
        else:
            print("   ✗ Order unexpectedly has shipment fields")
            return False
        
        # Step 3: Update order to add shipment fields (simulating shipment creation)
        print("\n3. Adding shipment fields to order...")
        orders_table.update_item(
            Key={'orderId': test_order_id},
            UpdateExpression='SET shipment_id = :sid, tracking_number = :tn, #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':sid': test_shipment_id,
                ':tn': test_tracking_number,
                ':status': 'shipped',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        print(f"   ✓ Added shipment_id: {test_shipment_id}")
        print(f"   ✓ Added tracking_number: {test_tracking_number}")
        
        # Step 4: Verify fields were added successfully
        print("\n4. Verifying shipment fields were added...")
        response = orders_table.get_item(Key={'orderId': test_order_id})
        updated_order = response.get('Item', {})
        
        checks_passed = True
        
        if updated_order.get('shipment_id') == test_shipment_id:
            print(f"   ✓ shipment_id field verified: {updated_order['shipment_id']}")
        else:
            print("   ✗ shipment_id field missing or incorrect")
            checks_passed = False
        
        if updated_order.get('tracking_number') == test_tracking_number:
            print(f"   ✓ tracking_number field verified: {updated_order['tracking_number']}")
        else:
            print("   ✗ tracking_number field missing or incorrect")
            checks_passed = False
        
        if updated_order.get('status') == 'shipped':
            print(f"   ✓ status updated to: {updated_order['status']}")
        else:
            print("   ✗ status not updated correctly")
            checks_passed = False
        
        # Step 5: Test backward compatibility (query without expecting fields)
        print("\n5. Testing backward compatibility pattern...")
        shipment_id = updated_order.get('shipment_id')
        if shipment_id:
            print(f"   ✓ Safe access pattern works: found shipment_id")
        else:
            print(f"   ⚠ Safe access pattern: no shipment_id (would show basic status)")
        
        # Step 6: Cleanup test order
        print("\n6. Cleaning up test order...")
        orders_table.delete_item(Key={'orderId': test_order_id})
        print(f"   ✓ Deleted test order: {test_order_id}")
        
        # Final result
        print("\n" + "="*60)
        if checks_passed:
            print("✅ VERIFICATION PASSED")
            print("="*60)
            print("\nConclusion:")
            print("  • shipment_id and tracking_number fields can be added dynamically")
            print("  • No schema changes required to DeviceOrders table")
            print("  • Backward compatibility maintained")
            print("  • Ready for shipment tracking integration")
        else:
            print("❌ VERIFICATION FAILED")
            print("="*60)
            return False
        
        return True
        
    except ClientError as e:
        print(f"\n✗ DynamoDB error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = verify_shipment_fields_integration()
    exit(0 if success else 1)
