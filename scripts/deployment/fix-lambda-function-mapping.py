#!/usr/bin/env python3
"""
Fix the Lambda function mapping for readings endpoint.
"""

import boto3
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    resource_id = 'o47l9d'  # /api/v1/readings/{deviceId}/latest
    
    print("🔧 Fixing Lambda function mapping...")
    
    # Correct Lambda function
    correct_function = 'aquachain-function-readings-service-dev'
    correct_arn = f'arn:aws:lambda:ap-south-1:339713024676:function:{correct_function}'
    
    try:
        # Update the integration to point to correct Lambda
        print(f"📝 Updating integration to use: {correct_function}")
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{correct_arn}/invocations'
        )
        
        print("✅ Updated Lambda integration")
        
        # Deploy
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix Lambda function mapping for readings'
        )
        print(f"✅ Deployed (ID: {deployment['id']})")
        
        print("\n🎉 Fixed! The endpoint now points to the correct Lambda function.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()