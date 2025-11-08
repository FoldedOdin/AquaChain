# AquaChain Frontend - Critical Fixes Installation Script (PowerShell)
# This script installs dependencies and verifies the fixes

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "AquaChain Frontend - Critical Fixes Installation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the frontend directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: package.json not found" -ForegroundColor Red
    Write-Host "Please run this script from the frontend directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found package.json" -ForegroundColor Green
Write-Host ""

# Install React Query dependencies
Write-Host "📦 Installing React Query dependencies..." -ForegroundColor Cyan
npm install @tanstack/react-query@^5.62.11 @tanstack/react-query-devtools@^5.62.11

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Run TypeScript type check
Write-Host "🔍 Running TypeScript type check..." -ForegroundColor Cyan
npx tsc --noEmit

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  TypeScript errors found (may be expected)" -ForegroundColor Yellow
} else {
    Write-Host "✅ TypeScript check passed" -ForegroundColor Green
}
Write-Host ""

# Run ESLint
Write-Host "🔍 Running ESLint..." -ForegroundColor Cyan
npm run lint

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  ESLint warnings found (may be expected)" -ForegroundColor Yellow
} else {
    Write-Host "✅ ESLint check passed" -ForegroundColor Green
}
Write-Host ""

# Attempt build
Write-Host "🏗️  Attempting production build..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Missing component files"
    Write-Host "2. TypeScript errors"
    Write-Host "3. Import path issues"
    Write-Host ""
    Write-Host "Please check the error messages above and fix any issues."
    exit 1
}

Write-Host "✅ Build completed successfully!" -ForegroundColor Green
Write-Host ""

# Check bundle size
Write-Host "📊 Checking bundle size..." -ForegroundColor Cyan
if (Test-Path "build/static/js") {
    Write-Host "JavaScript bundles:" -ForegroundColor Cyan
    Get-ChildItem "build/static/js/*.js" | ForEach-Object {
        $size = "{0:N2} KB" -f ($_.Length / 1KB)
        Write-Host "  $($_.Name) - $size"
    }
    Write-Host ""
    
    # Calculate total size
    $totalSize = (Get-ChildItem "build/static/js" -Recurse | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = "{0:N2} MB" -f ($totalSize / 1MB)
    Write-Host "Total JS size: $totalSizeMB" -ForegroundColor Cyan
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the build output above"
Write-Host "2. Test the application: npm start"
Write-Host "3. Open React Query DevTools in browser"
Write-Host "4. Verify dashboard performance"
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "- CRITICAL_FIXES_IMPLEMENTATION.md"
Write-Host "- FRONTEND_AUDIT_REPORT.md"
Write-Host ""
