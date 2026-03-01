# Update phone number for Karthik K Pradeep user
# This bypasses the OTP system for testing purposes

$userId = "karthikkpradeep123@gmail.com"
$phone = "+918547613649"

Write-Host "Updating phone number for user: $userId" -ForegroundColor Cyan
Write-Host "New phone number: $phone" -ForegroundColor Cyan
Write-Host ""

# Update the user's phone number in DynamoDB
aws dynamodb update-item `
  --table-name AquaChain-Users `
  --key "{\`"userId\`": {\`"S\`": \`"$userId\`"}}" `
  --update-expression "SET #prof.#ph = :phone" `
  --expression-attribute-names "{\`"#prof\`": \`"profile\`", \`"#ph\`": \`"phone\`"}" `
  --expression-attribute-values "{:\`"phone\`": {\`"S\`": \`"$phone\`"}}" `
  --region ap-south-1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Phone number updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "User can now place orders without OTP verification issues." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Failed to update phone number" -ForegroundColor Red
    Write-Host "Check the error message above for details." -ForegroundColor Red
}
