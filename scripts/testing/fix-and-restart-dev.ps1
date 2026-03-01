# Fix API endpoint and restart dev server
Write-Host "Fixing API endpoint configuration..." -ForegroundColor Cyan

# Kill any running React dev server
Write-Host "Stopping existing dev server..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*node_modules*"} | Stop-Process -Force

Write-Host "✓ Dev server stopped" -ForegroundColor Green
Write-Host ""
Write-Host "Please restart the dev server manually:" -ForegroundColor Cyan
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm start" -ForegroundColor White
Write-Host ""
Write-Host "The app will now use the correct AWS API endpoint from .env.local" -ForegroundColor Green
