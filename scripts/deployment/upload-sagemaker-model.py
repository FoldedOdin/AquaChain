"""
Upload ML models to S3 for SageMaker deployment
"""
import boto3
import tarfile
import os
import shutil
from pathlib import Path

def package_model_for_sagemaker(model_dir, output_file):
    """Package model files into tar.gz format for SageMaker"""
    print(f"Packaging model from {model_dir}...")
    
    # Create tar.gz file
    with tarfile.open(output_file, "w:gz") as tar:
        # Add model files
        for file in os.listdir(model_dir):
            if file.endswith(('.pkl', '.json')):
                file_path = os.path.join(model_dir, file)
                tar.add(file_path, arcname=file)
                print(f"  Added: {file}")
    
    print(f"Model packaged: {output_file}")
    return output_file

def upload_to_s3(file_path, bucket_name, s3_key):
    """Upload file to S3"""
    print(f"Uploading to s3://{bucket_name}/{s3_key}...")
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f"✓ Upload successful!")
        return True
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        return False

def main():
    # Get AWS account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    # Configuration
    model_dir = "lambda/ml_inference/models"
    bucket_name = f"aquachain-bucket-ml-models-{account_id}-dev"
    
    # Package WQI model
    wqi_tar = "wqi-model.tar.gz"
    package_model_for_sagemaker(model_dir, wqi_tar)
    
    # Upload to S3
    success = upload_to_s3(wqi_tar, bucket_name, "models/wqi-model.tar.gz")
    
    # Cleanup
    if os.path.exists(wqi_tar):
        os.remove(wqi_tar)
        print(f"Cleaned up local file: {wqi_tar}")
    
    if success:
        print("\n✓ Model ready for SageMaker deployment!")
        print(f"  S3 Location: s3://{bucket_name}/models/wqi-model.tar.gz")
    else:
        print("\n✗ Model upload failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
