# Build Lambda layers for deployment (PowerShell version)
# This script packages dependencies into the correct directory structure for Lambda layers

$ErrorActionPreference = "Stop"

Write-Host "Building Lambda layers..." -ForegroundColor Green

function Build-Layer {
    param(
        [string]$LayerName
    )
    
    $LayerDir = "lambda\layers\$LayerName"
    
    Write-Host ""
    Write-Host "Building $LayerName layer..." -ForegroundColor Cyan
    
    # Clean previous build
    if (Test-Path "$LayerDir\python") {
        Write-Host "Cleaning previous build..."
        Remove-Item -Recurse -Force "$LayerDir\python"
    }
    
    # Create python directory (required by Lambda)
    New-Item -ItemType Directory -Force -Path "$LayerDir\python" | Out-Null
    
    # Install dependencies
    Write-Host "Installing dependencies..."
    pip install -r "$LayerDir\requirements.txt" -t "$LayerDir\python" --upgrade
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies for $LayerName layer"
    }
    
    # Remove unnecessary files to reduce size
    Write-Host "Cleaning up unnecessary files..."
    Get-ChildItem -Path "$LayerDir\python" -Directory -Recurse -Filter "tests" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$LayerDir\python" -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$LayerDir\python" -File -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$LayerDir\python" -File -Recurse -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$LayerDir\python" -Directory -Recurse -Filter "*.dist-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Calculate size
    $Size = (Get-ChildItem -Path "$LayerDir\python" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "Layer size: $([math]::Round($Size, 2)) MB"
    
    Write-Host "$LayerName layer built successfully!" -ForegroundColor Green
}

# Build common layer
Build-Layer -LayerName "common"

# Build ML layer
Build-Layer -LayerName "ml"

Write-Host ""
Write-Host "All layers built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Layer locations:"
Write-Host "  - lambda\layers\common\python\"
Write-Host "  - lambda\layers\ml\python\"
Write-Host ""
Write-Host "To deploy layers, run: cdk deploy LambdaLayersStack"
