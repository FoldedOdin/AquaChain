# AquaChain Comprehensive System Test Runner (PowerShell)
# Runs the comprehensive test suite and opens the HTML report

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = './reports'
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AquaChain Comprehensive System Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green

# Check required Python packages
Write-Host "Checking required packages..." -ForegroundColor Yellow
$requiredPackages = @('boto3', 'requests')
foreach ($package in $requiredPackages) {
    python -c "import $package" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        pip install $package
    }
}
Write-Host "✓ All required packages available" -ForegroundColor Green

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "✓ Created output directory: $OutputDir" -ForegroundColor Green
}

# Run the test suite
Write-Host ""
Write-Host "Running comprehensive test suite..." -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host ""

python scripts/testing/comprehensive-system-test.py --environment $Environment --output-dir $OutputDir

# Check if reports were generated
$htmlReports = Get-ChildItem -Path $OutputDir -Filter "test-report-*.html" | Sort-Object LastWriteTime -Descending
if ($htmlReports.Count -gt 0) {
    $latestReport = $htmlReports[0].FullName
    Write-Host ""
    Write-Host "Opening HTML report..." -ForegroundColor Green
    Start-Process $latestReport
} else {
    Write-Host ""
    Write-Host "WARNING: No HTML report found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test execution complete!" -ForegroundColor Green
