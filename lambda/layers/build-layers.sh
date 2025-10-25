#!/bin/bash
# Build Lambda layers for deployment
# This script packages dependencies into the correct directory structure for Lambda layers

set -e

echo "Building Lambda layers..."

# Function to build a layer
build_layer() {
    local layer_name=$1
    local layer_dir="lambda/layers/${layer_name}"
    
    echo ""
    echo "Building ${layer_name} layer..."
    
    # Clean previous build
    if [ -d "${layer_dir}/python" ]; then
        echo "Cleaning previous build..."
        rm -rf "${layer_dir}/python"
    fi
    
    # Create python directory (required by Lambda)
    mkdir -p "${layer_dir}/python"
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r "${layer_dir}/requirements.txt" -t "${layer_dir}/python" --upgrade
    
    # Remove unnecessary files to reduce size
    echo "Cleaning up unnecessary files..."
    find "${layer_dir}/python" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find "${layer_dir}/python" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${layer_dir}/python" -name "*.pyc" -delete 2>/dev/null || true
    find "${layer_dir}/python" -name "*.pyo" -delete 2>/dev/null || true
    find "${layer_dir}/python" -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Calculate size
    local size=$(du -sh "${layer_dir}/python" | cut -f1)
    echo "Layer size: ${size}"
    
    echo "${layer_name} layer built successfully!"
}

# Build common layer
build_layer "common"

# Build ML layer
build_layer "ml"

echo ""
echo "All layers built successfully!"
echo ""
echo "Layer locations:"
echo "  - lambda/layers/common/python/"
echo "  - lambda/layers/ml/python/"
echo ""
echo "To deploy layers, run: cdk deploy LambdaLayersStack"
