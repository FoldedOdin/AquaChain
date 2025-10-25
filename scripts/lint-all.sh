#!/bin/bash
# Comprehensive linting script for the entire AquaChain project
# Runs ESLint for frontend and Pylint for Lambda functions

set -e

echo "🚀 Running comprehensive code quality checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# ============================================
# Frontend Linting
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📱 Frontend Code Quality Checks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -d "frontend" ]; then
    cd frontend
    
    echo "🔍 Running ESLint..."
    if npm run lint 2>&1; then
        echo -e "${GREEN}✅ ESLint passed${NC}"
    else
        echo -e "${RED}❌ ESLint failed${NC}"
        OVERALL_STATUS=1
    fi
    
    echo ""
    echo "💅 Checking code formatting..."
    if npm run format:check 2>&1; then
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    else
        echo -e "${YELLOW}⚠️  Code formatting issues found. Run 'npm run format' to fix.${NC}"
        OVERALL_STATUS=1
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  Frontend directory not found${NC}"
fi

echo ""

# ============================================
# Backend Linting
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⚙️  Backend Code Quality Checks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if pylint is installed
if ! command -v pylint &> /dev/null; then
    echo -e "${YELLOW}⚠️  Pylint not found. Installing...${NC}"
    pip install pylint
fi

# Run Python linting
if [ -f "scripts/lint-python.sh" ]; then
    bash scripts/lint-python.sh
    if [ $? -ne 0 ]; then
        OVERALL_STATUS=1
    fi
else
    echo -e "${YELLOW}⚠️  Python linting script not found${NC}"
fi

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ All code quality checks passed!${NC}"
    echo -e "${GREEN}🎉 Your code meets AquaChain quality standards${NC}"
else
    echo -e "${RED}❌ Some code quality checks failed${NC}"
    echo -e "${YELLOW}📝 Please fix the issues above before committing${NC}"
fi

echo ""

exit $OVERALL_STATUS
