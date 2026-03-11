#!/usr/bin/env python3
"""
Update Lambda functions to use the working SageMaker endpoint
"""

import boto3
import json

def update_lambda_environment(function_name, new_endpoint_name, region='ap-south-1'):
    """Update Lambda function environment variable"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Get current function configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        # Update environment variables
        env_vars = response.get('Environment', {}).get('Variables', {})
        env_vars['SAGEMAKER_ENDPOINT_NAME'] = new_endpoint_name
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print(f"✅ Updated {function_name} to use endpoint: {new_endpoint_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {function_name}: {str(e)}")
        return False

def main():
    """Update all relevant Lambda functions"""
    print("=== Updating Lambda Functions for Working SageMaker Endpoint ===")
    
    new_endpoint_name = "aquachain-wqi-working-dev"
    
    # List of Lambda functions that use SageMaker
    lambda_functions = [
        "AquaChain-Function-MLInference-dev",
        "AquaChain-Function-DataProcessing-dev",  # If it uses ML inference
    ]
    
    success_count = 0
    for function_name in lambda_functions:
        if update_lambda_environment(function_name, new_endpoint_name):
            success_count += 1
    
    print(f"\n=== Results ===")
    print(f"✅ {success_count}/{len(lambda_functions)} Lambda functions updated")
    
    if success_count == len(lambda_functions):
        print("🎉 All Lambda functions updated successfully!")
    else:
        print("⚠️  Some Lambda functions failed to update.")

if __name__ == "__main__":
    main()