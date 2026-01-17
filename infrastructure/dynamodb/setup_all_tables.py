"""
Master script to set up all DynamoDB tables including shipment tracking
"""
import sys
from tables import DynamoDBTableManager
from shipments_table import ShipmentsTableManager
from device_orders_table import DeviceOrdersTableManager
from contact_table import ContactTableManager

def setup_all_tables(region_name: str = 'us-east-1'):
    """
    Create all DynamoDB tables for AquaChain system
    Includes core tables, shipment tracking, and order management
    """
    print("="*70)
    print("AquaChain DynamoDB Tables Setup")
    print("="*70)
    
    # Initialize managers
    core_manager = DynamoDBTableManager(region_name)
    shipments_manager = ShipmentsTableManager(region_name)
    orders_manager = DeviceOrdersTableManager(region_name)
    contact_manager = ContactTableManager(region_name)
    
    tables_created = []
    tables_failed = []
    
    # Create core tables
    print("\n📦 Creating core system tables...")
    print("-"*70)
    try:
        core_manager.create_all_tables()
        tables_created.append("Core tables (readings, ledger, users, etc.)")
    except Exception as e:
        print(f"❌ Error creating core tables: {e}")
        tables_failed.append(("Core tables", str(e)))
    
    # Create shipment tracking tables
    print("\n🚚 Creating shipment tracking table...")
    print("-"*70)
    try:
        shipments_manager.create_shipments_table()
        tables_created.append("Shipments table")
    except Exception as e:
        print(f"❌ Error creating shipments table: {e}")
        tables_failed.append(("Shipments table", str(e)))
    
    # Create device orders table
    print("\n📋 Creating device orders table...")
    print("-"*70)
    try:
        orders_manager.create_device_orders_table()
        tables_created.append("DeviceOrders table")
    except Exception as e:
        print(f"❌ Error creating device orders table: {e}")
        tables_failed.append(("DeviceOrders table", str(e)))
    
    # Create contact submissions table
    print("\n📧 Creating contact submissions table...")
    print("-"*70)
    try:
        contact_manager.create_contact_submissions_table()
        tables_created.append("Contact submissions table")
    except Exception as e:
        print(f"❌ Error creating contact submissions table: {e}")
        tables_failed.append(("Contact submissions table", str(e)))
    
    # Print summary
    print("\n" + "="*70)
    print("Setup Summary")
    print("="*70)
    
    if tables_created:
        print(f"\n✅ Successfully created/verified {len(tables_created)} table group(s):")
        for table in tables_created:
            print(f"   • {table}")
    
    if tables_failed:
        print(f"\n❌ Failed to create {len(tables_failed)} table group(s):")
        for table_name, error in tables_failed:
            print(f"   • {table_name}: {error}")
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("="*70)
    print("1. Verify tables: python infrastructure/dynamodb/verify_all_tables.py")
    print("2. Test shipment integration: python infrastructure/dynamodb/verify_shipment_fields.py")
    print("3. Deploy Lambda functions for shipment tracking")
    print("4. Configure API Gateway endpoints")
    
    return len(tables_failed) == 0

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up all DynamoDB tables')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    success = setup_all_tables(args.region)
    sys.exit(0 if success else 1)
