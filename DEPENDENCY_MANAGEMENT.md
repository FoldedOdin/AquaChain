# Dependency Management Guide

This document describes the automated dependency management system for the AquaChain project, including Dependabot configuration, security scanning, and auto-merge policies.

## Overview

The AquaChain project uses a comprehensive dependency management strategy to:
- Keep dependencies up-to-date automatically
- Scan for security vulnerabilities daily
- Auto-merge safe patch updates
- Require manual review for major updates

## Components

### 1. Dependabot Configuration

**Location:** `.github/dependabot.yml`

Dependabot automatically creates pull requests for dependency updates across:
- Frontend (npm packages)
- Lambda functions (Python packages)
- Infrastructure (Python packages)
- IoT Simulator (Python packages)
- GitHub Actions workflows

**Schedule:** Weekly on Mondays at 9:00 AM UTC

**Update Strategy:**
- **Patch updates** (e.g., 1.2.3 → 1.2.4): Auto-merged after CI passes
- **Minor updates** (e.g., 1.2.0 → 1.3.0): Requires manual review
- **Major updates** (e.g., 1.0.0 → 2.0.0): Requires manual review and testing

### 2. Security Vulnerability Scanning

**Location:** `.github/workflows/dependency-security-scan.yml`

**Runs:**
- Daily at 2 AM UTC (scheduled)
- On push to main/develop branches
- On pull requests that modify dependencies
- On manual trigger

**Tools Used:**
- **npm audit**: Scans frontend JavaScript/TypeScript dependencies
- **Safety**: Scans Python dependencies for known vulnerabilities
- **pip-audit**: Additional Python vulnerability scanning
- **Snyk**: Third-party security scanning (optional, requires token)
- **Trivy**: Container and filesystem vulnerability scanning

**Severity Levels:**
- 🔴 **Critical**: Build fails, immediate action required
- 🟠 **High**: Warning issued, should be addressed soon
- 🟡 **Medium**: Tracked, address in next sprint
- 🟢 **Low**: Informational, address when convenient

### 3. Auto-Merge Workflow

**Location:** `.github/workflows/dependabot-auto-merge.yml`

**Behavior:**
- Automatically approves and merges **patch updates only**
- Waits for all CI checks to pass before merging
- Adds appropriate labels to PRs
- Comments on PRs requiring manual review

**Auto-Merge Criteria:**
1. PR is from Dependabot
2. Update is a patch version (semver-patch)
3. All CI checks pass (code quality, tests, security)
4. No critical vulnerabilities detected

## Workflow Details

### Dependabot PR Lifecycle

```
1. Dependabot creates PR
   ↓
2. CI/CD pipeline runs
   ↓
3. Security scan runs
   ↓
4. Auto-merge workflow checks update type
   ↓
5a. Patch update → Auto-approve → Auto-merge
5b. Minor/Major update → Label "requires-review" → Wait for manual approval
```

### Security Scan Workflow

```
1. Scan triggered (schedule/push/PR)
   ↓
2. Parallel scans:
   - Frontend (npm audit)
   - Lambda functions (safety, pip-audit)
   - Infrastructure (safety, pip-audit)
   ↓
3. Aggregate results
   ↓
4. Generate summary report
   ↓
5. Comment on PR (if applicable)
   ↓
6. Fail build if critical vulnerabilities found
```

## Configuration

### Dependabot Settings

**Ignored Updates:**
Critical packages that require manual review for major updates:
- `react` and `react-dom`
- `typescript`
- `aws-amplify`

**Grouping:**
- Production dependencies: Minor and patch updates grouped
- Development dependencies: Minor and patch updates grouped
- AWS dependencies: Grouped together for Lambda functions

**PR Limits:**
- Frontend: 10 open PRs max
- Lambda functions: 5 open PRs max per function
- Infrastructure: 5 open PRs max

### Security Scan Thresholds

**Build Failure Conditions:**
- Any critical vulnerabilities in any component
- More than 5 high severity vulnerabilities in frontend

**Warning Conditions:**
- High severity vulnerabilities detected
- More than 10 medium severity vulnerabilities

## Manual Processes

### Reviewing Minor/Major Updates

When Dependabot creates a PR for a minor or major update:

1. **Review the changelog:**
   - Check the dependency's GitHub releases or changelog
   - Look for breaking changes or new features

2. **Test locally:**
   ```bash
   # Checkout the Dependabot branch
   git fetch origin
   git checkout dependabot/<branch-name>
   
   # For frontend updates
   cd frontend
   npm install
   npm test
   npm run build
   
   # For Lambda updates
   cd lambda/<function-name>
   pip install -r requirements.txt
   python -m pytest
   ```

3. **Check for breaking changes:**
   - Review code that uses the updated dependency
   - Update code if necessary to handle breaking changes

4. **Approve and merge:**
   - If everything looks good, approve the PR
   - Merge using squash merge

### Handling Security Vulnerabilities

When a security vulnerability is detected:

1. **Assess severity:**
   - Critical: Drop everything and fix immediately
   - High: Fix within 24-48 hours
   - Medium: Fix within 1 week
   - Low: Fix in next sprint

2. **Check for available fixes:**
   ```bash
   # For npm packages
   cd frontend
   npm audit fix
   
   # For Python packages
   cd lambda/<function-name>
   pip install --upgrade <package-name>
   ```

3. **If no fix available:**
   - Check if the vulnerability affects your usage
   - Consider alternative packages
   - Document the risk and mitigation plan
   - Create a tracking issue

4. **Test the fix:**
   - Run full test suite
   - Test affected functionality manually
   - Deploy to staging environment

5. **Deploy the fix:**
   - Create PR with the fix
   - Get it reviewed and merged
   - Deploy to production

### Overriding Auto-Merge

To prevent a patch update from being auto-merged:

1. Add the label `no-auto-merge` to the PR
2. The auto-merge workflow will skip the PR
3. Review and merge manually when ready

## Monitoring and Reporting

### Daily Security Reports

Security scan results are available:
- In GitHub Actions workflow runs
- As downloadable artifacts (JSON reports)
- In PR comments (for PRs that modify dependencies)

### Weekly Dependency Updates

Every Monday, Dependabot checks for updates and creates PRs:
- Check the "Pull Requests" tab for new Dependabot PRs
- Review the labels to identify update types
- Patch updates will auto-merge if CI passes
- Minor/major updates require manual review

### Metrics to Track

Monitor these metrics in GitHub Insights:
- Number of open Dependabot PRs
- Time to merge dependency updates
- Number of security vulnerabilities detected
- Time to fix critical vulnerabilities

## Troubleshooting

### Dependabot PRs Not Being Created

**Possible causes:**
1. Dependabot is disabled for the repository
2. PR limit reached (check `.github/dependabot.yml`)
3. No updates available

**Solution:**
- Check repository settings → Security → Dependabot
- Review open Dependabot PRs and merge/close some
- Manually trigger Dependabot: Repository → Insights → Dependency graph → Dependabot

### Auto-Merge Not Working

**Possible causes:**
1. CI checks failing
2. Update is not a patch version
3. Branch protection rules preventing auto-merge

**Solution:**
- Check CI workflow runs for failures
- Review the PR labels (should have `auto-merge-candidate`)
- Verify branch protection settings allow auto-merge

### Security Scan Failing

**Possible causes:**
1. Critical vulnerabilities detected
2. Scan tools not installed properly
3. Network issues accessing vulnerability databases

**Solution:**
- Review the security scan workflow logs
- Check the uploaded security report artifacts
- Fix critical vulnerabilities immediately
- Re-run the workflow if it was a transient failure

### False Positive Vulnerabilities

**Solution:**
1. Verify the vulnerability affects your usage
2. If false positive, document in a comment
3. Consider using `.snyk` policy file to ignore specific vulnerabilities
4. Create an issue to track and review periodically

## Best Practices

1. **Review Dependabot PRs regularly:**
   - Don't let them pile up
   - Merge patch updates quickly
   - Schedule time for minor/major updates

2. **Keep dependencies up-to-date:**
   - Staying current makes updates easier
   - Reduces security risk
   - Easier to debug issues

3. **Test thoroughly:**
   - Don't rely solely on automated tests
   - Test critical paths manually
   - Use staging environment for major updates

4. **Monitor security alerts:**
   - Check GitHub Security tab regularly
   - Subscribe to security advisories for critical packages
   - Act quickly on critical vulnerabilities

5. **Document decisions:**
   - Comment on PRs with review notes
   - Document why certain updates are delayed
   - Track technical debt related to outdated dependencies

## Integration with CI/CD

The dependency management system integrates with the main CI/CD pipeline:

1. **Code Quality Checks:** Run on all Dependabot PRs
2. **Security Scans:** Run automatically on dependency changes
3. **Test Suites:** Full test coverage required before auto-merge
4. **Deployment:** Updated dependencies deployed through normal pipeline

## Security Considerations

1. **Secrets Management:**
   - `SNYK_TOKEN`: Optional, for Snyk scanning
   - `GITHUB_TOKEN`: Automatically provided by GitHub Actions

2. **Permissions:**
   - Dependabot has write access to create PRs
   - Auto-merge workflow has write access to merge PRs
   - Security scan workflow has read access only

3. **Audit Trail:**
   - All dependency updates tracked in Git history
   - Security scan results archived for 90 days
   - PR comments provide context for decisions

## Support and Resources

- **Dependabot Documentation:** https://docs.github.com/en/code-security/dependabot
- **npm audit:** https://docs.npmjs.com/cli/v8/commands/npm-audit
- **Safety:** https://pyup.io/safety/
- **pip-audit:** https://github.com/pypa/pip-audit
- **Snyk:** https://snyk.io/

## Changelog

- **2025-10-25:** Initial dependency management system setup
  - Configured Dependabot for all package ecosystems
  - Set up automated security scanning
  - Implemented auto-merge for patch updates
