#!/bin/bash

# AquaChain CDK Environment Setup Script
# This script sets up the development environment for CDK deployment

set -e

echo "Setting up AquaChain CDK Environment"
echo "===================================="

# Check if Python 3.11+ is installed
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"

# Check if Node.js is installed (required for CDK CLI)
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required for AWS CDK CLI"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
node_version=$(node --version)
echo "✓ Node.js version: $node_version"

# Check if AWS CLI is installed
echo "Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is required"
    echo "Please install AWS CLI from https://aws.amazon.com/cli/"
    exit 1
fi
aws_version=$(aws --version)
echo "✓ AWS CLI: $aws_version"

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured"
    echo "Please run 'aws configure' to set up your credentials"
    exit 1
fi
account_id=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account ID: $account_id"

# Install CDK CLI globally if not present
echo "Checking CDK CLI..."
if ! command -v cdk &> /dev/null; then
    echo "Installing AWS CDK CLI..."
    npm install -g aws-cdk
else
    cdk_version=$(cdk --version)
    echo "✓ CDK CLI version: $cdk_version"
fi

# Create Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Created virtual environment"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Verify CDK installation
echo "Verifying CDK installation..."
cdk --version
python -c "import aws_cdk_lib; print(f'✓ CDK Python library version: {aws_cdk_lib.__version__}')"

# Create environment-specific configuration files if they don't exist
echo "Setting up environment configurations..."

# Development environment
if [ ! -f "config/dev.json" ]; then
    cat > config/dev.json << EOF
{
  "environment": "dev",
  "region": "us-east-1",
  "domain_name": "dev.aquachain.io",
  "enable_deletion_protection": false,
  "enable_detailed_monitoring": false,
  "notification_emails": ["dev-team@aquachain.io"]
}
EOF
    echo "✓ Created dev.json configuration"
fi

# Staging environment
if [ ! -f "config/staging.json" ]; then
    cat > config/staging.json << EOF
{
  "environment": "staging",
  "region": "us-east-1",
  "domain_name": "staging.aquachain.io",
  "enable_deletion_protection": true,
  "enable_detailed_monitoring": true,
  "notification_emails": ["staging-alerts@aquachain.io"]
}
EOF
    echo "✓ Created staging.json configuration"
fi

# Production environment
if [ ! -f "config/prod.json" ]; then
    cat > config/prod.json << EOF
{
  "environment": "prod",
  "region": "us-east-1",
  "domain_name": "api.aquachain.io",
  "enable_deletion_protection": true,
  "enable_detailed_monitoring": true,
  "notification_emails": ["alerts@aquachain.io", "oncall@aquachain.io"]
}
EOF
    echo "✓ Created prod.json configuration"
fi

# Create deployment scripts
echo "Creating deployment scripts..."

# Quick deploy script
cat > scripts/quick-deploy.sh << 'EOF'
#!/bin/bash
# Quick deployment script for development

set -e

ENVIRONMENT=${1:-dev}

echo "Quick deploying to $ENVIRONMENT environment..."

# Activate virtual environment
source venv/bin/activate

# Deploy all stacks
python deployment/deploy.py --environment $ENVIRONMENT --action deploy --auto-approve

echo "✓ Quick deployment completed"
EOF

chmod +x scripts/quick-deploy.sh

# Full deploy script
cat > scripts/full-deploy.sh << 'EOF'
#!/bin/bash
# Full deployment script with validation

set -e

ENVIRONMENT=${1:-dev}

echo "Full deployment to $ENVIRONMENT environment..."

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Synthesize stacks
echo "Synthesizing stacks..."
python deployment/deploy.py --environment $ENVIRONMENT --action synth

# Deploy stacks
echo "Deploying stacks..."
python deployment/deploy.py --environment $ENVIRONMENT --action deploy

# Validate deployment
echo "Validating deployment..."
python validation/validate_infrastructure.py --environment $ENVIRONMENT

echo "✓ Full deployment completed successfully"
EOF

chmod +x scripts/full-deploy.sh

# Destroy script
cat > scripts/destroy.sh << 'EOF'
#!/bin/bash
# Destroy infrastructure script

set -e

ENVIRONMENT=${1:-dev}

echo "WARNING: This will destroy all infrastructure for $ENVIRONMENT environment"
read -p "Are you sure? Type 'yes' to continue: " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Destruction cancelled"
    exit 0
fi

# Activate virtual environment
source venv/bin/activate

# Destroy stacks
python deployment/deploy.py --environment $ENVIRONMENT --action destroy --auto-approve

echo "✓ Infrastructure destroyed"
EOF

chmod +x scripts/destroy.sh

echo "✓ Created deployment scripts"

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# CDK
cdk.out/
cdk.out.*/
*.d.ts
node_modules/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment specific
config/local.json
outputs-*.json

# Secrets
.env
.env.local
secrets.json
EOF
    echo "✓ Created .gitignore"
fi

# Create README
if [ ! -f "README.md" ]; then
    cat > README.md << 'EOF'
# AquaChain CDK Infrastructure

This directory contains the AWS CDK infrastructure code for the AquaChain water quality monitoring system.

## Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI configured with appropriate credentials
- AWS CDK CLI

## Setup

Run the setup script to configure your environment:

```bash
./scripts/setup_cdk_environment.sh
```

## Deployment

### Quick Development Deployment

```bash
./scripts/quick-deploy.sh dev
```

### Full Production Deployment

```bash
./scripts/full-deploy.sh prod
```

### Manual Deployment

```bash
# Activate virtual environment
source venv/bin/activate

# Bootstrap CDK (first time only)
python deployment/deploy.py --environment dev --action bootstrap

# Deploy all stacks
python deployment/deploy.py --environment dev --action deploy

# Deploy specific stack
python deployment/deploy.py --environment dev --action deploy --stack Security

# Validate deployment
python validation/validate_infrastructure.py --environment dev
```

## Environments

- **dev**: Development environment with minimal resources
- **staging**: Staging environment with production-like configuration
- **prod**: Production environment with full security and monitoring

## Stack Architecture

1. **Security Stack**: KMS keys, IAM roles, security policies
2. **Core Stack**: VPC, networking, shared resources
3. **Data Stack**: DynamoDB tables, S3 buckets, IoT Core
4. **Compute Stack**: Lambda functions, SageMaker, SNS topics
5. **API Stack**: API Gateway, Cognito, WAF
6. **Monitoring Stack**: CloudWatch dashboards, alarms, X-Ray

## Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run infrastructure validation
python validation/validate_infrastructure.py --environment dev
```

## Cleanup

```bash
./scripts/destroy.sh dev
```
EOF
    echo "✓ Created README.md"
fi

echo ""
echo "🎉 AquaChain CDK Environment Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Bootstrap CDK: python deployment/deploy.py --environment dev --action bootstrap"
echo "3. Deploy infrastructure: ./scripts/quick-deploy.sh dev"
echo "4. Validate deployment: python validation/validate_infrastructure.py --environment dev"
echo ""
echo "For more information, see README.md"