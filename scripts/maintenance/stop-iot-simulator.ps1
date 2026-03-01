#!/usr/bin/env pwsh
# Stop all IoT simulator processes

Write-Host "Stopping IoT Simulator processes..." -ForegroundColor Yellow

# Find and stop all python processes (simulator related)
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python processes" -ForegroundColor Cyan
    
    foreach ($proc in $pythonProcesses) {
        Write-Host "  Stopping PID $($proc.Id)..." -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host ""
    Write-Host "All Python processes stopped." -ForegroundColor Green
    Write-Host "IoT simulator is no longer running." -ForegroundColor Green
    Write-Host ""
    Write-Host "Cost savings: ~`$3-5/month" -ForegroundColor Green
} else {
    Write-Host "No Python processes found." -ForegroundColor Yellow
}
