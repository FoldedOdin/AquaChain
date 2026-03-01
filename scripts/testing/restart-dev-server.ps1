# Restart Development Server with Fresh Environment
# This ensures .env.local is loaded correctly

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restarting Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill any running node processes
Write-Host "Step 1: Stopping any running dev servers..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "  Found $($nodeProcesses.Count) node process(es)" -ForegroundColor Gray
    Write-Host "  Stopping them..." -ForegroundColor Gray
    $nodeProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Stopped" -ForegroundColor Green
} else {
    Write-Host "  No running node processes found" -ForegroundColor Gray
}
Write-Host ""

# Step 2: Clear cache
Write-Host "Step 2: Clearing node cache..." -ForegroundColor Yellow
$cachePath = "frontend/node_modules/.cache"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force
    Write-Host "  ✓ Cache cleared" -ForegroundColor Green
} else {
    Write-Host "  No cache to clear" -ForegroundColor Gray
}
Write-Host ""

# Step 3: Verify .env.local
Write-Host "Step 3: Verifying .env.local..." -ForegroundColor Yellow
$envLocalPath = "frontend/.env.local"
if (Test-Path $envLocalPath) {
    Write-Host "  ✓ .env.local found" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Key settings:" -ForegroundColor Cyan
    
    $content = Get-Content $envLocalPath
    $region = $content | Select-String "REACT_APP_AWS_REGION=" | Select-Object -First 1
    $userPool = $content | Select-String "REACT_APP_USER_POOL_ID=" | Select-Object -First 1
    $identityPool = $content | Select-String "REACT_APP_IDENTITY_POOL_ID=" | Select-Object -First 1
    
    if ($region) {
        Write-Host "    $region" -ForegroundColor White
    }
    if ($userPool) {
        Write-Host "    $userPool" -ForegroundColor White
    }
    if ($identityPool) {
        Write-Host "    WARNING: Identity Pool ID is set!" -ForegroundColor Red
        Write-Host "    $identityPool" -ForegroundColor Red
    } else {
        Write-Host "    ✓ No Identity Pool ID (correct)" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ .env.local NOT FOUND!" -ForegroundColor Red
    Write-Host "  Please create it first" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Check .env.development
Write-Host "Step 4: Checking .env.development..." -ForegroundColor Yellow
$envDevPath = "frontend/.env.development"
if (Test-Path $envDevPath) {
    $devContent = Get-Content $envDevPath
    $devIdentityPool = $devContent | Select-String "^REACT_APP_IDENTITY_POOL_ID=" | Select-Object -First 1
    
    if ($devIdentityPool) {
        Write-Host "  ⚠ WARNING: .env.development has uncommented Identity Pool ID!" -ForegroundColor Red
        Write-Host "    $devIdentityPool" -ForegroundColor Red
        Write-Host "    This will override .env.local!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Fix: Comment it out with #" -ForegroundColor Yellow
        Write-Host ""
        $response = Read-Host "  Do you want me to comment it out now? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            $newContent = $devContent -replace '^REACT_APP_IDENTITY_POOL_ID=', '# REACT_APP_IDENTITY_POOL_ID='
            $newContent | Set-Content $envDevPath
            Write-Host "  ✓ Fixed!" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✓ No active Identity Pool ID in .env.development" -ForegroundColor Green
    }
}
Write-Host ""

# Step 5: Start dev server
Write-Host "Step 5: Starting dev server..." -ForegroundColor Yellow
Write-Host "  Opening new terminal window..." -ForegroundColor Gray
Write-Host ""

# Start in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD/frontend'; Write-Host 'Starting React dev server...' -ForegroundColor Cyan; npm start"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dev server starting in new window..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Wait for server to start (usually 10-30 seconds)" -ForegroundColor White
Write-Host "2. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "3. Press F12 to open DevTools" -ForegroundColor White
Write-Host "4. Go to: Application > Storage > Clear site data" -ForegroundColor White
Write-Host "5. Click 'Clear site data' button" -ForegroundColor White
Write-Host "6. Refresh the page (F5)" -ForegroundColor White
Write-Host "7. Try logging in" -ForegroundColor White
Write-Host ""

Write-Host "WHAT TO LOOK FOR:" -ForegroundColor Yellow
Write-Host "✓ Console should show: ap-south-1 (NOT us-east-1)" -ForegroundColor Green
Write-Host "✓ No Identity Pool errors" -ForegroundColor Green
Write-Host "✓ Token stored in localStorage after login" -ForegroundColor Green
Write-Host ""

Write-Host "If you still see us-east-1 errors:" -ForegroundColor Red
Write-Host "- Make sure you cleared browser storage" -ForegroundColor White
Write-Host "- Check console: console.log(process.env.REACT_APP_AWS_REGION)" -ForegroundColor White
Write-Host "- Should show: ap-south-1" -ForegroundColor White
Write-Host ""
