# Shipment Tracking Database Infrastructure

## Overview

This directory contains the DynamoDB table definitions and management scripts for the AquaChain shipment tracking subsystem.

## 📁 Files

### Core Table Definitions
- **`shipments_table.py`** - Shipments table with GSIs for tracking
- **`device_orders_table.py`** - DeviceOrders table for order management
- **`tables.py`** - Core system tables (readings, ledger, users, etc.)
- **`contact_table.py`** - Contact form submissions table

### Setup Scripts
- **`setup_all_tables.py`** - Master script to create all tables
- **`QUICK_START.md`** - Quick start guide for developers

### Verification Scripts
- **`verify_shipment_tracking_tables.py`** - Comprehensive verification ⭐
- **`verify_shipments_table.py`** - Verify Shipments table only
- **`verify_shipment_fields.py`** - Test field integration
- **`verify_all_tables.py`** - Verify all system tables
- **`check_device_orders_table.py`** - Check DeviceOrders existence

### Documentation
- **`SHIPMENT_FIELDS_GUIDE.md`** - Field integration guide
- **`TASK_1_COMPLETION_SUMMARY.md`** - Task completion details
- **`README_SHIPMENT_TRACKING.md`** - This file

## 🚀 Quick Start

### Create Tables
```bash
# Create Shipments table
python infrastructure/dynamodb/shipments_table.py

# Create DeviceOrders table
python infrastructure/dynamodb/device_orders_table.py
```

### Verify Setup
```bash
# Recommended: Comprehensive verification
python infrastructure/dynamodb/verify_shipment_tracking_tables.py
```

## 📊 Table Specifications

### aquachain-shipments
**Purpose:** Store shipment tracking data with courier integration

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| shipment_id | String | HASH (PK) | Unique shipment identifier |
| order_id | String | GSI | Link to DeviceOrders table |
| tracking_number | String | GSI | Courier tracking number |
| internal_status | String | GSI (HASH) | Current shipment status |
| created_at | String | GSI (RANGE) | Creation timestamp |

**Global Secondary Indexes:**
1. `order_id-index` - Query by order ID
2. `tracking_number-index` - Query by tracking number
3. `status-created_at-index` - Query by status and time

**Features:**
- ✅ DynamoDB Streams enabled (NEW_AND_OLD_IMAGES)
- ✅ PAY_PER_REQUEST billing mode
- ✅ Real-time webhook event storage
- ✅ Complete timeline tracking

### DeviceOrders
**Purpose:** Manage device orders with shipment tracking integration

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| orderId | String | HASH (PK) | Unique order identifier |
| userId | String | GSI (HASH) | Customer user ID |
| status | String | GSI (HASH) | Order status |
| createdAt | String | GSI (RANGE) | Creation timestamp |
| shipment_id | String | Dynamic | Link to Shipments table |
| tracking_number | String | Dynamic | Quick tracking reference |

**Global Secondary Indexes:**
1. `userId-createdAt-index` - Query orders by user
2. `status-createdAt-index` - Query orders by status

**Features:**
- ✅ DynamoDB Streams enabled
- ✅ PAY_PER_REQUEST billing mode
- ✅ Schema-less design for shipment fields
- ✅ Backward compatible with existing orders

## 🔧 Common Operations

### Query Shipment by Order ID
```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aquachain-shipments')

response = table.query(
    IndexName='order_id-index',
    KeyConditionExpression='order_id = :oid',
    ExpressionAttributeValues={':oid': 'ord_123'}
)
```

### Query Shipment by Tracking Number
```python
response = table.query(
    IndexName='tracking_number-index',
    KeyConditionExpression='tracking_number = :tn',
    ExpressionAttributeValues={':tn': 'TRACK123'}
)
```

### Add Shipment Fields to Order (Atomic)
```python
dynamodb.meta.client.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': 'aquachain-shipments',
                'Item': {...}
            }
        },
        {
            'Update': {
                'TableName': 'DeviceOrders',
                'Key': {'orderId': {'S': 'ord_123'}},
                'UpdateExpression': 'SET shipment_id = :sid, tracking_number = :tn',
                'ExpressionAttributeValues': {
                    ':sid': {'S': 'ship_456'},
                    ':tn': {'S': 'TRACK123'}
                }
            }
        }
    ]
)
```

## 🧪 Testing

### Run All Verifications
```bash
# Comprehensive verification (recommended)
python infrastructure/dynamodb/verify_shipment_tracking_tables.py

# Test field integration
python infrastructure/dynamodb/verify_shipment_fields.py

# Verify individual tables
python infrastructure/dynamodb/verify_shipments_table.py
```

### Expected Output
```
✅ Table status: ACTIVE
✅ Primary key: shipment_id (HASH)
✅ GSI: order_id-index
✅ GSI: tracking_number-index
✅ GSI: status-created_at-index
✅ DynamoDB Streams: ENABLED (NEW_AND_OLD_IMAGES)
✅ Billing mode: PAY_PER_REQUEST
```

## 📋 Requirements Mapping

| Requirement | Implementation | Verification |
|------------|----------------|--------------|
| 1.1 | Shipments table with GSIs | ✅ verify_shipments_table.py |
| 1.3 | DeviceOrders shipment fields | ✅ verify_shipment_fields.py |
| 8.1 | Backward compatibility | ✅ Schema-less design |
| 8.4 | DynamoDB Streams | ✅ Enabled on both tables |

## 🔍 Troubleshooting

### Table Not Found
```bash
# Check if table exists
aws dynamodb describe-table --table-name aquachain-shipments

# Create table
python infrastructure/dynamodb/shipments_table.py
```

### GSI Missing
```bash
# Verify table structure
python infrastructure/dynamodb/verify_shipments_table.py
```

### Field Integration Issues
```bash
# Test dynamic field addition
python infrastructure/dynamodb/verify_shipment_fields.py
```

## 📚 Related Documentation

- **Design Document:** `.kiro/specs/shipment-tracking-automation/design.md`
- **Requirements:** `.kiro/specs/shipment-tracking-automation/requirements.md`
- **Tasks:** `.kiro/specs/shipment-tracking-automation/tasks.md`
- **Field Guide:** `SHIPMENT_FIELDS_GUIDE.md`
- **Quick Start:** `QUICK_START.md`

## 🎯 Next Steps

After setting up the database infrastructure:

1. **Deploy Lambda Functions**
   - `lambda/shipments/create_shipment.py`
   - `lambda/shipments/webhook_handler.py`
   - `lambda/shipments/get_shipment_status.py`

2. **Configure API Gateway**
   - POST /api/shipments
   - POST /api/webhooks/:courier
   - GET /api/shipments/:shipmentId

3. **Register Webhooks**
   - Delhivery webhook URL
   - BlueDart webhook URL
   - DTDC webhook URL

## ✅ Verification Checklist

Before proceeding to Lambda implementation:

- [ ] Shipments table created and ACTIVE
- [ ] DeviceOrders table created and ACTIVE
- [ ] All GSIs present and ACTIVE
- [ ] DynamoDB Streams enabled
- [ ] Field integration test passed
- [ ] Backward compatibility verified

Run: `python infrastructure/dynamodb/verify_shipment_tracking_tables.py`

## 🤝 Contributing

When modifying table schemas:
1. Update the table definition file
2. Update verification scripts
3. Update documentation
4. Test backward compatibility
5. Update TASK_1_COMPLETION_SUMMARY.md

---

**Status:** ✅ Task 1 Complete - Infrastructure Ready for Lambda Implementation

*Last Updated: 2024-12-31*
