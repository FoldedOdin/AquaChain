# Shipment Tracking Infrastructure - Quick Start Guide

## 🚀 Quick Setup

### 1. Create Tables
```bash
# Create Shipments table
python infrastructure/dynamodb/shipments_table.py

# Create DeviceOrders table
python infrastructure/dynamodb/device_orders_table.py
```

### 2. Verify Setup
```bash
# Verify shipment tracking infrastructure
python infrastructure/dynamodb/verify_shipment_tracking_tables.py
```

### 3. Test Integration
```bash
# Test shipment field integration
python infrastructure/dynamodb/verify_shipment_fields.py
```

---

## 📚 Table Reference

### Shipments Table
- **Name:** `aquachain-shipments`
- **Primary Key:** `shipment_id`
- **GSIs:** `order_id-index`, `tracking_number-index`, `status-created_at-index`

### DeviceOrders Table
- **Name:** `DeviceOrders`
- **Primary Key:** `orderId`
- **GSIs:** `userId-createdAt-index`, `status-createdAt-index`
- **Dynamic Fields:** `shipment_id`, `tracking_number`

---

## 💻 Code Examples

### Create Shipment (Python)
```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
shipments_table = dynamodb.Table('aquachain-shipments')
orders_table = dynamodb.Table('DeviceOrders')

# Atomic transaction
dynamodb.meta.client.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': 'aquachain-shipments',
                'Item': {
                    'shipment_id': {'S': 'ship_123'},
                    'order_id': {'S': 'ord_456'},
                    'tracking_number': {'S': 'TRACK789'},
                    'internal_status': {'S': 'shipment_created'},
                    'created_at': {'S': datetime.utcnow().isoformat()}
                }
            }
        },
        {
            'Update': {
                'TableName': 'DeviceOrders',
                'Key': {'orderId': {'S': 'ord_456'}},
                'UpdateExpression': 'SET shipment_id = :sid, tracking_number = :tn',
                'ExpressionAttributeValues': {
                    ':sid': {'S': 'ship_123'},
                    ':tn': {'S': 'TRACK789'}
                }
            }
        }
    ]
)
```

### Query Shipment by Order ID
```python
response = shipments_table.query(
    IndexName='order_id-index',
    KeyConditionExpression='order_id = :oid',
    ExpressionAttributeValues={':oid': 'ord_456'}
)
shipment = response['Items'][0]
```

### Query Shipment by Tracking Number
```python
response = shipments_table.query(
    IndexName='tracking_number-index',
    KeyConditionExpression='tracking_number = :tn',
    ExpressionAttributeValues={':tn': 'TRACK789'}
)
shipment = response['Items'][0]
```

### Safe Access Pattern (Backward Compatibility)
```python
# Get order
order = orders_table.get_item(Key={'orderId': 'ord_456'})['Item']

# Safe access to shipment fields
shipment_id = order.get('shipment_id')
if shipment_id:
    # Order has shipment tracking
    shipment = shipments_table.get_item(Key={'shipment_id': shipment_id})['Item']
    print(f"Tracking: {shipment['tracking_number']}")
else:
    # Legacy order without tracking
    print(f"Status: {order['status']}")
```

---

## 🔍 Troubleshooting

### Table Not Found
```bash
# Check if tables exist
python infrastructure/dynamodb/check_device_orders_table.py
python infrastructure/dynamodb/verify_shipments_table.py

# Create missing tables
python infrastructure/dynamodb/setup_all_tables.py
```

### Field Integration Issues
```bash
# Test field integration
python infrastructure/dynamodb/verify_shipment_fields.py
```

### Verification Failed
```bash
# Run comprehensive verification
python infrastructure/dynamodb/verify_shipment_tracking_tables.py
```

---

## 📖 Documentation

- **Field Integration Guide:** `SHIPMENT_FIELDS_GUIDE.md`
- **Task Completion Summary:** `TASK_1_COMPLETION_SUMMARY.md`
- **Design Document:** `.kiro/specs/shipment-tracking-automation/design.md`
- **Requirements:** `.kiro/specs/shipment-tracking-automation/requirements.md`

---

## ✅ Verification Checklist

- [ ] Shipments table created with 3 GSIs
- [ ] DeviceOrders table created with 2 GSIs
- [ ] DynamoDB Streams enabled on both tables
- [ ] Billing mode set to PAY_PER_REQUEST
- [ ] Field integration test passed
- [ ] Backward compatibility verified

---

## 🎯 Next Steps

1. Deploy Lambda functions:
   - `create_shipment`
   - `webhook_handler`
   - `get_shipment_status`

2. Configure API Gateway endpoints:
   - `POST /api/shipments`
   - `POST /api/webhooks/:courier`
   - `GET /api/shipments/:shipmentId`

3. Register webhook URLs with courier services

---

*For detailed information, see the full documentation in the `.kiro/specs/shipment-tracking-automation/` directory.*
