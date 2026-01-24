#!/usr/bin/env python3
"""
AquaChain Inventory Management - DynamoDB Tables Setup
Creates all tables required for the complete inventory management system
"""

import boto3
from botocore.exceptions import ClientError
import json
import time
from typing import Dict, List

class InventoryTablesSetup:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.region = region
        
    def create_inventory_items_table(self) -> Dict:
        """Create the main inventory items table"""
        table_name = 'AquaChain-Inventory-Items'
        
        try:
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'item_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'location_id', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'item_id', 'AttributeType': 'S'},
                    {'AttributeName': 'location_id', 'AttributeType': 'S'},
                    {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                    {'AttributeName': 'category', 'AttributeType': 'S'},
                    {'AttributeName': 'reorder_status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'SupplierIndex',
                        'KeySchema': [
                            {'AttributeName': 'supplier_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'CategoryIndex',
                        'KeySchema': [
                            {'AttributeName': 'category', 'KeyType': 'HASH'},
                            {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'ReorderStatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'reorder_status', 'KeyType': 'HASH'},
                            {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Inventory'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print(f"✅ Created table: {table_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
                return {'TableDescription': {'TableName': table_name}}
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

    def create_suppliers_table(self) -> Dict:
        """Create suppliers management table"""
        table_name = 'AquaChain-Suppliers'
        
        try:
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'supplier_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                    {'AttributeName': 'supplier_type', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'},
                    {'AttributeName': 'performance_score', 'AttributeType': 'N'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'TypeIndex',
                        'KeySchema': [
                            {'AttributeName': 'supplier_type', 'KeyType': 'HASH'},
                            {'AttributeName': 'performance_score', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'supplier_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Suppliers'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print(f"✅ Created table: {table_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
                return {'TableDescription': {'TableName': table_name}}
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

    def create_purchase_orders_table(self) -> Dict:
        """Create purchase orders table"""
        table_name = 'AquaChain-Purchase-Orders'
        
        try:
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'po_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'po_id', 'AttributeType': 'S'},
                    {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'},
                    {'AttributeName': 'created_date', 'AttributeType': 'S'},
                    {'AttributeName': 'expected_delivery', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'SupplierOrdersIndex',
                        'KeySchema': [
                            {'AttributeName': 'supplier_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_date', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'expected_delivery', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'PurchaseOrders'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print(f"✅ Created table: {table_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
                return {'TableDescription': {'TableName': table_name}}
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

    def create_warehouse_locations_table(self) -> Dict:
        """Create warehouse locations table"""
        table_name = 'AquaChain-Warehouse-Locations'
        
        try:
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'location_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'location_id', 'AttributeType': 'S'},
                    {'AttributeName': 'warehouse_id', 'AttributeType': 'S'},
                    {'AttributeName': 'zone', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'WarehouseIndex',
                        'KeySchema': [
                            {'AttributeName': 'warehouse_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'zone', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'location_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Warehouse'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print(f"✅ Created table: {table_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
                return {'TableDescription': {'TableName': table_name}}
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

    def create_demand_forecasts_table(self) -> Dict:
        """Create demand forecasts table for ML predictions"""
        table_name = 'AquaChain-Demand-Forecasts'
        
        try:
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'item_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'forecast_date', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'item_id', 'AttributeType': 'S'},
                    {'AttributeName': 'forecast_date', 'AttributeType': 'S'},
                    {'AttributeName': 'model_version', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'ModelVersionIndex',
                        'KeySchema': [
                            {'AttributeName': 'model_version', 'KeyType': 'HASH'},
                            {'AttributeName': 'forecast_date', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                },
                Tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'Forecasting'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print(f"✅ Created table: {table_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
                return {'TableDescription': {'TableName': table_name}}
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

    def wait_for_tables_active(self, table_names: List[str]):
        """Wait for all tables to become active"""
        print("⏳ Waiting for tables to become active...")
        
        for table_name in table_names:
            waiter = self.dynamodb.get_waiter('table_exists')
            try:
                waiter.wait(
                    TableName=table_name,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 20}
                )
                print(f"✅ Table {table_name} is active")
            except Exception as e:
                print(f"❌ Error waiting for {table_name}: {e}")

    def setup_all_inventory_tables(self):
        """Create all inventory management tables"""
        print("🚀 Setting up AquaChain Inventory Management Tables...")
        
        tables_created = []
        
        # Create all tables
        self.create_inventory_items_table()
        tables_created.append('AquaChain-Inventory-Items')
        
        self.create_suppliers_table()
        tables_created.append('AquaChain-Suppliers')
        
        self.create_purchase_orders_table()
        tables_created.append('AquaChain-Purchase-Orders')
        
        self.create_warehouse_locations_table()
        tables_created.append('AquaChain-Warehouse-Locations')
        
        self.create_demand_forecasts_table()
        tables_created.append('AquaChain-Demand-Forecasts')
        
        # Wait for all tables to be active
        self.wait_for_tables_active(tables_created)
        
        print("✅ All inventory management tables created successfully!")
        return tables_created

def main():
    """Main execution function"""
    try:
        setup = InventoryTablesSetup()
        tables = setup.setup_all_inventory_tables()
        
        print("\n📊 Inventory Management Tables Summary:")
        for table in tables:
            print(f"  • {table}")
            
        print("\n🎉 Inventory management infrastructure is ready!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()