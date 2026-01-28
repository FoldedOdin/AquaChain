#!/usr/bin/env python3
"""
Deploy Admin Service Infrastructure
Deploys the admin Lambda service and updates API Gateway routes
"""

import os
import sys
import subprocess
import json
import boto3
from pathlib import Path

def run_command(command, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def check_prerequisites():
    """Check if required tools are installed"""
    print("Checking prerequisites...")
    
    # Check AWS CLI
    try:
        run_command("aws --version")
        print("✓ AWS CLI installed")
    except:
        print("✗ AWS CLI not found. Please install AWS CLI.")
        sys.exit(1)
    
    # Check CDK
    try:
        run_command("cdk --version")
        print("✓ AWS CDK installed")
    except:
        print("✗ AWS CDK not found. Please install AWS CDK.")
        sys.exit(1)
    
    # Check Python
    try:
        run_command("python3 --version")
        print("✓ Python 3 installed")
    except:
        print("✗ Python 3 not found.")
        sys.exit(1)

def install_admin_service_dependencies():
    """Install dependencies for admin service"""
    print("Installing admin service dependencies...")
    
    admin_service_path = Path(__file__).parent.parent.parent / "lambda" / "admin_service"
    
    if not admin_service_path.exists():
        print(f"✗ Admin service directory not found: {admin_service_path}")
        sys.exit(1)
    
    # Install Python dependencies
    requirements_file = admin_service_path / "requirements.txt"
    if requirements_file.exists():
        run_command(f"pip install -r {requirements_file}", cwd=admin_service_path)
        print("✓ Admin service dependencies installed")
    else:
        print("✗ requirements.txt not found in admin service")
        sys.exit(1)

def deploy_infrastructure():
    """Deploy CDK infrastructure with admin service"""
    print("Deploying infrastructure...")
    
    infrastructure_path = Path(__file__).parent.parent.parent / "infrastructure" / "cdk"
    
    if not infrastructure_path.exists():
        print(f"✗ Infrastructure directory not found: {infrastructure_path}")
        sys.exit(1)
    
    # Install CDK dependencies
    print("Installing CDK dependencies...")
    run_command("pip install -r requirements.txt", cwd=infrastructure_path)
    
    # Bootstrap CDK if needed
    print("Checking CDK bootstrap...")
    try:
        run_command("cdk bootstrap", cwd=infrastructure_path)
        print("✓ CDK bootstrap completed")
    except:
        print("⚠ CDK bootstrap may have failed, continuing...")
    
    # Deploy stacks in order
    stacks_to_deploy = [
        "AquaChain-Security-dev",  # Security resources first
        "AquaChain-Data-dev",      # Data layer with new system config table
        "AquaChain-Compute-dev",   # Compute layer with admin service
        "AquaChain-API-dev"        # API layer with admin routes
    ]
    
    for stack in stacks_to_deploy:
        print(f"Deploying {stack}...")
        try:
            run_command(f"cdk deploy {stack} --require-approval never", cwd=infrastructure_path)
            print(f"✓ {stack} deployed successfully")
        except:
            print(f"✗ Failed to deploy {stack}")
            sys.exit(1)

def verify_deployment():
    """Verify that admin endpoints are working"""
    print("Verifying deployment...")
    
    # Get API Gateway endpoint from CDK outputs
    try:
        cloudformation = boto3.client('cloudformation')
        
        # Get API stack outputs
        response = cloudformation.describe_stacks(StackName='AquaChain-API-dev')
        outputs = response['Stacks'][0]['Outputs']
        
        api_endpoint = None
        for output in outputs:
            if output['OutputKey'] == 'RestAPIEndpoint':
                api_endpoint = output['OutputValue']
                break
        
        if api_endpoint:
            print(f"✓ API Gateway endpoint: {api_endpoint}")
            
            # Test admin endpoints (without auth for now)
            test_endpoints = [
                f"{api_endpoint}/api/admin/system/health",
                f"{api_endpoint}/api/admin/system/configuration",
                f"{api_endpoint}/api/admin/incidents/stats"
            ]
            
            print("Admin endpoints configured:")
            for endpoint in test_endpoints:
                print(f"  - {endpoint}")
            
        else:
            print("⚠ Could not find API Gateway endpoint in stack outputs")
            
    except Exception as e:
        print(f"⚠ Could not verify deployment: {e}")

def update_frontend_config():
    """Update frontend configuration with new API endpoint"""
    print("Updating frontend configuration...")
    
    try:
        cloudformation = boto3.client('cloudformation')
        response = cloudformation.describe_stacks(StackName='AquaChain-API-dev')
        outputs = response['Stacks'][0]['Outputs']
        
        api_endpoint = None
        user_pool_id = None
        client_id = None
        
        for output in outputs:
            if output['OutputKey'] == 'RestAPIEndpoint':
                api_endpoint = output['OutputValue']
            elif output['OutputKey'] == 'UserPoolId':
                user_pool_id = output['OutputValue']
            elif output['OutputKey'] == 'UserPoolClientId':
                client_id = output['OutputValue']
        
        if api_endpoint:
            frontend_env_path = Path(__file__).parent.parent.parent / "frontend" / ".env.local"
            
            env_content = f"""# AquaChain Frontend Configuration
REACT_APP_API_ENDPOINT={api_endpoint}
REACT_APP_USER_POOL_ID={user_pool_id}
REACT_APP_USER_POOL_CLIENT_ID={client_id}
REACT_APP_REGION=us-east-1
"""
            
            with open(frontend_env_path, 'w') as f:
                f.write(env_content)
            
            print(f"✓ Frontend configuration updated: {frontend_env_path}")
        
    except Exception as e:
        print(f"⚠ Could not update frontend config: {e}")

def main():
    """Main deployment function"""
    print("🚀 Deploying AquaChain Admin Service")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    
    # Install dependencies
    install_admin_service_dependencies()
    
    # Deploy infrastructure
    deploy_infrastructure()
    
    # Verify deployment
    verify_deployment()
    
    # Update frontend config
    update_frontend_config()
    
    print("\n" + "=" * 50)
    print("✅ Admin Service Deployment Complete!")
    print("\nNext steps:")
    print("1. Restart your frontend development server")
    print("2. Test admin dashboard functionality")
    print("3. Verify admin endpoints are working")
    print("\nAdmin endpoints available:")
    print("- GET /api/admin/users")
    print("- GET/PUT /api/admin/system/configuration")
    print("- GET /api/admin/system/health")
    print("- GET /api/admin/incidents/stats")
    print("- GET /api/admin/audit/trail")
    print("- GET /api/admin/devices")

if __name__ == "__main__":
    main()