# Phase 4 CI/CD Quick Reference

Quick commands and checks for Phase 4 CI/CD pipeline.

## Pre-Commit Checks

### Run All Quality Checks Locally
```bash
# Frontend
cd frontend
npm run lint
npm run format:check
npx tsc --noEmit --strict
npm test -- --coverage --watchAll=false
npm run build
node scripts/check-bundle-size.js

# Backend
cd lambda
mypy . --config-file=mypy.ini
bash ../scripts/lint-python.sh
pytest -v --cov=. --cov-report=term --cov-fail-under=80
```

## Quick Fixes

### Fix Linting Issues
```bash
# Frontend
cd frontend
npm run lint:fix
npm run format

# Backend
cd lambda
pylint --fix {file}.py
```

### Fix Type Errors
```bash
# Python - Add type hints
def my_function(param: str) -> Dict[str, Any]:
    """Docstring with types"""
    pass

# TypeScript - Enable strict mode
// tsconfig.json already has "strict": true
```

### Improve Test Coverage
```bash
# Find uncovered code
cd frontend
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html

# Python
cd lambda/{function}
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Reduce Bundle Size
```bash
cd frontend
npm run build:analyze
# Look for large dependencies
# Consider code splitting or lazy loading
```

## CI/CD Pipeline Status

### Check Pipeline Status
- Go to: https://github.com/{org}/{repo}/actions
- Look for: ✅ (passing) or ❌ (failing)

### View Performance Regression
- On PR: Check comments for performance report
- Locally: `npm run performance:regression`

### View Compliance Report
- In Actions: Download "compliance-validation-report" artifact
- Locally: Run compliance tests

## Common Issues

### "Type checking failed"
```bash
# Check specific function
cd lambda/{function}
mypy . --config-file=../mypy.ini

# Add missing type hints
# Install type stubs: pip install boto3-stubs types-requests
```

### "Coverage below 80%"
```bash
# Identify uncovered code
pytest --cov=. --cov-report=term-missing

# Write tests for uncovered functions
# Focus on business logic, not boilerplate
```

### "Bundle size exceeds 500KB"
```bash
# Analyze bundle
npm run build:analyze

# Solutions:
# 1. Remove unused dependencies
# 2. Use dynamic imports: const Module = lazy(() => import('./Module'))
# 3. Optimize images
# 4. Enable tree shaking
```

### "Performance regression detected"
```bash
# View detailed report
npm run performance:regression

# Common causes:
# - New large dependencies
# - Unoptimized images
# - Missing memoization
# - Blocking JavaScript

# Solutions:
# - Use React.memo, useMemo, useCallback
# - Lazy load components
# - Optimize images (WebP, compression)
# - Code splitting
```

### "Compliance validation failed"
```bash
# Check what failed
# View Actions logs or run locally:

# Audit logging
grep -r "audit_logger" lambda/auth_service/

# Data encryption
test -f lambda/shared/data_encryption_service.py

# GDPR services
test -d lambda/gdpr_service

# Run tests
pytest tests/integration/test_gdpr_export_workflow.py -v
```

## Deployment

### Deploy to Staging
```bash
# Automatic on push to develop branch
git checkout develop
git merge feature-branch
git push origin develop
```

### Deploy to Production
```bash
# Automatic on push to main branch
git checkout main
git merge develop
git push origin main
```

### Manual Deployment
```bash
# Trigger via GitHub Actions UI
# Go to Actions → CI/CD Pipeline → Run workflow
# Select environment: staging or production
```

### Validate Deployment
```bash
python scripts/validate-phase4-deployment.py \
  --region us-east-1 \
  --environment staging
```

## Monitoring

### View Metrics
```bash
# CloudWatch Dashboard
# https://console.aws.amazon.com/cloudwatch/

# Key metrics:
# - Lambda cold starts
# - API latency
# - Cache hit rate
# - Error rate
```

### Check Logs
```bash
# Lambda logs
aws logs tail /aws/lambda/AquaChain-{function}-{env} --follow

# API Gateway logs
aws logs tail /aws/apigateway/AquaChain-API-{env} --follow
```

## Rollback

### Rollback Lambda
```bash
# Switch to BLUE alias
aws lambda update-alias \
  --function-name AquaChain-{function}-production \
  --name LIVE \
  --function-version $(aws lambda get-alias \
    --function-name AquaChain-{function}-production \
    --name BLUE \
    --query 'FunctionVersion' --output text)
```

### Rollback Frontend
```bash
# Restore from backup
aws s3 sync s3://aquachain-frontend-blue-{account}/ \
  s3://aquachain-frontend-production-{account}/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id {distribution-id} \
  --paths "/*"
```

## Useful Commands

### Check Coverage
```bash
# Frontend
cd frontend && npm test -- --coverage --watchAll=false

# Backend
cd lambda && pytest --cov=. --cov-report=term
```

### Run Performance Tests
```bash
cd frontend
npm run performance:budget
npm run performance:regression
npm run lighthouse
```

### Run Security Scans
```bash
# Dependency vulnerabilities
npm audit
pip-audit

# Code security
npm run test:security
```

### Build and Test Locally
```bash
# Full frontend build
cd frontend
npm ci
npm run lint
npm test -- --watchAll=false
npm run build
node scripts/check-bundle-size.js

# Full backend test
cd lambda
pip install -r requirements-dev.txt
mypy . --config-file=mypy.ini
pytest -v --cov=. --cov-fail-under=80
```

## Environment Variables

### Local Development
```bash
# Frontend (.env.development)
REACT_APP_API_URL=http://localhost:3001
REACT_APP_WS_URL=ws://localhost:3001

# Backend
AWS_REGION=us-east-1
ENVIRONMENT=development
```

### CI/CD Secrets
- Set in GitHub: Settings → Secrets and variables → Actions
- Required: AWS credentials, account ID, CloudFront IDs

## Resources

- [Full Documentation](PHASE_4_CICD_ENHANCEMENTS.md)
- [Code Quality Standards](CODE_QUALITY_STANDARDS.md)
- [Performance Guide](frontend/PERFORMANCE_OPTIMIZATIONS.md)
- [Compliance Guide](COMPLIANCE_REPORTING_QUICK_REFERENCE.md)

## Support

**Pipeline Issues**: Check GitHub Actions logs  
**AWS Issues**: Check CloudWatch logs  
**Questions**: Contact DevOps team

---

**Tip**: Bookmark this page for quick reference during development!
