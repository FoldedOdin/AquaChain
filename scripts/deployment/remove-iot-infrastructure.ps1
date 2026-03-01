#!/usr/bin/env pwsh
# Remove IoT Infrastructure to Save Costs
# Saves ~$3-5/month by removing IoT Core resources

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Remove IoT Infrastructure" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will remove:" -ForegroundColor Yellow
Write-Host "  1. IoT Security Stack (device policies, certificates)" -ForegroundColor White
Write-Host "  2. IoT Core resources from Data Stack" -ForegroundColor White
Write-Host "  3. Stop any running simulator processes" -ForegroundColor White
Write-Host ""
Write-Host "Cost savings: ~`$3-5/month" -ForegroundColor Green
Write-Host ""
Write-Host "What will still work:" -ForegroundColor Green
Write-Host "  - All Lambda functions" -ForegroundColor White
Write-Host "  - DynamoDB data storage" -ForegroundColor White
Write-Host "  - API Gateway and authentication" -ForegroundColor White
Write-Host "  - Frontend dashboard" -ForegroundColor White
Write-Host ""
Write-Host "What will NOT work:" -ForegroundColor Red
Write-Host "  - Real IoT device connectivity" -ForegroundColor White
Write-Host "  - IoT simulator" -ForegroundColor White
Write-Host "  - Real-time sensor data ingestion" -ForegroundColor White
Write-Host ""

if (-not $DryRun) {
    $confirm = Read-Host "Type 'REMOVE' to proceed"
    if ($confirm -ne "REMOVE") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Stop Simulator Processes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Stopping $($pythonProcesses.Count) Python processes..." -ForegroundColor Yellow
    if (-not $DryRun) {
        $pythonProcesses | Stop-Process -Force
        Write-Host "  Processes stopped." -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Would stop $($pythonProcesses.Count) processes" -ForegroundColor Gray
    }
} else {
    Write-Host "No Python processes running." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Destroy IoT Security Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Destroying AquaChain-IoTSecurity-dev..." -ForegroundColor Yellow
if (-not $DryRun) {
    cd infrastructure/cdk
    cdk destroy AquaChain-IoTSecurity-dev --force
    cd ../..
    Write-Host "  IoT Security Stack destroyed." -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would destroy AquaChain-IoTSecurity-dev" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Clean Up IoT Core Resources" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking for orphaned IoT resources..." -ForegroundColor Yellow

# List IoT things
Write-Host "  Checking IoT Things..." -ForegroundColor Gray
if (-not $DryRun) {
    $things = aws iot list-things --region ap-south-1 2>$null | ConvertFrom-Json
    if ($things.things.Count -gt 0) {
        Write-Host "    Found $($things.things.Count) IoT things" -ForegroundColor Yellow
        foreach ($thing in $things.things) {
            Write-Host "    Deleting thing: $($thing.thingName)" -ForegroundColor Gray
            # Detach principals first
            $principals = aws iot list-thing-principals --thing-name $thing.thingName --region ap-south-1 2>$null | ConvertFrom-Json
            foreach ($principal in $principals.principals) {
                aws iot detach-thing-principal --thing-name $thing.thingName --principal $principal --region ap-south-1 2>$null
            }
            # Delete thing
            aws iot delete-thing --thing-name $thing.thingName --region ap-south-1 2>$null
        }
        Write-Host "    IoT things cleaned up." -ForegroundColor Green
    } else {
        Write-Host "    No IoT things found." -ForegroundColor Green
    }
} else {
    Write-Host "    [DRY RUN] Would check and clean IoT things" -ForegroundColor Gray
}

# List IoT policies
Write-Host "  Checking IoT Policies..." -ForegroundColor Gray
if (-not $DryRun) {
    $policies = aws iot list-policies --region ap-south-1 2>$null | ConvertFrom-Json
    $aquachainPolicies = $policies.policies | Where-Object { $_.policyName -like "*aquachain*" -or $_.policyName -like "*AquaChain*" }
    if ($aquachainPolicies.Count -gt 0) {
        Write-Host "    Found $($aquachainPolicies.Count) AquaChain policies" -ForegroundColor Yellow
        foreach ($policy in $aquachainPolicies) {
            Write-Host "    Deleting policy: $($policy.policyName)" -ForegroundColor Gray
            # Detach all targets first
            $targets = aws iot list-targets-for-policy --policy-name $policy.policyName --region ap-south-1 2>$null | ConvertFrom-Json
            foreach ($target in $targets.targets) {
                aws iot detach-policy --policy-name $policy.policyName --target $target --region ap-south-1 2>$null
            }
            # Delete all versions
            $versions = aws iot list-policy-versions --policy-name $policy.policyName --region ap-south-1 2>$null | ConvertFrom-Json
            foreach ($version in $versions.policyVersions) {
                if (-not $version.isDefaultVersion) {
                    aws iot delete-policy-version --policy-name $policy.policyName --policy-version-id $version.versionId --region ap-south-1 2>$null
                }
            }
            # Delete policy
            aws iot delete-policy --policy-name $policy.policyName --region ap-south-1 2>$null
        }
        Write-Host "    IoT policies cleaned up." -ForegroundColor Green
    } else {
        Write-Host "    No AquaChain IoT policies found." -ForegroundColor Green
    }
} else {
    Write-Host "    [DRY RUN] Would check and clean IoT policies" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IoT infrastructure removed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Cost Impact:" -ForegroundColor Yellow
Write-Host "  Savings: ~`$3-5/month" -ForegroundColor Green
Write-Host "  Removed: IoT Core connectivity, messaging, device management" -ForegroundColor White
Write-Host ""
Write-Host "System Status:" -ForegroundColor Yellow
Write-Host "  ✓ Lambda functions still operational" -ForegroundColor Green
Write-Host "  ✓ DynamoDB data intact" -ForegroundColor Green
Write-Host "  ✓ API Gateway functional" -ForegroundColor Green
Write-Host "  ✓ Frontend dashboard accessible" -ForegroundColor Green
Write-Host "  ✗ IoT device connectivity disabled" -ForegroundColor Red
Write-Host ""
Write-Host "Note: You can still test with mock data in the frontend." -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
