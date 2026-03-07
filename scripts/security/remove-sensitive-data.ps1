# Security Remediation Script
# This script helps remove sensitive data from the repository

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AquaChain Security Remediation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  WARNING: This script will modify files and git history" -ForegroundColor Yellow
Write-Host "⚠️  Make sure you have a backup before proceeding" -ForegroundColor Yellow
Write-Host ""

$continue = Read-Host "Do you want to continue? (yes/no)"
if ($continue -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Replacing API Gateway endpoint with environment variable..." -ForegroundColor Green

# Define the sensitive endpoint to replace
$sensitiveEndpoint = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$placeholder = '${process.env.REACT_APP_API_ENDPOINT || "https://YOUR-API-ID.execute-api.REGION.amazonaws.com/STAGE"}'

# Find all files containing the sensitive endpoint
$files = Get-ChildItem -Recurse -File -Include *.tsx,*.ts,*.js,*.ps1,*.bat,*.sh,*.md | 
    Where-Object { $_.FullName -notmatch "node_modules|\.git|package" } |
    Select-String -Pattern "vtqjfznspc\.execute-api" -List |
    Select-Object -ExpandProperty Path

Write-Host "Found $($files.Count) files containing the API endpoint" -ForegroundColor Yellow

foreach ($file in $files) {
    Write-Host "  Processing: $file" -ForegroundColor Gray
    
    # Read file content
    $content = Get-Content $file -Raw
    
    # Replace the endpoint based on file type
    if ($file -match "\.(tsx|ts|js)$") {
        # For TypeScript/JavaScript files
        $content = $content -replace [regex]::Escape($sensitiveEndpoint), '${process.env.REACT_APP_API_ENDPOINT}'
    }
    elseif ($file -match "\.ps1$") {
        # For PowerShell files
        $content = $content -replace [regex]::Escape($sensitiveEndpoint), '${env:API_ENDPOINT}'
    }
    elseif ($file -match "\.(bat|sh)$") {
        # For batch/shell files
        $content = $content -replace [regex]::Escape($sensitiveEndpoint), '${API_ENDPOINT}'
    }
    elseif ($file -match "\.md$") {
        # For markdown files
        $content = $content -replace [regex]::Escape($sensitiveEndpoint), 'https://YOUR-API-ID.execute-api.REGION.amazonaws.com/STAGE'
    }
    
    # Write back to file
    Set-Content -Path $file -Value $content -NoNewline
}

Write-Host "✅ API endpoint replaced in $($files.Count) files" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Replacing personal email with placeholder..." -ForegroundColor Green

$sensitiveEmail = "karthikpradep@gmail.com"
$emailPlaceholder = "test-user@example.com"

$emailFiles = Get-ChildItem -Recurse -File -Include *.ps1,*.sh,*.md | 
    Where-Object { $_.FullName -notmatch "node_modules|\.git" } |
    Select-String -Pattern $sensitiveEmail -List |
    Select-Object -ExpandProperty Path

Write-Host "Found $($emailFiles.Count) files containing the email" -ForegroundColor Yellow

foreach ($file in $emailFiles) {
    Write-Host "  Processing: $file" -ForegroundColor Gray
    $content = Get-Content $file -Raw
    $content = $content -replace [regex]::Escape($sensitiveEmail), $emailPlaceholder
    Set-Content -Path $file -Value $content -NoNewline
}

Write-Host "✅ Email replaced in $($emailFiles.Count) files" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Creating .env.example with required variables..." -ForegroundColor Green

$envExample = @"
# AquaChain Environment Variables

# API Configuration
REACT_APP_API_ENDPOINT=https://YOUR-API-ID.execute-api.REGION.amazonaws.com/STAGE
REACT_APP_WEBSOCKET_ENDPOINT=wss://YOUR-WS-ID.execute-api.REGION.amazonaws.com/STAGE

# AWS Configuration
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012

# Cognito Configuration
REACT_APP_USER_POOL_ID=YOUR-USER-POOL-ID
REACT_APP_USER_POOL_CLIENT_ID=YOUR-CLIENT-ID

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ML_INSIGHTS=true

# Environment
REACT_APP_ENV=development
"@

Set-Content -Path "frontend/.env.example" -Value $envExample

Write-Host "✅ Created frontend/.env.example" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Staging changes..." -ForegroundColor Green
git add -A

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remediation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the changes: git diff --staged" -ForegroundColor White
Write-Host "2. Commit the changes: git commit -m 'security: remove sensitive data from repository'" -ForegroundColor White
Write-Host "3. To remove from git history, use BFG Repo-Cleaner or git filter-repo" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Coordinate with team before rewriting git history!" -ForegroundColor Yellow
Write-Host ""
