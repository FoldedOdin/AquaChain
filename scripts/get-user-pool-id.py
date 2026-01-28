#!/usr/bin/env python3
"""
Get Cognito User Pool ID from deployed infrastructure
"""

import boto3
import json
from botocore.exceptions import ClientError

def get_user_pool_id_from_cloudformation():
    """Get User Pool ID from CloudFormation stack outputs"""
    try:
        cf_client = boto3.client('cloudformation')
        
        # Try different possible stack names
        stack_names = [
            'AquaChain-API-dev',
            'aquachain-api-dev', 
            'AquaChain-Auth-dev',
            'aquachain-auth-dev'
        ]
        
        for stack_name in stack_names:
            try:
                print(f"Checking stack: {stack_name}")
                response = cf_client.describe_stacks(StackName=stack_name)
                
                for output in response['Stacks'][0]['Outputs']:
                    if output['OutputKey'] in ['UserPoolId', 'CognitoUserPoolId', 'UserPool']:
                        user_pool_id = output['OutputValue']
                        print(f"✓ Found User Pool ID in {stack_name}: {user_pool_id}")
                        return user_pool_id
                        
            except ClientError as e:
                if e.response['Error']['Code'] != 'ValidationError':
                    print(f"  Error checking {stack_name}: {e}")
                continue
        
        print("Could not find User Pool ID in CloudFormation outputs")
        return None
        
    except Exception as e:
        print(f"Error accessing CloudFormation: {e}")
        return None

def get_user_pool_id_from_cognito():
    """Get User Pool ID by listing Cognito User Pools"""
    try:
        cognito_client = boto3.client('cognito-idp')
        
        print("Searching for AquaChain User Pools...")
        response = cognito_client.list_user_pools(MaxResults=50)
        
        aquachain_pools = []
        for pool in response['UserPools']:
            if 'aquachain' in pool['Name'].lower() or 'AquaChain' in pool['Name']:
                aquachain_pools.append(pool)
                print(f"✓ Found AquaChain User Pool: {pool['Name']} - {pool['Id']}")
        
        if len(aquachain_pools) == 1:
            return aquachain_pools[0]['Id']
        elif len(aquachain_pools) > 1:
            print("\nMultiple AquaChain User Pools found:")
            for i, pool in enumerate(aquachain_pools):
                print(f"{i+1}. {pool['Name']} - {pool['Id']}")
            
            while True:
                try:
                    choice = int(input("Select User Pool (enter number): ")) - 1
                    if 0 <= choice < len(aquachain_pools):
                        return aquachain_pools[choice]['Id']
                    else:
                        print("Invalid choice, please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            print("No AquaChain User Pools found")
            return None
            
    except Exception as e:
        print(f"Error accessing Cognito: {e}")
        return None

def main():
    print("🔍 Finding AquaChain Cognito User Pool ID")
    print("=" * 50)
    
    # Method 1: Try CloudFormation first
    user_pool_id = get_user_pool_id_from_cloudformation()
    
    # Method 2: If not found, try listing Cognito pools
    if not user_pool_id:
        print("\nTrying to find User Pool by listing Cognito pools...")
        user_pool_id = get_user_pool_id_from_cognito()
    
    if user_pool_id:
        print(f"\n✅ User Pool ID: {user_pool_id}")
        
        # Save to file for future use
        with open('user_pool_id.txt', 'w') as f:
            f.write(user_pool_id)
        print(f"📄 Saved to: user_pool_id.txt")
        
        return user_pool_id
    else:
        print("\n❌ Could not find User Pool ID")
        print("\nManual steps to find it:")
        print("1. Go to AWS Console > Cognito")
        print("2. Click on 'User pools'")
        print("3. Find your AquaChain user pool")
        print("4. Copy the User pool ID")
        return None

if __name__ == "__main__":
    main()