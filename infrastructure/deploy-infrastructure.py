#!/usr/bin/env python3
"""
AquaChain Infrastructure Deployment Script
Deploys the complete AquaChain infrastructure to AWS
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def run_command(command, cwd=None, check=True, env=None):
    """Run a command and return the result"""
    print(f"🔧 Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True,
            env=env
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def load_environment_variables():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("📋 Loading environment variables from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    if not key.endswith('_SECRET'):  # Don't print secrets
                        print(f"   {key}={value}")

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Load environment variables first
    load_environment_variables()
    
    # Check Python
    try:
        result = run_command("python --version")
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python not found")
        return False
    
    # Check AWS CLI
    try:
        result = run_command("aws --version")
        print(f"✅ AWS CLI: {result.stdout.strip()}")
    except:
        print("❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/")
        return False
    
    # Check AWS credentials
    try:
        result = run_command("aws sts get-caller-identity")
        identity = json.loads(result.stdout)
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ AWS User: {identity['Arn']}")
        
        # Store account ID for CDK
        os.environ['CDK_DEFAULT_ACCOUNT'] = identity['Account']
        
    except:
        print("❌ AWS credentials not configured.")
        print("   Option 1: Run 'aws configure'")
        print("   Option 2: Set environment variables in .env file")
        print("   Option 3: Use IAM roles (for EC2/Lambda)")
        return False
    
    # Check CDK
    try:
        result = run_command("cdk --version")
        print(f"✅ CDK: {result.stdout.strip()}")
    except:
        print("❌ CDK not found. Installing...")
        run_command("npm install -g aws-cdk")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print("🐍 Setting up Python environment...")
    
    cdk_dir = Path(__file__).parent / "cdk"
    
    # Create virtual environment if it doesn't exist
    venv_dir = cdk_dir / "venv"
    if not venv_dir.exists():
        print("Creating Python virtual environment...")
        run_command("python -m venv venv", cwd=cdk_dir)
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate.bat"
        pip_cmd = str(venv_dir / "Scripts" / "pip")
    else:  # Unix/Linux/macOS
        activate_script = venv_dir / "bin" / "activate"
        pip_cmd = str(venv_dir / "bin" / "pip")
    
    print("Installing Python dependencies...")
    run_command(f"{pip_cmd} install -r requirements.txt", cwd=cdk_dir)
    
    return venv_dir

def bootstrap_cdk(region=None):
    """Bootstrap CDK in the AWS account"""
    if region is None:
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    print(f"🚀 Bootstrapping CDK in region {region}...")
    
    cdk_dir = Path(__file__).parent / "cdk"
    
    # Check if already bootstrapped
    try:
        result = run_command(
            f"aws cloudformation describe-stacks --stack-name CDKToolkit --region {region}",
            check=False
        )
        if result.returncode == 0:
            print("✅ CDK already bootstrapped")
            return True
    except:
        pass
    
    # Bootstrap CDK
    # Get account ID first
    account_result = run_command("aws sts get-caller-identity --query Account --output text")
    account_id = account_result.stdout.strip()
    
    # Set up environment to use virtual environment Python
    venv_dir = cdk_dir / "venv"
    env = os.environ.copy()
    if os.name == 'nt':  # Windows
        env['PATH'] = str(venv_dir / "Scripts") + ";" + env['PATH']
    else:  # Unix/Linux/macOS
        env['PATH'] = str(venv_dir / "bin") + ":" + env['PATH']
    
    run_command(f"cdk bootstrap aws://{account_id}/{region}", cwd=cdk_dir, env=env)
    print("✅ CDK bootstrapped successfully")
    return True

def deploy_stacks(environment="dev"):
    """Deploy all CDK stacks"""
    print(f"🚀 Deploying AquaChain infrastructure for environment: {environment}")
    
    cdk_dir = Path(__file__).parent / "cdk"
    
    # Set environment context
    context_args = f"--context environment={environment}"
    
    # Deploy stacks in order
    stacks = [
        f"AquaChain-Security-{environment}",
        f"AquaChain-Core-{environment}",
        f"AquaChain-Data-{environment}",
        f"AquaChain-Compute-{environment}",
        f"AquaChain-API-{environment}",
        f"AquaChain-Monitoring-{environment}",
        f"AquaChain-DR-{environment}",
        f"AquaChain-LandingPage-{environment}"
    ]
    
    print("📋 Deployment plan:")
    for i, stack in enumerate(stacks, 1):
        print(f"  {i}. {stack}")
    
    print("\n🚀 Starting deployment...")
    
    for i, stack in enumerate(stacks, 1):
        print(f"\n📦 Deploying stack {i}/{len(stacks)}: {stack}")
        
        try:
            run_command(
                f"cdk deploy {stack} {context_args} --require-approval never",
                cwd=cdk_dir
            )
            print(f"✅ {stack} deployed successfully")
        except Exception as e:
            print(f"❌ Failed to deploy {stack}: {e}")
            
            # Ask if user wants to continue
            response = input("Continue with remaining stacks? (y/n): ")
            if response.lower() != 'y':
                print("Deployment stopped by user")
                return False
    
    print("\n🎉 All stacks deployed successfully!")
    return True

def get_stack_outputs(environment="dev"):
    """Get outputs from deployed stacks"""
    print(f"📋 Getting stack outputs for environment: {environment}")
    
    api_stack_name = f"AquaChain-API-{environment}"
    
    try:
        result = run_command(
            f"aws cloudformation describe-stacks --stack-name {api_stack_name} --query 'Stacks[0].Outputs' --output json"
        )
        
        outputs = json.loads(result.stdout)
        
        print("\n📊 Stack Outputs:")
        print("=" * 50)
        
        config = {}
        for output in outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            description = output.get('Description', '')
            
            print(f"{key}: {value}")
            if description:
                print(f"  Description: {description}")
            
            # Store key values for frontend config
            if key == 'RestAPIEndpoint':
                config['api_endpoint'] = value
            elif key == 'WebSocketAPIEndpoint':
                config['websocket_endpoint'] = value
            elif key == 'UserPoolId':
                config['user_pool_id'] = value
            elif key == 'UserPoolClientId':
                config['user_pool_client_id'] = value
        
        return config
        
    except Exception as e:
        print(f"❌ Failed to get stack outputs: {e}")
        return None

def create_frontend_config(config, environment="dev"):
    """Create frontend configuration file"""
    print("📝 Creating frontend configuration...")
    
    frontend_dir = Path(__file__).parent.parent / "frontend"
    
    env_content = f"""# Production Environment Configuration - Generated {time.strftime('%Y-%m-%d %H:%M:%S')}
# Environment: {environment}

# AWS Configuration
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID={config.get('user_pool_id', 'NOT_FOUND')}
REACT_APP_USER_POOL_CLIENT_ID={config.get('user_pool_client_id', 'NOT_FOUND')}
REACT_APP_IDENTITY_POOL_ID=us-east-1:your-identity-pool-id

# API Configuration
REACT_APP_API_ENDPOINT={config.get('api_endpoint', 'NOT_FOUND')}
REACT_APP_WEBSOCKET_ENDPOINT={config.get('websocket_endpoint', 'NOT_FOUND')}

# Analytics Configuration
REACT_APP_PINPOINT_APPLICATION_ID=your-pinpoint-app-id
REACT_APP_AWS_ACCESS_KEY_ID=your-access-key-id
REACT_APP_AWS_SECRET_ACCESS_KEY=your-secret-access-key
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Security Configuration
REACT_APP_RECAPTCHA_SITE_KEY=your_production_recaptcha_key

# Feature Flags
REACT_APP_ENABLE_PRODUCTION_MODE=true
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AB_TESTING=true

# RUM Configuration
REACT_APP_RUM_ENDPOINT={config.get('api_endpoint', 'NOT_FOUND')}/api/rum
"""
    
    # Write to .env.production
    env_file = frontend_dir / ".env.production"
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created {env_file}")
    
    # Also create .env.local for immediate use
    env_local = frontend_dir / ".env.local"
    with open(env_local, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created {env_local}")

def main():
    """Main deployment function"""
    print("🌊 AquaChain Infrastructure Deployment")
    print("=" * 50)
    
    # Get environment from command line
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    
    print(f"Target environment: {environment}")
    print(f"AWS Region: {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please install missing components.")
        sys.exit(1)
    
    # Setup Python environment
    setup_python_environment()
    
    # Bootstrap CDK
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    bootstrap_cdk(region)
    
    # Deploy stacks
    if deploy_stacks(environment):
        print("\n🎉 Infrastructure deployment completed!")
        
        # Get stack outputs
        config = get_stack_outputs(environment)
        
        if config:
            # Create frontend configuration
            create_frontend_config(config, environment)
            
            print("\n🚀 Next Steps:")
            print("1. Review the generated .env.production file")
            print("2. Create users in AWS Cognito console")
            print("3. Switch frontend to AWS mode: cd frontend && npm run switch-to-aws")
            print("4. Start your app: npm start")
            print("\n✅ Your AquaChain infrastructure is ready!")
        else:
            print("⚠️  Could not retrieve stack outputs. Check AWS console for deployed resources.")
    else:
        print("❌ Infrastructure deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()