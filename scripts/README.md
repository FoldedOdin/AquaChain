# AquaChain Scripts

This directory contains utility scripts for the AquaChain project.

## Code Quality Scripts

### lint-all.sh
Comprehensive linting script that checks both frontend and backend code quality.

**Usage:**
```bash
bash scripts/lint-all.sh
```

**What it does:**
- Runs ESLint on frontend TypeScript/React code
- Checks Prettier formatting
- Runs Pylint on all Lambda functions
- Provides colored output and summary

**Exit codes:**
- `0`: All checks passed
- `1`: One or more checks failed

### lint-python.sh
Python-specific linting script for Lambda functions.

**Usage:**
```bash
bash scripts/lint-python.sh
```

**What it does:**
- Finds all Lambda function directories
- Runs Pylint on each function
- Lints shared modules
- Reports individual function status

**Configuration:**
Uses `.pylintrc` in project root.

## Other Scripts

### generate-sbom.py
Generates Software Bill of Materials (SBOM) for the project.

### vulnerability-report-generator.py
Scans dependencies for security vulnerabilities.

### deploy.py
Deployment automation script.

### disaster_recovery.py
Disaster recovery procedures.

### validate-phase3-deployment.py
Validates Phase 3 deployment.

## Running Scripts on Windows

These are bash scripts. On Windows, you can run them using:

1. **Git Bash** (recommended)
   ```bash
   bash scripts/lint-all.sh
   ```

2. **WSL (Windows Subsystem for Linux)**
   ```bash
   bash scripts/lint-all.sh
   ```

3. **PowerShell** (may require adjustments)
   ```powershell
   bash scripts/lint-all.sh
   ```

## CI/CD Integration

These scripts are integrated into the GitHub Actions CI/CD pipeline:
- `.github/workflows/ci-cd-pipeline.yml`

The `code-quality` job runs linting checks on every push and pull request.

## Development Workflow

1. Make code changes
2. Run `bash scripts/lint-all.sh` before committing
3. Fix any reported issues
4. Commit (pre-commit hooks will run automatically)
5. Push to GitHub (CI/CD will run full checks)

## Troubleshooting

### "pylint: command not found"
Install Python development dependencies:
```bash
pip install -r requirements-dev.txt
```

### "npm: command not found"
Install Node.js and npm, then install frontend dependencies:
```bash
cd frontend
npm install
```

### Permission denied
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

## Adding New Scripts

When adding new scripts:

1. Place them in this directory
2. Add execute permissions: `chmod +x scripts/your-script.sh`
3. Document them in this README
4. Add them to CI/CD if needed

## Support

For issues with scripts:
1. Check this README
2. Review script comments
3. Check CI/CD logs in GitHub Actions
4. Create an issue in the repository
