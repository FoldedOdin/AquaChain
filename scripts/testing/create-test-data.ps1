# Create Test Data for AquaChain Dashboard
# Populates DynamoDB with realistic test devices and sensor readings

param(
    [string]$UserId = "51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0",
    [string]$UserEmail = "karthikkpradeep123@gmail.com",
    [string]$Region = "ap-south-1",
    [int]$DeviceCount = 3,
    [int]$ReadingsPerDevice = 20
)

Write-Host "=== Creating Test Data for AquaChain ===" -ForegroundColor Cyan
Write-Host "User ID: $UserId" -ForegroundColor White
Write-Host "Devices: $DeviceCount" -ForegroundColor White
Write-Host "Readings per device: $ReadingsPerDevice" -ForegroundColor White
Write-Host ""

$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
$devicesCreated = 0
$readingsCreated = 0
$alertsCreated = 0

# Device locations and names
$deviceData = @(
    @{Name="Kitchen Tap"; Location="Kitchen"; Status="active"},
    @{Name="Bathroom Sink"; Location="Bathroom"; Status="active"},
    @{Name="Garden Hose"; Location="Garden"; Status="active"}
)

Write-Host "Step 1: Creating Devices..." -ForegroundColor Yellow

for ($i = 0; $i -lt [Math]::Min($DeviceCount, $deviceData.Count); $i++) {
    $device = $deviceData[$i]
    $deviceId = "DEV-TEST-$(Get-Random -Minimum 1000 -Maximum 9999)"
    
    $deviceItem = @"
{
    "deviceId": {"S": "$deviceId"},
    "userId": {"S": "$UserId"},
    "deviceName": {"S": "$($device.Name)"},
    "location": {"S": "$($device.Location)"},
    "status": {"S": "$($device.Status)"},
    "deviceType": {"S": "ESP32-WROOM-32"},
    "firmwareVersion": {"S": "1.2.0"},
    "lastSeen": {"S": "$timestamp"},
    "createdAt": {"S": "$timestamp"},
    "updatedAt": {"S": "$timestamp"},
    "isOnline": {"BOOL": true}
}
"@

    try {
        aws dynamodb put-item `
            --table-name "AquaChain-Devices" `
            --item $deviceItem `
            --region $Region `
            2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Created device: $($device.Name) ($deviceId)" -ForegroundColor Green
            $devicesCreated++
            
            # Create readings for this device
            Write-Host "    Creating $ReadingsPerDevice readings..." -ForegroundColor Gray
            
            for ($j = 0; $j -lt $ReadingsPerDevice; $j++) {
                # Generate realistic sensor data
                $hoursAgo = $ReadingsPerDevice - $j
                $readingTime = (Get-Date).AddHours(-$hoursAgo).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
                $month = (Get-Date).AddHours(-$hoursAgo).ToString("yyyy-MM")
                
                # Realistic water quality parameters
                $ph = [Math]::Round((Get-Random -Minimum 65 -Maximum 85) / 10.0, 2)
                $turbidity = [Math]::Round((Get-Random -Minimum 1 -Maximum 5), 2)
                $tds = Get-Random -Minimum 50 -Maximum 300
                $temperature = [Math]::Round((Get-Random -Minimum 18 -Maximum 28), 1)
                
                # Calculate quality score (0-100)
                $qualityScore = 100
                if ($ph -lt 6.5 -or $ph -gt 8.5) { $qualityScore -= 20 }
                if ($turbidity -gt 5) { $qualityScore -= 15 }
                if ($tds -gt 500) { $qualityScore -= 15 }
                $qualityScore = [Math]::Max(0, $qualityScore)
                
                # Determine quality status
                $qualityStatus = "excellent"
                if ($qualityScore -lt 90) { $qualityStatus = "good" }
                if ($qualityScore -lt 70) { $qualityStatus = "fair" }
                if ($qualityScore -lt 50) { $qualityStatus = "poor" }
                
                $readingItem = @"
{
    "deviceId_month": {"S": "${deviceId}_${month}"},
    "timestamp": {"S": "$readingTime"},
    "deviceId": {"S": "$deviceId"},
    "pH": {"N": "$ph"},
    "turbidity": {"N": "$turbidity"},
    "tds": {"N": "$tds"},
    "temperature": {"N": "$temperature"},
    "qualityScore": {"N": "$qualityScore"},
    "qualityStatus": {"S": "$qualityStatus"},
    "metric_type": {"S": "water_quality"},
    "createdAt": {"S": "$readingTime"}
}
"@

                aws dynamodb put-item `
                    --table-name "AquaChain-Readings" `
                    --item $readingItem `
                    --region $Region `
                    2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    $readingsCreated++
                }
            }
            
            Write-Host "    ✓ Created $ReadingsPerDevice readings" -ForegroundColor Green
            
            # Create an alert if quality is poor
            if ($qualityScore -lt 70) {
                $alertId = "ALERT-$(Get-Random -Minimum 10000 -Maximum 99999)"
                $alertItem = @"
{
    "alertId": {"S": "$alertId"},
    "deviceId": {"S": "$deviceId"},
    "userId": {"S": "$UserId"},
    "alertType": {"S": "water_quality"},
    "severity": {"S": "warning"},
    "status": {"S": "active"},
    "message": {"S": "Water quality below acceptable threshold"},
    "details": {"S": "Quality score: $qualityScore. pH: $ph, Turbidity: $turbidity NTU"},
    "timestamp": {"S": "$timestamp"},
    "createdAt": {"S": "$timestamp"}
}
"@

                aws dynamodb put-item `
                    --table-name "AquaChain-Alerts" `
                    --item $alertItem `
                    --region $Region `
                    2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ Created alert for low quality" -ForegroundColor Yellow
                    $alertsCreated++
                }
            }
            
        } else {
            Write-Host "  ✗ Failed to create device: $($device.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ Error creating device: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Devices created: $devicesCreated" -ForegroundColor Green
Write-Host "Readings created: $readingsCreated" -ForegroundColor Green
Write-Host "Alerts created: $alertsCreated" -ForegroundColor $(if ($alertsCreated -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

if ($devicesCreated -gt 0) {
    Write-Host "✓ Test data created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Refresh your dashboard: http://localhost:3000" -ForegroundColor White
    Write-Host "2. You should now see:" -ForegroundColor White
    Write-Host "   - $devicesCreated devices" -ForegroundColor Gray
    Write-Host "   - $readingsCreated sensor readings" -ForegroundColor Gray
    Write-Host "   - $alertsCreated active alerts" -ForegroundColor Gray
    Write-Host "   - Dashboard statistics" -ForegroundColor Gray
    Write-Host "   - Water quality charts" -ForegroundColor Gray
} else {
    Write-Host "⚠ No test data was created. Check errors above." -ForegroundColor Yellow
}

Write-Host ""
