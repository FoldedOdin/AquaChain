# Security Remediation Guide

## Overview

This guide provides step-by-step instructions to remove sensitive data from the AquaChain repository.

## Findings Summary

### 🔴 Critical: Exposed API Gateway Endpoint
- **Endpoint**: `vtqjfznspc.execute-api.ap-south-1.amazonaws.com`
- **Occurrences**: 50+ files
- **Risk**: Infrastructure details exposed

### 🟡 Medium: Personal Email
- **Email**: `karthikpradep@gmail.com`
- **Location**: `scripts/testing/debug-profile-502.ps1`
- **Risk**: PII exposure

## Quick Fix (Recommended)

Since the API Gateway endpoint is already deployed and public-facing, the immediate risk is low. However, best practice is to use environment variables.

### Option 1: Keep Current Commits, Fix Going Forward

This is the recommended approach as it doesn't rewrite history:

1. **Update all files to use environment variables**
2. **Commit the changes**
3. **Rotate the API Gateway endpoint** (optional, if concerned)

### Option 2: Rewrite Git History (Advanced)

⚠️ **WARNING**: This will rewrite git history and require force push. Coordinate with all team members first!

Use BFG Repo-Cleaner or git-filter-repo to remove sensitive data from history.

## Step-by-Step Remediation

### 1. Run the Automated Script

```powershell
# Run the remediation script
.\scripts\security\remove-sensitive-data.ps1
```

This script will:
- Replace API endpoints with environment variables
- Replace personal emails with placeholders
- Create `.env.example` files
- Stage all changes

### 2. Review Changes

```bash
git diff --staged
```

### 3. Commit Changes

```bash
git commit -m "security: remove sensitive data and use environment variables"
```

### 4. Update Environment Variables

Create a `.env` file (DO NOT COMMIT):

```bash
# Frontend
cd frontend
cp .env.example .env
# Edit .env with your actual values
```

### 5. (Optional) Rotate API Gateway

If you want to completely remove the exposed endpoint:

```bash
# Deploy new API Gateway stage
cd infrastructure/cdk
cdk deploy --all

# Update your .env files with new endpoint
```

## Manual Remediation (If Script Fails)

### Replace API Endpoint

**In TypeScript/JavaScript files:**
```typescript
// Before
const apiEndpoint = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

// After
const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'https://YOUR-API-ID.execute-api.REGION.amazonaws.com/STAGE';
```

**In PowerShell scripts:**
```powershell
# Before
$API_URL = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

# After
$API_URL = $env:API_ENDPOINT
if (-not $API_URL) {
    Write-Error "API_ENDPOINT environment variable not set"
    exit 1
}
```

**In Bash scripts:**
```bash
# Before
API_BASE="https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

# After
API_BASE="${API_ENDPOINT}"
if [ -z "$API_BASE" ]; then
    echo "Error: API_ENDPOINT environment variable not set"
    exit 1
fi
```

### Replace Email

```powershell
# In scripts/testing/debug-profile-502.ps1
# Before
$EMAIL = "karthikpradep@gmail.com"

# After
$EMAIL = "test-user@example.com"
```

## Verification

After remediation, verify no sensitive data remains:

```bash
# Check for API endpoint
git grep "vtqjfznspc" -- ':!SECURITY_*.md'

# Check for email
git grep "karthikpradep@gmail.com" -- ':!SECURITY_*.md'

# Should return no results (except in security docs)
```

## Prevention

### 1. Install Pre-commit Hooks

```bash
# Install git-secrets
# Windows (using Chocolatey)
choco install git-secrets

# Configure
git secrets --install
git secrets --register-aws
git secrets --add 'vtqjfznspc\.execute-api'
git secrets --add '[a-zA-Z0-9._%+-]+@gmail\.com'
```

### 2. Update .gitignore

Already done - `.env` files are ignored.

### 3. Use Environment Variables

Always use environment variables for:
- API endpoints
- AWS account IDs
- Email addresses
- Any infrastructure details

### 4. Code Review Checklist

Add to PR template:
- [ ] No hardcoded API endpoints
- [ ] No personal emails or PII
- [ ] No AWS account IDs
- [ ] No credentials or secrets
- [ ] Environment variables used for configuration

## Risk Assessment

### Current Risk Level: 🟡 MEDIUM

**Why Medium and not High?**
- API Gateway endpoint is public-facing anyway (needs to be accessible)
- Endpoint is protected by Cognito authentication
- No actual credentials (API keys, passwords) were exposed
- Email is in a test script, not production code

**Recommended Actions:**
1. ✅ Fix going forward (use environment variables)
2. ⚠️ Optional: Rotate API Gateway endpoint
3. ✅ Add pre-commit hooks
4. ✅ Update documentation

## Questions?

If you have questions about this remediation:
1. Review the SECURITY_AUDIT_REPORT.md
2. Check the agent-steering.md for security guidelines
3. Consult with security team if rotating production endpoints

## Completion Checklist

- [ ] Run remediation script
- [ ] Review changes
- [ ] Commit changes
- [ ] Update .env files locally
- [ ] Verify no sensitive data in new commits
- [ ] (Optional) Rotate API Gateway endpoint
- [ ] Install pre-commit hooks
- [ ] Update team documentation
