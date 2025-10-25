#!/usr/bin/env python3
"""
API Key Management Script
Create, retrieve, and manage API Gateway keys
"""

import boto3
import json
import argparse
from datetime import datetime
from typing import Dict, List
import sys


class APIKeyManager:
    """
    Manage API Gateway keys and usage plans
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.region = region
    
    def list_api_keys(self, name_prefix: str = 'aquachain') -> List[Dict]:
        """
        List all API keys matching prefix
        """
        try:
            response = self.apigateway.get_api_keys(
                nameQuery=name_prefix,
                includeValues=False
            )
            
            keys = response.get('items', [])
            
            print(f"\n📋 Found {len(keys)} API keys:")
            print("-" * 80)
            
            for key in keys:
                print(f"Name: {key['name']}")
                print(f"ID: {key['id']}")
                print(f"Enabled: {key['enabled']}")
                print(f"Created: {key.get('createdDate', 'Unknown')}")
                print("-" * 80)
            
            return keys
            
        except Exception as e:
            print(f"❌ Error listing API keys: {e}")
            return []
    
    def get_api_key_value(self, key_id: str) -> str:
        """
        Retrieve the actual API key value (sensitive!)
        """
        try:
            response = self.apigateway.get_api_key(
                apiKey=key_id,
                includeValue=True
            )
            
            return response['value']
            
        except Exception as e:
            print(f"❌ Error retrieving API key value: {e}")
            return None
    
    def create_api_key(self, name: str, description: str = "") -> Dict:
        """
        Create a new API key
        """
        try:
            response = self.apigateway.create_api_key(
                name=name,
                description=description,
                enabled=True
            )
            
            print(f"✅ Created API key: {name}")
            print(f"   ID: {response['id']}")
            print(f"   Value: {response['value']}")
            print(f"   ⚠️  Save this value securely - it won't be shown again!")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating API key: {e}")
            return None
    
    def delete_api_key(self, key_id: str) -> bool:
        """
        Delete an API key
        """
        try:
            self.apigateway.delete_api_key(apiKey=key_id)
            print(f"✅ Deleted API key: {key_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting API key: {e}")
            return False
    
    def list_usage_plans(self) -> List[Dict]:
        """
        List all usage plans
        """
        try:
            response = self.apigateway.get_usage_plans()
            
            plans = response.get('items', [])
            
            print(f"\n📊 Found {len(plans)} usage plans:")
            print("-" * 80)
            
            for plan in plans:
                print(f"Name: {plan['name']}")
                print(f"ID: {plan['id']}")
                
                if 'throttle' in plan:
                    print(f"Rate Limit: {plan['throttle'].get('rateLimit', 'N/A')} req/s")
                    print(f"Burst Limit: {plan['throttle'].get('burstLimit', 'N/A')}")
                
                if 'quota' in plan:
                    print(f"Quota: {plan['quota'].get('limit', 'N/A')} requests per {plan['quota'].get('period', 'N/A')}")
                
                print("-" * 80)
            
            return plans
            
        except Exception as e:
            print(f"❌ Error listing usage plans: {e}")
            return []
    
    def associate_key_with_plan(self, key_id: str, usage_plan_id: str) -> bool:
        """
        Associate an API key with a usage plan
        """
        try:
            self.apigateway.create_usage_plan_key(
                usagePlanId=usage_plan_id,
                keyId=key_id,
                keyType='API_KEY'
            )
            
            print(f"✅ Associated key {key_id} with usage plan {usage_plan_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error associating key with plan: {e}")
            return False
    
    def get_usage_statistics(self, usage_plan_id: str, key_id: str = None, 
                            days: int = 7) -> Dict:
        """
        Get usage statistics for a usage plan
        """
        try:
            from datetime import timedelta
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            params = {
                'usagePlanId': usage_plan_id,
                'startDate': start_date,
                'endDate': end_date
            }
            
            if key_id:
                params['keyId'] = key_id
            
            response = self.apigateway.get_usage(**params)
            
            print(f"\n📈 Usage Statistics ({start_date} to {end_date}):")
            print("-" * 80)
            
            items = response.get('items', {})
            for key, usage_data in items.items():
                print(f"API Key: {key}")
                for date, requests in usage_data.items():
                    print(f"  {date}: {requests[0][0]} requests")
            
            return response
            
        except Exception as e:
            print(f"❌ Error getting usage statistics: {e}")
            return {}
    
    def export_keys_to_file(self, filename: str = 'api-keys.json'):
        """
        Export API keys to a file (without values for security)
        """
        try:
            keys = self.list_api_keys()
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'region': self.region,
                'keys': [
                    {
                        'name': key['name'],
                        'id': key['id'],
                        'enabled': key['enabled'],
                        'created': str(key.get('createdDate', ''))
                    }
                    for key in keys
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"✅ Exported {len(keys)} API keys to {filename}")
            
        except Exception as e:
            print(f"❌ Error exporting keys: {e}")


def main():
    parser = argparse.ArgumentParser(description='Manage API Gateway keys')
    parser.add_argument('action', choices=[
        'list', 'create', 'delete', 'get-value', 'list-plans', 
        'associate', 'usage', 'export'
    ])
    parser.add_argument('--name', help='API key name')
    parser.add_argument('--key-id', help='API key ID')
    parser.add_argument('--plan-id', help='Usage plan ID')
    parser.add_argument('--description', help='API key description')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--days', type=int, default=7, help='Days for usage stats')
    parser.add_argument('--output', default='api-keys.json', help='Output file for export')
    
    args = parser.parse_args()
    
    manager = APIKeyManager(region=args.region)
    
    if args.action == 'list':
        manager.list_api_keys()
    
    elif args.action == 'create':
        if not args.name:
            print("❌ --name is required for create action")
            sys.exit(1)
        manager.create_api_key(args.name, args.description or "")
    
    elif args.action == 'delete':
        if not args.key_id:
            print("❌ --key-id is required for delete action")
            sys.exit(1)
        
        confirm = input(f"⚠️  Are you sure you want to delete key {args.key_id}? (yes/no): ")
        if confirm.lower() == 'yes':
            manager.delete_api_key(args.key_id)
        else:
            print("❌ Deletion cancelled")
    
    elif args.action == 'get-value':
        if not args.key_id:
            print("❌ --key-id is required for get-value action")
            sys.exit(1)
        
        value = manager.get_api_key_value(args.key_id)
        if value:
            print(f"\n🔑 API Key Value: {value}")
            print("⚠️  Keep this value secure!")
    
    elif args.action == 'list-plans':
        manager.list_usage_plans()
    
    elif args.action == 'associate':
        if not args.key_id or not args.plan_id:
            print("❌ --key-id and --plan-id are required for associate action")
            sys.exit(1)
        manager.associate_key_with_plan(args.key_id, args.plan_id)
    
    elif args.action == 'usage':
        if not args.plan_id:
            print("❌ --plan-id is required for usage action")
            sys.exit(1)
        manager.get_usage_statistics(args.plan_id, args.key_id, args.days)
    
    elif args.action == 'export':
        manager.export_keys_to_file(args.output)


if __name__ == "__main__":
    main()
