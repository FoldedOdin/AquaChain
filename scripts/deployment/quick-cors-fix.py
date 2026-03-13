#!/usr/bin/env python3
"""
Quick CORS Fix - Deploy via CDK
Updates the API stack to ensure alerts endpoint has proper CORS
"""

import subprocess
import sys
import os

def deploy_cors_fix():
    """Deploy CORS fix via CDK"""
    
    print("🔧 Deploying CORS fix via CDK...")
    
    # Change to CDK directory
    cdk_dir = "infrastructure/cdk"
    if not os.path.exists(cdk_dir):
        print("❌ CDK directory not found!")
        return False
    
    try:
        # Step 1: Synthesize the stack to check for errors
        print("📋 Step 1: Synthesizing CDK stack...")
        result = subprocess.run([
            "cdk", "synth", "AquaChain-API-dev", "--quiet"
        ], cwd=cdk_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ CDK synth failed: {result.stderr}")
            return False
        
        print("✅ CDK synthesis successful")
        
        # Step 2: Deploy the API stack
        print("🚀 Step 2: Deploying API stack...")
        result = subprocess.run([
            "cdk", "deploy", "AquaChain-API-dev", "--require-approval", "never"
        ], cwd=cdk_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ CDK deploy failed: {result.stderr}")
            print("Full output:", result.stdout)
            return False
        
        print("✅ CDK deployment successful!")
        print("🎯 CORS configuration should now be updated")
        
        # Step 3: Test the endpoint
        print("🧪 Step 3: Testing the endpoint...")
        print("Run this in your browser console:")
        print("fetch('https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/alerts', {method: 'OPTIONS'})")
        print("  .then(r => console.log('Status:', r.status))")
        
        return True
        
    except FileNotFoundError:
        print("❌ CDK CLI not found. Please install AWS CDK:")
        print("npm install -g aws-cdk")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_cors_fix()
    sys.exit(0 if success else 1)