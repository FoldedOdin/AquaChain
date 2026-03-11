#!/usr/bin/env python3
"""
Deploy a working SageMaker endpoint with the trained XGBoost model
This script creates a new endpoint with native XGBoost format (no custom inference)
"""

import boto3
import json
import time
from datetime import datetime

# Configuration
REGION = "ap-south-1"
MODEL_BUCKET = "aquachain-ml-models-dev-758346259059"
MODEL_PATH = "models/wqi-model/latest/model.tar.gz"
SAGEMAKER_ROLE = "arn:aws:iam::758346259059:role/AquaChain-SageMaker-ExecutionRole-dev"

# Resource names (use working- prefix to avoid conflicts)
MODEL_NAME = "aquachain-wqi-working-dev"
ENDPOINT_CONFIG_NAME = "aquachain-wqi-working-config-dev"
ENDPOINT_NAME = "aquachain-wqi-working-dev"

def create_sagemaker_model():
    """Create SageMaker model with native XGBoost container"""
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    
    # XGBoost container image URI for ap-south-1
    container_image = "720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-xgboost:1.7-1"
    
    model_data_url = f"s3://{MODEL_BUCKET}/{MODEL_PATH}"
    
    print(f"Creating SageMaker model: {MODEL_NAME}")
    print(f"Model data: {model_data_url}")
    print(f"Container: {container_image}")
    
    try:
        response = sagemaker.create_model(
            ModelName=MODEL_NAME,
            PrimaryContainer={
                'Image': container_image,
                'ModelDataUrl': model_data_url,
                'Environment': {
                    'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                    'SAGEMAKER_REGION': REGION,
                }
            },
            ExecutionRoleArn=SAGEMAKER_ROLE,
            Tags=[
                {'Key': 'Project', 'Value': 'AquaChain'},
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'ModelType', 'Value': 'WaterQualityIndex'},
                {'Key': 'Version', 'Value': 'working'},
            ]
        )
        print(f"✅ Model created successfully: {response['ModelArn']}")
        return True
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Model {MODEL_NAME} already exists, continuing...")
            return True
        else:
            print(f"❌ Error creating model: {str(e)}")
            return False

def create_endpoint_config():
    """Create endpoint configuration"""
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    
    print(f"Creating endpoint configuration: {ENDPOINT_CONFIG_NAME}")
    
    try:
        response = sagemaker.create_endpoint_config(
            EndpointConfigName=ENDPOINT_CONFIG_NAME,
            ProductionVariants=[
                {
                    'VariantName': 'primary',
                    'ModelName': MODEL_NAME,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.t2.medium',
                    'InitialVariantWeight': 1.0,
                }
            ],
            Tags=[
                {'Key': 'Project', 'Value': 'AquaChain'},
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'Version', 'Value': 'working'},
            ]
        )
        print(f"✅ Endpoint config created: {response['EndpointConfigArn']}")
        return True
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Endpoint config {ENDPOINT_CONFIG_NAME} already exists, continuing...")
            return True
        else:
            print(f"❌ Error creating endpoint config: {str(e)}")
            return False

def create_endpoint():
    """Create SageMaker endpoint"""
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    
    print(f"Creating endpoint: {ENDPOINT_NAME}")
    
    try:
        response = sagemaker.create_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=ENDPOINT_CONFIG_NAME,
            Tags=[
                {'Key': 'Project', 'Value': 'AquaChain'},
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'Version', 'Value': 'working'},
            ]
        )
        print(f"✅ Endpoint creation started: {response['EndpointArn']}")
        return True
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Endpoint {ENDPOINT_NAME} already exists, checking status...")
            return True
        else:
            print(f"❌ Error creating endpoint: {str(e)}")
            return False

def wait_for_endpoint():
    """Wait for endpoint to be in service"""
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    
    print(f"Waiting for endpoint {ENDPOINT_NAME} to be in service...")
    
    max_wait_time = 20 * 60  # 20 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = sagemaker.describe_endpoint(EndpointName=ENDPOINT_NAME)
            status = response['EndpointStatus']
            
            print(f"Endpoint status: {status}")
            
            if status == 'InService':
                print(f"✅ Endpoint {ENDPOINT_NAME} is now in service!")
                return True
            elif status in ['Failed', 'RollingBack']:
                print(f"❌ Endpoint deployment failed with status: {status}")
                if 'FailureReason' in response:
                    print(f"Failure reason: {response['FailureReason']}")
                return False
            
            time.sleep(30)  # Wait 30 seconds before checking again
            
        except Exception as e:
            print(f"Error checking endpoint status: {str(e)}")
            time.sleep(30)
    
    print(f"❌ Timeout waiting for endpoint to be ready")
    return False

def test_endpoint():
    """Test the deployed endpoint"""
    runtime = boto3.client('sagemaker-runtime', region_name=REGION)
    
    # Test data - good water quality
    test_data = [7.2, 2.5, 450, 25.0]  # pH, turbidity, TDS, temperature
    csv_data = ",".join(map(str, test_data))
    
    print(f"Testing endpoint with data: {csv_data}")
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',
            Body=csv_data
        )
        
        result = response['Body'].read().decode()
        print(f"✅ Endpoint test successful!")
        print(f"Raw response: {result}")
        
        # Parse prediction
        try:
            prediction = float(result.strip())
            quality_labels = ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
            quality = quality_labels[int(prediction)] if int(prediction) < len(quality_labels) else "Unknown"
            print(f"Predicted class: {int(prediction)} ({quality})")
        except ValueError:
            print(f"Response: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint test failed: {str(e)}")
        return False

def main():
    """Main deployment pipeline"""
    print("=== Deploying Working SageMaker Endpoint ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Step 1: Create model
    if not create_sagemaker_model():
        return False
    
    # Step 2: Create endpoint configuration
    if not create_endpoint_config():
        return False
    
    # Step 3: Create endpoint
    if not create_endpoint():
        return False
    
    # Step 4: Wait for endpoint to be ready
    if not wait_for_endpoint():
        return False
    
    # Step 5: Test endpoint
    if not test_endpoint():
        return False
    
    print(f"\n🎉 Deployment completed successfully!")
    print(f"Endpoint name: {ENDPOINT_NAME}")
    print(f"You can now use this endpoint for ML inference.")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)