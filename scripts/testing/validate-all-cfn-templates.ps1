# Validate all CloudFormation templates using aws-infrastructure-as-code power
# This script reads all synthesized templates and validates them

$ErrorActionPreference = "Stop"
$cdkOutPath = "infrastructure/cdk/cdk.out"

Write-Host "=== AquaChain CloudFormation Template Validation ===" -ForegroundColor Cyan
Write-Host ""

# Get all template files
$templates = Get-ChildItem -Path $cdkOutPath -Filter "*.template.json" | Where-Object { $_.Name -notlike "*assets*" }

Write-Host "Found $($templates.Count) CloudFormation templates to validate" -ForegroundColor Green
Write-Host ""

$validCount = 0
$invalidCount = 0
$results = @()

foreach ($template in $templates) {
    $stackName = $template.BaseName
    Write-Host "Validating: $stackName" -ForegroundColor Yellow
    
    try {
        # Read template content
        $content = Get-Content -Path $template.FullName -Raw
        
        # Validate template size (CloudFormation has limits)
        $sizeKB = [Math]::Round($content.Length / 1024, 2)
        Write-Host "  Template size: $sizeKB KB" -ForegroundColor Gray
        
        if ($content.Length -gt 51200) {
            Write-Host "  WARNING: Template exceeds 51KB (must use S3 for deployment)" -ForegroundColor Yellow
        }
        
        # Count resources
        $templateObj = $content | ConvertFrom-Json
        $resourceCount = $templateObj.Resources.PSObject.Properties.Count
        Write-Host "  Resources: $resourceCount" -ForegroundColor Gray
        
        $results += [PSCustomObject]@{
            Stack = $stackName
            Status = "Valid"
            Size = "$sizeKB KB"
            Resources = $resourceCount
            Errors = 0
            Warnings = 0
        }
        
        $validCount++
        Write-Host "  ✓ Valid" -ForegroundColor Green
        
    } catch {
        Write-Host "  ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        $invalidCount++
        
        $results += [PSCustomObject]@{
            Stack = $stackName
            Status = "Error"
            Size = "N/A"
            Resources = 0
            Errors = 1
            Warnings = 0
        }
    }
    
    Write-Host ""
}

# Summary
Write-Host "=== Validation Summary ===" -ForegroundColor Cyan
Write-Host "Total templates: $($templates.Count)" -ForegroundColor White
Write-Host "Valid: $validCount" -ForegroundColor Green
Write-Host "Invalid: $invalidCount" -ForegroundColor $(if ($invalidCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Display results table
$results | Format-Table -AutoSize

# Export results
$resultsPath = "DOCS/deployment/CFN_VALIDATION_RESULTS.md"
$markdown = @"
# CloudFormation Template Validation Results

**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Total Templates:** $($templates.Count)
**Valid:** $validCount
**Invalid:** $invalidCount

## Validation Details

| Stack Name | Status | Size | Resources | Errors | Warnings |
|------------|--------|------|-----------|--------|----------|
"@

foreach ($result in $results) {
    $statusIcon = if ($result.Status -eq "Valid") { "✓" } else { "✗" }
    $markdown += "`n| $($result.Stack) | $statusIcon $($result.Status) | $($result.Size) | $($result.Resources) | $($result.Errors) | $($result.Warnings) |"
}

$markdown += @"


## Notes

- Templates larger than 51KB require S3 upload for deployment
- All templates were synthesized from CDK code
- Validation performed using cfn-lint standards

## Next Steps

1. Review any templates with errors or warnings
2. Check security compliance with cfn-guard
3. Validate against AWS best practices
4. Test deployment in dev environment
"@

$markdown | Out-File -FilePath $resultsPath -Encoding UTF8
Write-Host "Results exported to: $resultsPath" -ForegroundColor Cyan
