# Dependency Management Quick Reference

Quick reference guide for managing dependencies in the AquaChain project.

## Daily Tasks

### Check for New Dependabot PRs
```bash
# View open Dependabot PRs
gh pr list --label dependencies

# Or visit: https://github.com/<org>/<repo>/pulls?q=is:pr+is:open+label:dependencies
```

### Review Security Alerts
```bash
# Check GitHub Security tab
# Or run manual dependency check
python scripts/dependency-check.py --check
```

## Weekly Tasks

### Review Dependabot PRs

**Patch Updates (Auto-merged):**
- ✅ Automatically merged if CI passes
- No action needed unless CI fails

**Minor Updates (Manual review):**
1. Check the PR description for changes
2. Review the changelog
3. Test locally if needed
4. Approve and merge

**Major Updates (Careful review):**
1. ⚠️ Review breaking changes carefully
2. Update code to handle breaking changes
3. Test thoroughly in staging
4. Approve and merge after validation

### Generate Dependency Report
```bash
# Generate comprehensive report
python scripts/dependency-check.py --report --output dependency-report.json

# Check version consistency
python scripts/dependency-check.py --consistency
```

## Common Commands

### Frontend (npm)

```bash
cd frontend

# Check for outdated packages
npm outdated

# Check for vulnerabilities
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Update a specific package
npm update <package-name>

# Update all packages (respecting semver)
npm update

# Install a specific version
npm install <package-name>@<version>
```

### Lambda Functions (pip)

```bash
cd lambda/<function-name>

# Check for outdated packages
pip list --outdated

# Check for vulnerabilities
safety check --file requirements.txt
pip-audit --requirement requirements.txt

# Update a specific package
pip install --upgrade <package-name>

# Update requirements.txt
pip freeze > requirements.txt
```

### Infrastructure (pip)

```bash
cd infrastructure

# Same commands as Lambda functions
pip list --outdated
safety check --file requirements.txt
```

## Handling Security Vulnerabilities

### Critical Vulnerabilities (🔴)
1. **Immediate action required**
2. Check for available fix: `npm audit fix` or `pip install --upgrade <package>`
3. Test the fix
4. Create PR and merge ASAP
5. Deploy to production immediately

### High Vulnerabilities (🟠)
1. **Fix within 24-48 hours**
2. Follow same process as critical
3. Can wait for next deployment cycle

### Medium/Low Vulnerabilities (🟡🟢)
1. **Fix in next sprint**
2. Create tracking issue
3. Include in next dependency update cycle

## Troubleshooting

### Dependabot PR Not Auto-Merging

**Check:**
1. Is it a patch update? (Only patches auto-merge)
2. Did CI pass? (Check workflow runs)
3. Are there merge conflicts?

**Fix:**
```bash
# Rebase Dependabot branch
gh pr comment <pr-number> --body "@dependabot rebase"

# Or manually merge
gh pr merge <pr-number> --squash
```

### CI Failing on Dependabot PR

**Check:**
1. Review CI logs
2. Test locally
3. May need code changes to support new version

**Fix:**
```bash
# Checkout Dependabot branch
gh pr checkout <pr-number>

# Make necessary fixes
# ... edit files ...

# Push fixes
git add .
git commit -m "fix: update code for new dependency version"
git push
```

### Security Scan Failing

**Check:**
1. Review security scan logs
2. Check which vulnerabilities were found
3. Determine if they affect your code

**Fix:**
```bash
# For npm
cd frontend
npm audit fix

# For pip
cd lambda/<function-name>
pip install --upgrade <vulnerable-package>
pip freeze > requirements.txt

# Create PR with fixes
git checkout -b fix/security-vulnerabilities
git add .
git commit -m "fix: address security vulnerabilities"
git push origin fix/security-vulnerabilities
gh pr create
```

## Labels

- `dependencies`: All dependency updates
- `auto-merge-candidate`: Patch updates eligible for auto-merge
- `minor-update`: Minor version updates
- `major-update`: Major version updates
- `requires-review`: Updates requiring manual review
- `no-auto-merge`: Prevent auto-merge for specific PRs

## Workflows

### Dependabot Configuration
- **File:** `.github/dependabot.yml`
- **Schedule:** Weekly, Mondays at 9 AM UTC
- **Scope:** Frontend, Lambda, Infrastructure, GitHub Actions

### Dependency Security Scan
- **File:** `.github/workflows/dependency-security-scan.yml`
- **Schedule:** Daily at 2 AM UTC
- **Triggers:** Push, PR, Manual
- **Tools:** npm audit, safety, pip-audit, Snyk, Trivy

### Dependabot Auto-Merge
- **File:** `.github/workflows/dependabot-auto-merge.yml`
- **Triggers:** Dependabot PRs
- **Behavior:** Auto-merge patch updates after CI passes

## Best Practices

✅ **DO:**
- Review Dependabot PRs regularly
- Merge patch updates quickly
- Test major updates thoroughly
- Keep dependencies up-to-date
- Monitor security alerts

❌ **DON'T:**
- Ignore Dependabot PRs
- Merge major updates without testing
- Disable security scanning
- Let vulnerabilities accumulate
- Skip changelog reviews

## Resources

- **Full Documentation:** [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md)
- **Dependabot Docs:** https://docs.github.com/en/code-security/dependabot
- **npm audit:** https://docs.npmjs.com/cli/v8/commands/npm-audit
- **Safety:** https://pyup.io/safety/
- **pip-audit:** https://github.com/pypa/pip-audit

## Support

For questions or issues:
1. Check [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md)
2. Review workflow logs in GitHub Actions
3. Contact the DevOps team
4. Create an issue in the repository
