"""
EventBridge Rule Setup for Stale Shipment Detection

Creates CloudWatch Event Rule to trigger stale_shipment_detector Lambda daily at 9 AM.
The rule checks for shipments with no updates for 7+ days.

Requirements: 5.3
"""

import boto3
import json
from typing import Dict, Any
from botocore.exceptions import ClientError


class StaleShipmentEventBridge:
    def __init__(self, region='us-east-1'):
        self.events = boto3.client('events', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region
        
        # Configuration
        self.rule_name = 'aquachain-stale-shipment-detector'
        self.lambda_function_name = 'aquachain-stale-shipment-detector'
        self.schedule_expression = 'cron(0 9 * * ? *)'  # Daily at 9 AM UTC
        
    def create_eventbridge_rule(self, enabled: bool = True) -> Dict[str, Any]:
        """
        Create EventBridge rule to trigger stale_shipment_detector Lambda daily at 9 AM.
        
        Args:
            enabled: Whether to enable the rule immediately (default: True)
            
        Returns:
            Dictionary with rule ARN and configuration
        """
        try:
            # Create or update the rule
            response = self.events.put_rule(
                Name=self.rule_name,
                ScheduleExpression=self.schedule_expression,
                State='ENABLED' if enabled else 'DISABLED',
                Description='Trigger stale shipment detection daily at 9 AM to check for shipments with no updates for 7+ days',
                Tags=[
                    {'Key': 'Service', 'Value': 'AquaChain'},
                    {'Key': 'Component', 'Value': 'ShipmentTracking'},
                    {'Key': 'Purpose', 'Value': 'StaleShipmentDetection'}
                ]
            )
            
            rule_arn = response['RuleArn']
            print(f"Created EventBridge rule: {self.rule_name}")
            print(f"Rule ARN: {rule_arn}")
            print(f"Schedule: {self.schedule_expression} (Daily at 9 AM UTC)")
            print(f"State: {'ENABLED' if enabled else 'DISABLED'}")
            
            return {
                'rule_name': self.rule_name,
                'rule_arn': rule_arn,
                'schedule': self.schedule_expression,
                'enabled': enabled
            }
            
        except ClientError as e:
            print(f"Error creating EventBridge rule: {e}")
            raise
    
    def add_lambda_target(self, lambda_function_arn: str = None) -> Dict[str, Any]:
        """
        Add Lambda function as target for the EventBridge rule.
        
        Args:
            lambda_function_arn: ARN of the Lambda function (optional, will be constructed if not provided)
            
        Returns:
            Dictionary with target configuration
        """
        try:
            # Construct Lambda ARN if not provided
            if not lambda_function_arn:
                account_id = boto3.client('sts').get_caller_identity()['Account']
                lambda_function_arn = f"arn:aws:lambda:{self.region}:{account_id}:function:{self.lambda_function_name}"
            
            # Add Lambda as target
            response = self.events.put_targets(
                Rule=self.rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': lambda_function_arn,
                        'Input': json.dumps({
                            'source': 'eventbridge',
                            'trigger': 'scheduled',
                            'schedule': self.schedule_expression,
                            'detection_type': 'stale_shipment'
                        })
                    }
                ]
            )
            
            print(f"Added Lambda target to rule: {self.lambda_function_name}")
            print(f"Lambda ARN: {lambda_function_arn}")
            
            # Check for failures
            if response.get('FailedEntryCount', 0) > 0:
                print(f"Warning: {response['FailedEntryCount']} targets failed to add")
                print(f"Failed entries: {response.get('FailedEntries', [])}")
            
            return {
                'rule_name': self.rule_name,
                'lambda_arn': lambda_function_arn,
                'target_id': '1',
                'failed_count': response.get('FailedEntryCount', 0)
            }
            
        except ClientError as e:
            print(f"Error adding Lambda target: {e}")
            raise
    
    def add_lambda_permission(self, lambda_function_name: str = None) -> Dict[str, Any]:
        """
        Add permission for EventBridge to invoke the Lambda function.
        
        Args:
            lambda_function_name: Name of the Lambda function (optional)
            
        Returns:
            Dictionary with permission configuration
        """
        if not lambda_function_name:
            lambda_function_name = self.lambda_function_name
        
        try:
            # Get account ID for source ARN
            account_id = boto3.client('sts').get_caller_identity()['Account']
            source_arn = f"arn:aws:events:{self.region}:{account_id}:rule/{self.rule_name}"
            
            # Add permission
            response = self.lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=f'{self.rule_name}-invoke-permission',
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=source_arn
            )
            
            print(f"Added EventBridge invoke permission to Lambda: {lambda_function_name}")
            print(f"Source ARN: {source_arn}")
            
            return {
                'function_name': lambda_function_name,
                'statement_id': f'{self.rule_name}-invoke-permission',
                'source_arn': source_arn
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"Permission already exists for Lambda: {lambda_function_name}")
                return {
                    'function_name': lambda_function_name,
                    'statement_id': f'{self.rule_name}-invoke-permission',
                    'status': 'already_exists'
                }
            else:
                print(f"Error adding Lambda permission: {e}")
                raise
    
    def enable_rule(self) -> Dict[str, Any]:
        """
        Enable the EventBridge rule.
        
        Returns:
            Dictionary with rule status
        """
        try:
            self.events.enable_rule(Name=self.rule_name)
            print(f"Enabled EventBridge rule: {self.rule_name}")
            
            return {
                'rule_name': self.rule_name,
                'status': 'enabled'
            }
            
        except ClientError as e:
            print(f"Error enabling rule: {e}")
            raise
    
    def disable_rule(self) -> Dict[str, Any]:
        """
        Disable the EventBridge rule.
        
        Returns:
            Dictionary with rule status
        """
        try:
            self.events.disable_rule(Name=self.rule_name)
            print(f"Disabled EventBridge rule: {self.rule_name}")
            
            return {
                'rule_name': self.rule_name,
                'status': 'disabled'
            }
            
        except ClientError as e:
            print(f"Error disabling rule: {e}")
            raise
    
    def get_rule_status(self) -> Dict[str, Any]:
        """
        Get current status of the EventBridge rule.
        
        Returns:
            Dictionary with rule details and status
        """
        try:
            response = self.events.describe_rule(Name=self.rule_name)
            
            return {
                'rule_name': response['Name'],
                'arn': response['Arn'],
                'state': response['State'],
                'schedule': response.get('ScheduleExpression', 'N/A'),
                'description': response.get('Description', ''),
                'created_by': response.get('CreatedBy', 'N/A')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return {
                    'rule_name': self.rule_name,
                    'status': 'not_found'
                }
            else:
                print(f"Error getting rule status: {e}")
                raise
    
    def delete_rule(self) -> Dict[str, Any]:
        """
        Delete the EventBridge rule and remove all targets.
        
        Returns:
            Dictionary with deletion status
        """
        try:
            # Remove all targets first
            targets_response = self.events.list_targets_by_rule(Rule=self.rule_name)
            target_ids = [target['Id'] for target in targets_response.get('Targets', [])]
            
            if target_ids:
                self.events.remove_targets(
                    Rule=self.rule_name,
                    Ids=target_ids
                )
                print(f"Removed {len(target_ids)} targets from rule")
            
            # Delete the rule
            self.events.delete_rule(Name=self.rule_name)
            print(f"Deleted EventBridge rule: {self.rule_name}")
            
            return {
                'rule_name': self.rule_name,
                'status': 'deleted',
                'targets_removed': len(target_ids)
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Rule not found: {self.rule_name}")
                return {
                    'rule_name': self.rule_name,
                    'status': 'not_found'
                }
            else:
                print(f"Error deleting rule: {e}")
                raise
    
    def setup_complete_stale_detection_infrastructure(
        self,
        lambda_function_arn: str = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Set up complete stale shipment detection infrastructure.
        
        Creates EventBridge rule, adds Lambda target, and configures permissions.
        
        Args:
            lambda_function_arn: ARN of the Lambda function (optional)
            enabled: Whether to enable the rule immediately (default: True)
            
        Returns:
            Dictionary with complete setup details
        """
        print("Setting up stale shipment detection infrastructure...")
        
        # Create EventBridge rule
        rule_config = self.create_eventbridge_rule(enabled=enabled)
        
        # Add Lambda target
        target_config = self.add_lambda_target(lambda_function_arn)
        
        # Add Lambda permission
        permission_config = self.add_lambda_permission()
        
        print("\n=== Stale Shipment Detection Setup Complete ===")
        print(f"Rule: {rule_config['rule_name']}")
        print(f"Schedule: {rule_config['schedule']} (Daily at 9 AM UTC)")
        print(f"State: {'ENABLED' if enabled else 'DISABLED'}")
        print(f"Lambda: {self.lambda_function_name}")
        print("=" * 50)
        
        return {
            'rule': rule_config,
            'target': target_config,
            'permission': permission_config,
            'setup_complete': True
        }


def main():
    """
    Main function to set up stale shipment detection infrastructure.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup EventBridge rule for stale shipment detection')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--lambda-arn', help='Lambda function ARN (optional)')
    parser.add_argument('--enabled', action='store_true', default=True, help='Enable rule immediately')
    parser.add_argument('--disabled', action='store_true', help='Create rule but keep it disabled')
    parser.add_argument('--status', action='store_true', help='Get current rule status')
    parser.add_argument('--enable', action='store_true', help='Enable existing rule')
    parser.add_argument('--disable', action='store_true', help='Disable existing rule')
    parser.add_argument('--delete', action='store_true', help='Delete the rule')
    
    args = parser.parse_args()
    
    # Initialize EventBridge setup
    eventbridge = StaleShipmentEventBridge(region=args.region)
    
    # Handle different actions
    if args.status:
        status = eventbridge.get_rule_status()
        print(json.dumps(status, indent=2))
        
    elif args.enable:
        result = eventbridge.enable_rule()
        print(json.dumps(result, indent=2))
        
    elif args.disable:
        result = eventbridge.disable_rule()
        print(json.dumps(result, indent=2))
        
    elif args.delete:
        result = eventbridge.delete_rule()
        print(json.dumps(result, indent=2))
        
    else:
        # Default: Set up complete infrastructure
        enabled = not args.disabled
        result = eventbridge.setup_complete_stale_detection_infrastructure(
            lambda_function_arn=args.lambda_arn,
            enabled=enabled
        )
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
