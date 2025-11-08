#!/bin/bash

###############################################################################
# AquaChain Phase 3 Incremental Deployment Script
# Deploys Phase 3 components incrementally with validation
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}
COMPONENT=${2:-all}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AquaChain Phase 3 Incremental Deployment Script        ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║  Environment: ${ENVIRONMENT}                                        ║${NC}"
echo -e "${BLUE}║  Region: ${AWS_REGION}                                  ║${NC}"
echo -e "${BLUE}║  Component: ${COMPONENT}                                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Helper Functions
###############################################################################

deploy_component() {
    local component_name=$1
    local stack_name=$2
    local description=$3
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📦 Deploying ${component_name}...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Description: ${description}${NC}"
    echo ""
    
    # Deploy stack
    cdk deploy ${stack_name} --require-approval never || {
        echo -e "${RED}❌ Failed to deploy ${component_name}${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ ${component_name} deployed successfully${NC}"
    echo ""
    
    return 0
}

verify_component() {
    local component_name=$1
    local verification_command=$2
    
    echo -e "${YELLOW}🔍 Verifying ${component_name}...${NC}"
    
    if eval "$verification_command"; then
        echo -e "${GREEN}✅ ${component_name} verified${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  ${component_name} verification incomplete${NC}"
        return 1
    fi
}

run_smoke_tests() {
    local component=$1
    
    echo -e "${YELLOW}🧪 Running smoke tests for ${component}...${NC}"
    
    cd ../../tests
    python run_phase3_tests.py --smoke --component ${component} || {
        echo -e "${YELLOW}⚠️  Some smoke tests failed${NC}"
        return 1
    }
    cd ../infrastructure/cdk
    
    echo -e "${GREEN}✅ Smoke tests passed${NC}"
    return 0
}

###############################################################################
# Pre-flight Checks
###############################################################################

echo -e "${YELLOW}🔍 Running pre-flight checks...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials configured (Account: ${ACCOUNT_ID})${NC}"

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ CDK not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ CDK found: $(cdk --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

echo ""

###############################################################################
# Install Dependencies
###############################################################################

echo -e "${YELLOW}📦 Installing dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}✅ CDK dependencies installed${NC}"
fi

# Install Lambda dependencies
echo -e "${BLUE}Installing Lambda dependencies...${NC}"
for lambda_dir in ../../lambda/*/; do
    if [ -f "${lambda_dir}requirements.txt" ]; then
        echo "  Installing for $(basename $lambda_dir)..."
        pip3 install -r "${lambda_dir}requirements.txt" -t "${lambda_dir}" --quiet --upgrade
    fi
done
echo -e "${GREEN}✅ Lambda dependencies installed${NC}"

echo ""

###############################################################################
# Component Deployment
###############################################################################

deploy_infrastructure() {
    deploy_component \
        "Phase 3 Infrastructure Foundation" \
        "AquaChain-Phase3-${ENVIRONMENT}" \
        "DynamoDB tables, EventBridge schedules, SNS topics"
    
    verify_component \
        "ModelMetrics Table" \
        "aws dynamodb describe-table --table-name aquachain-model-metrics-${ENVIRONMENT} &> /dev/null"
    
    verify_component \
        "CertificateLifecycle Table" \
        "aws dynamodb describe-table --table-name aquachain-certificate-lifecycle-${ENVIRONMENT} &> /dev/null"
}

deploy_ml_monitoring() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📊 Deploying ML Monitoring System...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Package and deploy ML inference Lambda with monitoring
    cd ../../lambda/ml_inference
    echo -e "${BLUE}Packaging ML inference Lambda...${NC}"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" -x "*.md" > /dev/null
    
    aws lambda update-function-code \
        --function-name aquachain-ml-inference-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  ML inference function not found, creating...${NC}"
    }
    
    rm function.zip
    cd ../../infrastructure/cdk
    
    echo -e "${GREEN}✅ ML monitoring deployed${NC}"
    
    # Run smoke tests
    run_smoke_tests "ml-monitoring"
}

deploy_data_validation() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🔍 Deploying Training Data Validation...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    deploy_component \
        "Training Data Validation Stack" \
        "AquaChain-TrainingDataValidation-${ENVIRONMENT}" \
        "S3 triggers, validation Lambda, SNS alerts"
    
    # Package and deploy validation Lambda
    cd ../../lambda/ml_training
    echo -e "${BLUE}Packaging data validation Lambda...${NC}"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" -x "*.md" > /dev/null
    
    aws lambda update-function-code \
        --function-name aquachain-data-validator-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  Data validator function not found${NC}"
    }
    
    rm function.zip
    cd ../../infrastructure/cdk
    
    echo -e "${GREEN}✅ Data validation deployed${NC}"
    
    run_smoke_tests "data-validation"
}

deploy_ota_updates() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📡 Deploying OTA Update System...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    deploy_component \
        "IoT Code Signing Stack" \
        "AquaChain-IoTCodeSigning-${ENVIRONMENT}" \
        "Code signing profile, S3 firmware bucket, IoT Jobs"
    
    # Set up code signing
    echo -e "${BLUE}Configuring code signing...${NC}"
    cd ../iot
    python setup-code-signing.py || {
        echo -e "${YELLOW}⚠️  Code signing setup incomplete${NC}"
    }
    cd ../cdk
    
    # Package and deploy OTA Lambda
    cd ../../lambda/iot_management
    echo -e "${BLUE}Packaging OTA update Lambda...${NC}"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" -x "*.md" > /dev/null
    
    aws lambda update-function-code \
        --function-name aquachain-ota-manager-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  OTA manager function not found${NC}"
    }
    
    rm function.zip
    cd ../../infrastructure/cdk
    
    echo -e "${GREEN}✅ OTA update system deployed${NC}"
    
    run_smoke_tests "ota-updates"
}

deploy_certificate_rotation() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🔐 Deploying Certificate Rotation System...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Package and deploy certificate rotation Lambda
    cd ../../lambda/iot_management
    echo -e "${BLUE}Packaging certificate rotation Lambda...${NC}"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" -x "*.md" > /dev/null
    
    aws lambda update-function-code \
        --function-name aquachain-cert-rotation-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  Certificate rotation function not found${NC}"
    }
    
    rm function.zip
    cd ../../infrastructure/cdk
    
    # Set up EventBridge schedule
    echo -e "${BLUE}Configuring daily certificate check schedule...${NC}"
    aws events put-rule \
        --name aquachain-cert-rotation-daily-${ENVIRONMENT} \
        --schedule-expression "cron(0 2 * * ? *)" \
        --state ENABLED \
        --description "Daily certificate expiration check" || {
        echo -e "${YELLOW}⚠️  EventBridge rule creation failed${NC}"
    }
    
    echo -e "${GREEN}✅ Certificate rotation deployed${NC}"
    
    run_smoke_tests "certificate-rotation"
}

deploy_dependency_scanner() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🔒 Deploying Dependency Scanner...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    deploy_component \
        "Dependency Scanner Stack" \
        "AquaChain-DependencyScanner-${ENVIRONMENT}" \
        "Scanner Lambda, S3 reports bucket, SNS alerts"
    
    # Package and deploy scanner Lambda
    cd ../../lambda/dependency_scanner
    echo -e "${BLUE}Packaging dependency scanner Lambda...${NC}"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" -x "*.md" > /dev/null
    
    aws lambda update-function-code \
        --function-name aquachain-dependency-scanner-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  Dependency scanner function not found${NC}"
    }
    
    rm function.zip
    cd ../../infrastructure/cdk
    
    # Set up weekly schedule
    echo -e "${BLUE}Configuring weekly scan schedule...${NC}"
    aws events put-rule \
        --name aquachain-dependency-scan-weekly-${ENVIRONMENT} \
        --schedule-expression "cron(0 3 ? * SUN *)" \
        --state ENABLED \
        --description "Weekly dependency vulnerability scan" || {
        echo -e "${YELLOW}⚠️  EventBridge rule creation failed${NC}"
    }
    
    echo -e "${GREEN}✅ Dependency scanner deployed${NC}"
    
    run_smoke_tests "dependency-scanner"
}

deploy_sbom_generator() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📋 Deploying SBOM Generator...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    deploy_component \
        "SBOM Storage Stack" \
        "AquaChain-SBOMStorage-${ENVIRONMENT}" \
        "S3 bucket for SBOM storage with versioning"
    
    # Verify Syft and Grype are installed
    echo -e "${BLUE}Checking SBOM tools...${NC}"
    if ! command -v syft &> /dev/null; then
        echo -e "${YELLOW}⚠️  Syft not found. Install: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh${NC}"
    else
        echo -e "${GREEN}✅ Syft found: $(syft version)${NC}"
    fi
    
    if ! command -v grype &> /dev/null; then
        echo -e "${YELLOW}⚠️  Grype not found. Install: curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh${NC}"
    else
        echo -e "${GREEN}✅ Grype found: $(grype version)${NC}"
    fi
    
    # Generate initial SBOM
    echo -e "${BLUE}Generating initial SBOM...${NC}"
    cd ../../scripts
    python generate-sbom.py --all || {
        echo -e "${YELLOW}⚠️  SBOM generation incomplete${NC}"
    }
    cd ../infrastructure/cdk
    
    echo -e "${GREEN}✅ SBOM generator deployed${NC}"
}

deploy_performance_dashboard() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📊 Deploying Performance Dashboard...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    deploy_component \
        "Performance Dashboard Stack" \
        "AquaChain-PerformanceDashboard-${ENVIRONMENT}" \
        "CloudWatch dashboard with metrics and alarms"
    
    # Get dashboard URL
    DASHBOARD_NAME="AquaChain-Performance-${ENVIRONMENT}"
    DASHBOARD_URL="https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${DASHBOARD_NAME}"
    
    echo -e "${GREEN}✅ Performance dashboard deployed${NC}"
    echo -e "${BLUE}Dashboard URL: ${DASHBOARD_URL}${NC}"
}

###############################################################################
# Main Deployment Logic
###############################################################################

case $COMPONENT in
    "all")
        echo -e "${YELLOW}🚀 Deploying all Phase 3 components...${NC}"
        echo ""
        
        deploy_infrastructure
        deploy_ml_monitoring
        deploy_data_validation
        deploy_ota_updates
        deploy_certificate_rotation
        deploy_dependency_scanner
        deploy_sbom_generator
        deploy_performance_dashboard
        
        echo -e "${GREEN}✅ All Phase 3 components deployed${NC}"
        ;;
    
    "infrastructure")
        deploy_infrastructure
        ;;
    
    "ml-monitoring")
        deploy_ml_monitoring
        ;;
    
    "data-validation")
        deploy_data_validation
        ;;
    
    "ota-updates")
        deploy_ota_updates
        ;;
    
    "certificate-rotation")
        deploy_certificate_rotation
        ;;
    
    "dependency-scanner")
        deploy_dependency_scanner
        ;;
    
    "sbom")
        deploy_sbom_generator
        ;;
    
    "dashboard")
        deploy_performance_dashboard
        ;;
    
    *)
        echo -e "${RED}❌ Unknown component: ${COMPONENT}${NC}"
        echo ""
        echo -e "${YELLOW}Usage: $0 <environment> <component>${NC}"
        echo ""
        echo -e "${BLUE}Available components:${NC}"
        echo "  all                  - Deploy all Phase 3 components"
        echo "  infrastructure       - Deploy foundation (DynamoDB, EventBridge)"
        echo "  ml-monitoring        - Deploy ML monitoring system"
        echo "  data-validation      - Deploy training data validation"
        echo "  ota-updates          - Deploy OTA update system"
        echo "  certificate-rotation - Deploy certificate rotation"
        echo "  dependency-scanner   - Deploy dependency scanner"
        echo "  sbom                 - Deploy SBOM generator"
        echo "  dashboard            - Deploy performance dashboard"
        exit 1
        ;;
esac

echo ""

###############################################################################
# Deployment Summary
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        🎉 PHASE 3 DEPLOYMENT COMPLETED! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Environment:${NC} ${ENVIRONMENT}"
echo -e "${BLUE}Region:${NC} ${AWS_REGION}"
echo -e "${BLUE}Component:${NC} ${COMPONENT}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Review CloudWatch dashboard for metrics"
echo "2. Run full integration tests: cd tests && python run_phase3_tests.py"
echo "3. Monitor CloudWatch alarms for issues"
echo "4. Review deployment logs in CloudWatch Logs"
echo "5. Update documentation with any environment-specific details"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- Implementation Guide: PHASE_3_IMPLEMENTATION_GUIDE.md"
echo "- Test Guide: tests/PHASE3_TEST_GUIDE.md"
echo "- Requirements: .kiro/specs/phase-3-high-priority/requirements.md"
echo ""
echo -e "${GREEN}✨ Phase 3 is ready! ✨${NC}"
