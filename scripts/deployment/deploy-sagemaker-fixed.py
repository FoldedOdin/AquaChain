#!/usr/bin/env python3
"""
Deploy SageMaker stack after fixing all CDK issues
"""

import subprocess
import sys
import os
import time

def main():
    """Deploy the fixed SageMaker stack"""
    
    print("🚀 Deploying AquaChain SageMaker Stack (Fixed Version)")
    print("=" * 60)
    
    # Change to CDK directory
    cdk_dir = os.path.join(os.path.dirname(__file__), "..", "..", "infrastructure", "cdk")
    os.chdir(cdk_dir)
    
    print("📍 Working directory:", os.getcwd())
    
    try:
        print("\n🔍 Step 1: Validating CDK stack...")
        
        # First try a quick synth to validate
        result = subprocess.run([
            "npx", "cdk", "synth", "AquaChain-SageMaker-dev", 
            "--no-staging", "--quiet"
        ], capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            print("❌ CDK synth failed:")
            print("STDERR:", result.stderr)
            return False
            
        print("✅ CDK stack validation successful!")
        
        print("\n🚀 Step 2: Deploying to AWS...")
        
        # Deploy the stack
        deploy_result = subprocess.run([
            "npx", "cdk", "deploy", "AquaChain-SageMaker-dev", 
            "--require-approval", "never"
        ], text=True, timeout=1800)  # 30 minutes timeout
        
        if deploy_result.returncode == 0:
            print("\n🎉 SageMaker stack deployed successfully!")
            print("\n📋 What was created:")
            print("  ✅ S3 bucket for ML model storage")
            print("  ✅ IAM roles for SageMaker operations")
            print("  ✅ SageMaker model, endpoint config, and endpoint")
            print("  ✅ Lambda function for training job management")
            print("  ✅ CloudWatch monitoring and alarms")
            print("  ✅ Proper resource tagging")
            
            print("\n🔧 Next steps:")
            print("  1. Upload ML model artifacts to the S3 bucket")
            print("  2. Test the training job Lambda function")
            print("  3. Configure SageMaker endpoints for inference")
            
            return True
        else:
            print("❌ Deployment failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Deployment timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)