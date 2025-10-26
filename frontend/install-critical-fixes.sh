#!/bin/bash

# AquaChain Frontend - Critical Fixes Installation Script
# This script installs dependencies and verifies the fixes

echo "================================================"
echo "AquaChain Frontend - Critical Fixes Installation"
echo "================================================"
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "Please run this script from the frontend directory"
    exit 1
fi

echo "✅ Found package.json"
echo ""

# Install React Query dependencies
echo "📦 Installing React Query dependencies..."
npm install @tanstack/react-query@^5.62.11 @tanstack/react-query-devtools@^5.62.11

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Run TypeScript type check
echo "🔍 Running TypeScript type check..."
npx tsc --noEmit

if [ $? -ne 0 ]; then
    echo "⚠️  TypeScript errors found (may be expected)"
else
    echo "✅ TypeScript check passed"
fi
echo ""

# Run ESLint
echo "🔍 Running ESLint..."
npm run lint

if [ $? -ne 0 ]; then
    echo "⚠️  ESLint warnings found (may be expected)"
else
    echo "✅ ESLint check passed"
fi
echo ""

# Attempt build
echo "🏗️  Attempting production build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    echo ""
    echo "Common issues:"
    echo "1. Missing component files"
    echo "2. TypeScript errors"
    echo "3. Import path issues"
    echo ""
    echo "Please check the error messages above and fix any issues."
    exit 1
fi

echo "✅ Build completed successfully!"
echo ""

# Check bundle size
echo "📊 Checking bundle size..."
if [ -d "build/static/js" ]; then
    echo "JavaScript bundles:"
    ls -lh build/static/js/*.js | awk '{print "  " $9 " - " $5}'
    echo ""
    
    # Calculate total size
    total_size=$(du -sh build/static/js | awk '{print $1}')
    echo "Total JS size: $total_size"
fi
echo ""

echo "================================================"
echo "✅ Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review the build output above"
echo "2. Test the application: npm start"
echo "3. Open React Query DevTools in browser"
echo "4. Verify dashboard performance"
echo ""
echo "Documentation:"
echo "- CRITICAL_FIXES_IMPLEMENTATION.md"
echo "- FRONTEND_AUDIT_REPORT.md"
echo ""
