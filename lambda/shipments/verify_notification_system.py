"""
Verification script for shipment notification system

This script verifies:
1. DynamoDB Streams are enabled on Shipments table
2. Event source mapping exists and is active
3. Lambda function is deployed and configured
4. Required environment variables are set
5. IAM permissions are correct
"""
import boto3
import json
import sys

dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')
iam = boto3.client('iam')

SHIPMENTS_TABLE = 'aquachain-shipments'
LAMBDA_FUNCTION = 'shipment-notification-handler'


def check_dynamodb_stream():
    """Check if DynamoDB Streams are enabled"""
    print("1. Checking DynamoDB Streams...")
    try:
        response = dynamodb.describe_table(TableName=SHIPMENTS_TABLE)
        stream_spec = response['Table'].get('StreamSpecification', {})
        
        if stream_spec.get('StreamEnabled'):
            stream_arn = response['Table'].get('LatestStreamArn')
            view_type = stream_spec.get('StreamViewType')
            print(f"   ✓ DynamoDB Stream enabled")
            print(f"   ✓ Stream ARN: {stream_arn}")
            print(f"   ✓ View type: {view_type}")
            
            if view_type != 'NEW_AND_OLD_IMAGES':
                print(f"   ⚠ Warning: View type should be NEW_AND_OLD_IMAGES, got {view_type}")
                return False, stream_arn
            
            return True, stream_arn
        else:
            print(f"   ✗ DynamoDB Stream not enabled")
            return False, None
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False, None


def check_lambda_function():
    """Check if Lambda function exists and is configured"""
    print("\n2. Checking Lambda function...")
    try:
        response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION)
        config = response['Configuration']
        
        print(f"   ✓ Lambda function exists")
        print(f"   ✓ Runtime: {config['Runtime']}")
        print(f"   ✓ Handler: {config['Handler']}")
        print(f"   ✓ Timeout: {config['Timeout']}s")
        print(f"   ✓ Memory: {config['MemorySize']}MB")
        
        # Check environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        required_vars = [
            'ORDERS_TABLE',
            'SNS_TOPIC_ARN',
            'SES_FROM_EMAIL'
        ]
        
        print("\n   Environment Variables:")
        missing_vars = []
        for var in required_vars:
            if var in env_vars:
                print(f"   ✓ {var}: {env_vars[var]}")
            else:
                print(f"   ✗ {var}: NOT SET")
                missing_vars.append(var)
        
        if missing_vars:
            print(f"\n   ⚠ Warning: Missing environment variables: {', '.join(missing_vars)}")
            return False, config['FunctionArn']
        
        return True, config['FunctionArn']
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"   ✗ Lambda function not found")
        return False, None
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False, None


def check_event_source_mapping(stream_arn, lambda_arn):
    """Check if event source mapping exists"""
    print("\n3. Checking event source mapping...")
    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=lambda_arn
        )
        
        mappings = response.get('EventSourceMappings', [])
        
        if not mappings:
            print(f"   ✗ No event source mappings found")
            return False
        
        # Find mapping for our stream
        stream_mapping = None
        for mapping in mappings:
            if mapping['EventSourceArn'] == stream_arn:
                stream_mapping = mapping
                break
        
        if not stream_mapping:
            print(f"   ✗ No mapping found for Shipments table stream")
            return False
        
        print(f"   ✓ Event source mapping exists")
        print(f"   ✓ UUID: {stream_mapping['UUID']}")
        print(f"   ✓ State: {stream_mapping['State']}")
        print(f"   ✓ Batch size: {stream_mapping['BatchSize']}")
        print(f"   ✓ Starting position: {stream_mapping.get('StartingPosition', 'N/A')}")
        
        if stream_mapping['State'] != 'Enabled':
            print(f"   ⚠ Warning: Mapping state is {stream_mapping['State']}, should be Enabled")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def check_iam_permissions(lambda_arn):
    """Check if Lambda has required IAM permissions"""
    print("\n4. Checking IAM permissions...")
    try:
        # Get Lambda execution role
        response = lambda_client.get_function(FunctionName=lambda_arn)
        role_arn = response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"   ✓ Execution role: {role_name}")
        
        # Get attached policies
        response = iam.list_attached_role_policies(RoleName=role_name)
        policies = response['AttachedPolicies']
        
        print(f"\n   Attached policies:")
        for policy in policies:
            print(f"   - {policy['PolicyName']}")
        
        # Check inline policies
        response = iam.list_role_policies(RoleName=role_name)
        inline_policies = response['PolicyNames']
        
        if inline_policies:
            print(f"\n   Inline policies:")
            for policy_name in inline_policies:
                print(f"   - {policy_name}")
        
        print("\n   Required permissions:")
        required_permissions = [
            "dynamodb:GetRecords",
            "dynamodb:GetShardIterator",
            "dynamodb:DescribeStream",
            "ses:SendEmail",
            "sns:Publish",
            "execute-api:ManageConnections"
        ]
        
        for perm in required_permissions:
            print(f"   - {perm}")
        
        print("\n   ⚠ Note: Verify these permissions manually in IAM console")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_notification_trigger():
    """Provide instructions for testing"""
    print("\n5. Testing instructions...")
    print("\n   To test the notification system:")
    print("\n   Test 1: Create a shipment")
    print("   aws dynamodb put-item \\")
    print("     --table-name aquachain-shipments \\")
    print("     --item '{")
    print('       "shipment_id": {"S": "ship_test_001"},')
    print('       "order_id": {"S": "ord_test_001"},')
    print('       "tracking_number": {"S": "TEST123456"},')
    print('       "internal_status": {"S": "shipment_created"},')
    print('       "courier_name": {"S": "Delhivery"}')
    print("     }'")
    print("\n   Test 2: Update status to out_for_delivery")
    print("   aws dynamodb update-item \\")
    print("     --table-name aquachain-shipments \\")
    print('     --key \'{"shipment_id": {"S": "ship_test_001"}}\' \\')
    print('     --update-expression "SET internal_status = :status" \\')
    print('     --expression-attribute-values \'{":status": {"S": "out_for_delivery"}}\'')
    print("\n   Test 3: Monitor Lambda logs")
    print("   aws logs tail /aws/lambda/shipment-notification-handler --follow")


def main():
    """Main verification function"""
    print("=" * 70)
    print("Shipment Notification System Verification")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    
    # Check 1: DynamoDB Stream
    stream_ok, stream_arn = check_dynamodb_stream()
    if not stream_ok:
        all_checks_passed = False
        print("\n   ⚠ Action required: Enable DynamoDB Streams")
        print("   aws dynamodb update-table \\")
        print("     --table-name aquachain-shipments \\")
        print("     --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES")
    
    # Check 2: Lambda function
    lambda_ok, lambda_arn = check_lambda_function()
    if not lambda_ok:
        all_checks_passed = False
        print("\n   ⚠ Action required: Deploy Lambda function")
        print("   See NOTIFICATION_QUICK_START.md for deployment instructions")
    
    # Check 3: Event source mapping (only if stream and lambda exist)
    if stream_ok and lambda_ok:
        mapping_ok = check_event_source_mapping(stream_arn, lambda_arn)
        if not mapping_ok:
            all_checks_passed = False
            print("\n   ⚠ Action required: Create event source mapping")
            print("   aws lambda create-event-source-mapping \\")
            print(f"     --function-name {LAMBDA_FUNCTION} \\")
            print(f"     --event-source-arn {stream_arn} \\")
            print("     --batch-size 10 \\")
            print("     --starting-position LATEST")
    
    # Check 4: IAM permissions (only if lambda exists)
    if lambda_ok:
        check_iam_permissions(lambda_arn)
    
    # Test instructions
    test_notification_trigger()
    
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✓ All checks passed! Notification system is ready.")
    else:
        print("⚠ Some checks failed. Review the output above and take required actions.")
    print("=" * 70)
    print()
    
    return 0 if all_checks_passed else 1


if __name__ == '__main__':
    sys.exit(main())
