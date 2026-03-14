#!/usr/bin/env python3
"""
Check Lambda function configuration to see which handler is being used
"""

import boto3
import json

def check_lambda_config():
    """Check the Lambda function configuration"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Get function configuration
        response = lambda_client.get_function(FunctionName=func_name)
        
        config = response['Configuration']
        code = response.get('Code', {})
        
        print(f"📋 Lambda Function Configuration:")
        print(f"   Function Name: {config['FunctionName']}")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Handler: {config['Handler']}")
        print(f"   Memory: {config['MemorySize']} MB")
        print(f"   Timeout: {config['Timeout']} seconds")
        print(f"   Last Modified: {config['LastModified']}")
        
        # Environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        print(f"\n📋 Environment Variables:")
        for key, value in env_vars.items():
            print(f"   {key}: {value}")
        
        # Code location
        print(f"\n📋 Code Configuration:")
        print(f"   Code Size: {config['CodeSize']} bytes")
        print(f"   Code SHA256: {config['CodeSha256']}")
        
        if 'Location' in code:
            print(f"   Code Location: {code['Location']}")
        
        return config['Handler']
        
    except Exception as e:
        print(f"❌ Error checking Lambda config: {e}")
        return None

def main():
    print("🔍 Checking Lambda Configuration")
    print("=" * 35)
    
    handler = check_lambda_config()
    
    if handler:
        print(f"\n🎯 Current Handler: {handler}")
        
        # Parse handler
        if '.' in handler:
            module, function = handler.rsplit('.', 1)
            print(f"   Module: {module}")
            print(f"   Function: {function}")
            
            # Determine which file is being used
            if 'user_aware' in module:
                print(f"\n✅ Using user_aware_ingestion_handler.py")
                print(f"   This handler should NOT require location field")
            elif 'handler' in module:
                print(f"\n⚠️ Using handler.py")
                print(f"   This handler REQUIRES location field - this is the problem!")
            else:
                print(f"\n❓ Unknown handler module: {module}")

if __name__ == "__main__":
    main()