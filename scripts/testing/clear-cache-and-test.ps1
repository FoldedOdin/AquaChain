# Clear Python cache and run comprehensive test
# This ensures the latest code changes are used

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev'
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Clear Cache and Run Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clear Python cache
Write-Host "Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "✓ Cache cleared" -ForegroundColor Green

Write-Host ""
Write-Host "Running comprehensive test suite..." -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host ""

# Run the test
python scripts/testing/comprehensive-system-test.py --environment $Environment --output-dir ./reports

# Check if reports were generated
$htmlReports = Get-ChildItem -Path ./reports -Filter "test-report-*.html" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($htmlReports.Count -gt 0) {
    $latestReport = $htmlReports[0].FullName
    Write-Host ""
    Write-Host "Opening HTML report..." -ForegroundColor Green
    Start-Process $latestReport
} else {
    Write-Host ""
    Write-Host "No HTML report found (test may have failed)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test execution complete!" -ForegroundColor Green
