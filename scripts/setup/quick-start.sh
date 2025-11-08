#!/bin/bash

# AquaChain Quick Start Script
# This script helps you get the project running quickly

set -e

echo "🚀 AquaChain Quick Start"
echo "======================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js not found${NC}"
    echo "   Install from: https://nodejs.org"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python not found${NC}"
    echo "   Install Python 3.11+"
    exit 1
fi

# Check AWS CLI
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version)
    echo -e "${GREEN}✅ AWS CLI installed: $AWS_VERSION${NC}"
else
    echo -e "${RED}❌ AWS CLI not found${NC}"
    echo "   Install from: https://aws.amazon.com/cli/"
    exit 1
fi

echo ""
echo "🎯 What would you like to do?"
echo ""
echo "1) Full setup (Infrastructure + Frontend)"
echo "2) Frontend only (Development mode)"
echo "3) Infrastructure only"
echo "4) Just install dependencies"
echo "5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🏗️  Full Setup Selected"
        echo "====================="
        echo ""
        
        # Install root dependencies
        echo "📦 Installing root dependencies..."
        npm install
        
        # Install frontend dependencies
        echo "📦 Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
        
        # Install Python dependencies
        echo "📦 Installing Python dependencies..."
        pip3 install -r requirements-dev.txt
        
        # Check AWS credentials
        echo ""
        echo "🔐 Checking AWS credentials..."
        if aws sts get-caller-identity &> /dev/null; then
            echo -e "${GREEN}✅ AWS credentials configured${NC}"
            
            # Ask if user wants to deploy
            echo ""
            read -p "Deploy infrastructure now? (y/n): " deploy
            if [ "$deploy" = "y" ]; then
                echo ""
                echo "🚀 Deploying infrastructure..."
                ./deploy-all.sh
            else
                echo ""
                echo -e "${YELLOW}⚠️  Skipping deployment${NC}"
                echo "   Run './deploy-all.sh' when ready to deploy"
            fi
        else
            echo -e "${RED}❌ AWS credentials not configured${NC}"
            echo ""
            echo "Configure AWS credentials:"
            echo "  aws configure"
            exit 1
        fi
        ;;
        
    2)
        echo ""
        echo "💻 Frontend Development Setup"
        echo "============================"
        echo ""
        
        # Install frontend dependencies
        echo "📦 Installing frontend dependencies..."
        cd frontend
        npm install
        
        # Check if .env exists
        if [ ! -f ".env.development" ]; then
            echo ""
            echo "📝 Creating .env.development..."
            if [ -f ".env.example" ]; then
                cp .env.example .env.development
                echo -e "${YELLOW}⚠️  Please edit frontend/.env.development with your AWS settings${NC}"
            else
                echo -e "${RED}❌ .env.example not found${NC}"
            fi
        fi
        
        echo ""
        echo -e "${GREEN}✅ Frontend setup complete!${NC}"
        echo ""
        echo "To start development server:"
        echo "  cd frontend"
        echo "  npm start"
        cd ..
        ;;
        
    3)
        echo ""
        echo "🏗️  Infrastructure Setup"
        echo "======================"
        echo ""
        
        # Install CDK dependencies
        echo "📦 Installing CDK dependencies..."
        cd infrastructure/cdk
        pip3 install -r requirements.txt
        
        # Check AWS credentials
        echo ""
        echo "🔐 Checking AWS credentials..."
        if aws sts get-caller-identity &> /dev/null; then
            echo -e "${GREEN}✅ AWS credentials configured${NC}"
            
            # Ask if user wants to bootstrap
            echo ""
            read -p "Bootstrap CDK? (required first time) (y/n): " bootstrap
            if [ "$bootstrap" = "y" ]; then
                echo ""
                echo "🔧 Bootstrapping CDK..."
                cdk bootstrap
            fi
            
            # Ask if user wants to deploy
            echo ""
            read -p "Deploy infrastructure now? (y/n): " deploy
            if [ "$deploy" = "y" ]; then
                echo ""
                echo "🚀 Deploying infrastructure..."
                cdk deploy --all
            else
                echo ""
                echo -e "${YELLOW}⚠️  Skipping deployment${NC}"
                echo "   Run 'cdk deploy --all' when ready"
            fi
        else
            echo -e "${RED}❌ AWS credentials not configured${NC}"
            echo ""
            echo "Configure AWS credentials:"
            echo "  aws configure"
            exit 1
        fi
        cd ../..
        ;;
        
    4)
        echo ""
        echo "📦 Installing Dependencies Only"
        echo "=============================="
        echo ""
        
        # Install root dependencies
        echo "📦 Installing root dependencies..."
        npm install
        
        # Install frontend dependencies
        echo "📦 Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
        
        # Install Python dependencies
        echo "📦 Installing Python dependencies..."
        pip3 install -r requirements-dev.txt
        
        echo ""
        echo -e "${GREEN}✅ All dependencies installed!${NC}"
        ;;
        
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "✨ Setup Complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Read SETUP_GUIDE.md for detailed instructions"
echo "   2. Read PROJECT_REPORT.md for comprehensive documentation"
echo "   3. Read README_START_HERE.md for navigation"
echo ""
echo "🚀 Quick commands:"
echo "   Frontend dev:  cd frontend && npm start"
echo "   Deploy all:    ./deploy-all.sh"
echo "   Run tests:     npm test"
echo ""
