# Check GSI Status for All AquaChain Tables
# Verifies that all Global Secondary Indexes are ACTIVE

Write-Host "=== Checking GSI Status for AquaChain Tables ===" -ForegroundColor Cyan
Write-Host ""

$region = "ap-south-1"
$allActive = $true

# Expected GSIs per table
$expectedGSIs = @{
    "AquaChain-Readings" = @("DeviceIndex", "device_id-metric_type-index")
    "AquaChain-Ledger" = @()
    "AquaChain-Sequence" = @()
    "AquaChain-Users" = @("EmailIndex", "RoleIndex")
    "AquaChain-ServiceRequests" = @("TechnicianIndex", "StatusIndex")
    "AquaChain-Devices" = @("UserIndex", "StatusIndex")
    "AquaChain-AuditLogs" = @("ActionIndex", "ResourceIndex")
    "AquaChain-SystemConfig" = @()
}

foreach ($tableName in $expectedGSIs.Keys) {
    Write-Host "Table: $tableName" -ForegroundColor Yellow
    
    # Check if table exists
    $tableInfo = aws dynamodb describe-table --table-name $tableName --region $region 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Table not found" -ForegroundColor Red
        $allActive = $false
        Write-Host ""
        continue
    }
    
    $table = $tableInfo | ConvertFrom-Json
    $tableStatus = $table.Table.TableStatus
    
    Write-Host "  Table Status: $tableStatus" -ForegroundColor $(if ($tableStatus -eq "ACTIVE") { "Green" } else { "Yellow" })
    
    # Check GSIs
    $expectedIndexes = $expectedGSIs[$tableName]
    
    if ($expectedIndexes.Count -eq 0) {
        Write-Host "  No GSIs expected" -ForegroundColor Gray
    } else {
        $actualGSIs = $table.Table.GlobalSecondaryIndexes
        
        if ($null -eq $actualGSIs) {
            Write-Host "  ✗ No GSIs found (expected $($expectedIndexes.Count))" -ForegroundColor Red
            $allActive = $false
        } else {
            Write-Host "  GSIs ($($actualGSIs.Count)/$($expectedIndexes.Count)):" -ForegroundColor Cyan
            
            foreach ($expectedIndex in $expectedIndexes) {
                $gsi = $actualGSIs | Where-Object { $_.IndexName -eq $expectedIndex }
                
                if ($null -eq $gsi) {
                    Write-Host "    ✗ $expectedIndex - NOT FOUND" -ForegroundColor Red
                    $allActive = $false
                } else {
                    $status = $gsi.IndexStatus
                    $color = switch ($status) {
                        "ACTIVE" { "Green" }
                        "CREATING" { "Yellow" }
                        "UPDATING" { "Yellow" }
                        "DELETING" { "Red" }
                        default { "Red" }
                    }
                    
                    $symbol = if ($status -eq "ACTIVE") { "✓" } else { "⏳" }
                    Write-Host "    $symbol $expectedIndex - $status" -ForegroundColor $color
                    
                    if ($status -ne "ACTIVE") {
                        $allActive = $false
                    }
                }
            }
        }
    }
    
    Write-Host ""
}

Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ""

if ($allActive) {
    Write-Host "✓ All tables and GSIs are ACTIVE" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your application is ready to use!" -ForegroundColor Green
    Write-Host "Start your frontend: cd frontend && npm start" -ForegroundColor White
} else {
    Write-Host "⚠ Some tables or GSIs are not ready" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  - If GSIs are CREATING: Wait 2-5 minutes and run this script again" -ForegroundColor White
    Write-Host "  - If tables are missing: Run .\scripts\deployment\create-dynamodb-tables-manually.ps1" -ForegroundColor White
    Write-Host "  - If GSIs are missing: They may have failed to create, check AWS Console" -ForegroundColor White
}

Write-Host ""
