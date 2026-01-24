# Shipment Fields in DeviceOrders Table

## Overview

The DeviceOrders table now supports shipment tracking through two additional fields:
- `shipment_id`: Links to the Shipments table for detailed tracking
- `tracking_number`: Quick reference to the courier tracking number

## DynamoDB Schema-less Design

DynamoDB is schema-less, which means:
- Fields don't need to be pre-defined in the table schema
- New fields can be added to items dynamically
- Only key attributes (primary key and GSI keys) need to be defined upfront

## Field Specifications

### shipment_id (String)
- **Purpose**: Foreign key linking to the Shipments table
- **Format**: `ship_<timestamp>` (e.g., `ship_1735478400000`)
- **Added when**: Order status changes to "shipped"
- **Usage**: Query the Shipments table for detailed tracking information

### tracking_number (String)
- **Purpose**: Quick reference to courier tracking number
- **Format**: Courier-specific (e.g., `DELHUB123456789`)
- **Added when**: Shipment is created with courier
- **Usage**: Display tracking number to users without additional queries

## Backward Compatibility

### Existing Orders
- Orders created before shipment tracking implementation will NOT have these fields
- This is perfectly fine in DynamoDB - missing fields are simply absent
- Code must handle both cases:
  ```python
  # Safe access pattern
  shipment_id = order.get('shipment_id')
  if shipment_id:
      # Order has shipment tracking
      shipment = get_shipment(shipment_id)
  else:
      # Legacy order without shipment tracking
      show_basic_status(order['status'])
  ```

### New Orders
- Orders marked as "shipped" after implementation will have both fields
- Fields are added atomically during shipment creation transaction

## Implementation Example

### Creating a Shipment (Lambda function)
```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table('DeviceOrders')
shipments_table = dynamodb.Table('aquachain-shipments')

def create_shipment(order_id, tracking_number):
    shipment_id = f"ship_{int(datetime.now().timestamp() * 1000)}"
    
    # Atomic transaction
    dynamodb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Put': {
                    'TableName': 'aquachain-shipments',
                    'Item': {
                        'shipment_id': {'S': shipment_id},
                        'order_id': {'S': order_id},
                        'tracking_number': {'S': tracking_number},
                        # ... other shipment fields
                    }
                }
            },
            {
                'Update': {
                    'TableName': 'DeviceOrders',
                    'Key': {'orderId': {'S': order_id}},
                    'UpdateExpression': 'SET shipment_id = :sid, tracking_number = :tn, #status = :status',
                    'ExpressionAttributeNames': {
                        '#status': 'status'
                    },
                    'ExpressionAttributeValues': {
                        ':sid': {'S': shipment_id},
                        ':tn': {'S': tracking_number},
                        ':status': {'S': 'shipped'}
                    }
                }
            }
        ]
    )
```

### Querying Orders with Shipment Info
```python
def get_order_with_shipment(order_id):
    # Get order
    response = orders_table.get_item(Key={'orderId': order_id})
    order = response.get('Item', {})
    
    # Check if order has shipment tracking
    if 'shipment_id' in order:
        # Get detailed shipment info
        shipment_response = shipments_table.get_item(
            Key={'shipment_id': order['shipment_id']}
        )
        order['shipment_details'] = shipment_response.get('Item', {})
    
    return order
```

## Verification

To verify the fields can be added successfully:

```bash
# Run the verification script
python infrastructure/dynamodb/verify_shipment_fields.py
```

## Migration Notes

### No Migration Required
- Existing orders continue to work without modification
- No data migration script needed
- Fields are added organically as orders are shipped

### Monitoring
- Monitor for orders with `status='shipped'` but missing `shipment_id`
- These indicate shipment creation failures that need investigation

## Testing

### Test Scenarios
1. **Create new order** → Should NOT have shipment fields
2. **Mark order as shipped** → Should add both fields atomically
3. **Query old order** → Should handle missing fields gracefully
4. **Query new shipped order** → Should return shipment fields

### Test Script
```python
# Test backward compatibility
def test_backward_compatibility():
    # Create order without shipment fields
    orders_table.put_item(Item={
        'orderId': 'test_order_1',
        'userId': 'user_123',
        'status': 'PENDING',
        'createdAt': '2025-01-01T00:00:00Z'
    })
    
    # Query should work fine
    response = orders_table.get_item(Key={'orderId': 'test_order_1'})
    order = response['Item']
    
    # Safe access
    assert 'shipment_id' not in order
    assert order['status'] == 'PENDING'
    
    print("✓ Backward compatibility test passed")
```

## Summary

✅ **No schema changes required** - DynamoDB handles new fields automatically  
✅ **Backward compatible** - Existing orders work without modification  
✅ **Atomic updates** - Fields added in transaction with shipment creation  
✅ **Safe access patterns** - Code uses `.get()` to handle missing fields  
✅ **No migration needed** - Fields added organically as orders ship  

The shipment tracking integration is designed to be non-breaking and seamlessly extend the existing order management system.
