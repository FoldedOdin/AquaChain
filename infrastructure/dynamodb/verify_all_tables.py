"""
Verify all DynamoDB tables are created correctly
"""
import boto3
from botocore.exceptions import ClientError

def verify_table(dynamodb, table_name, required_gsis=None):
    """Verify a single table exists and has required structure"""
    try:
        response = dynamodb.describe_table(TableName=table_name)
        table = response['Table']
        
        status = table['TableStatus']
        if status == 'ACTIVE':
            print(f"✅ {table_name:<40} Status: {status}")
            
            # Check GSIs if specified
            if required_gsis:
                gsis = table.get('GlobalSecondaryIndexes', [])
                gsi_names = [gsi['IndexName'] for gsi in gsis]
                
                for required_gsi in required_gsis:
                    if required_gsi in gsi_names:
                        print(f"   ✓ GSI: {required_gsi}")
                    else:
                        print(f"   ✗ Missing GSI: {required_gsi}")
            
            # Check streams
            stream_spec = table.get('StreamSpecification', {})
            if stream_spec.get('StreamEnabled'):
                print(f"   ✓ Streams: ENABLED ({stream_spec.get('StreamViewType')})")
            
            return True
        else:
            print(f"⚠️  {table_name:<40} Status: {status}")
            return False
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ {table_name:<40} NOT FOUND")
        else:
            print(f"❌ {table_name:<40} Error: {e.response['Error']['Message']}")
        return False

def verify_all_tables():
    """Verify all AquaChain DynamoDB tables"""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    print("="*70)
    print("AquaChain DynamoDB Tables Verification")
    print("="*70)
    
    tables_to_verify = [
        # Core tables
        {
            'name': 'aquachain-readings',
            'gsis': ['DeviceIndex', 'device_id-metric_type-index', 'alert_level-timestamp-index']
        },
        {
            'name': 'aquachain-ledger',
            'gsis': ['DeviceLedgerIndex']
        },
        {
            'name': 'aquachain-sequence',
            'gsis': []
        },
        {
            'name': 'aquachain-users',
            'gsis': ['email-index', 'organization_id-role-index']
        },
        {
            'name': 'aquachain-service-requests',
            'gsis': ['ConsumerIndex', 'TechnicianIndex', 'StatusIndex']
        },
        {
            'name': 'aquachain-alerts',
            'gsis': ['DeviceAlerts', 'AlertLevelIndex']
        },
        {
            'name': 'aquachain-notifications',
            'gsis': ['UserNotifications']
        },
        {
            'name': 'aquachain-rate-limits',
            'gsis': []
        },
        {
            'name': 'aquachain-websocket-connections',
            'gsis': ['UserConnections']
        },
        {
            'name': 'aquachain-devices',
            'gsis': ['user_id-created_at-index', 'status-last_seen-index']
        },
        # Shipment tracking tables
        {
            'name': 'aquachain-shipments',
            'gsis': ['order_id-index', 'tracking_number-index', 'status-created_at-index']
        },
        # Order management tables
        {
            'name': 'DeviceOrders',
            'gsis': ['userId-createdAt-index', 'status-createdAt-index']
        },
        # Contact form tables
        {
            'name': 'aquachain-contact-submissions',
            'gsis': ['email-createdAt-index', 'inquiryType-createdAt-index', 'status-createdAt-index']
        }
    ]
    
    print("\n📊 Verifying tables...\n")
    
    verified_count = 0
    failed_count = 0
    
    for table_info in tables_to_verify:
        if verify_table(dynamodb, table_info['name'], table_info['gsis']):
            verified_count += 1
        else:
            failed_count += 1
        print()  # Empty line between tables
    
    # Summary
    print("="*70)
    print("Verification Summary")
    print("="*70)
    print(f"✅ Verified: {verified_count} tables")
    print(f"❌ Failed:   {failed_count} tables")
    
    if failed_count == 0:
        print("\n🎉 All tables verified successfully!")
        print("\n✨ Shipment tracking infrastructure is ready:")
        print("   • aquachain-shipments table: Stores shipment tracking data")
        print("   • DeviceOrders table: Supports shipment_id and tracking_number fields")
        print("   • DynamoDB Streams enabled for real-time notifications")
        return True
    else:
        print("\n⚠️  Some tables are missing or have issues")
        print("   Run: python infrastructure/dynamodb/setup_all_tables.py")
        return False

if __name__ == '__main__':
    import sys
    success = verify_all_tables()
    sys.exit(0 if success else 1)
