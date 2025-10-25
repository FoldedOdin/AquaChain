# SBOM Quick Reference Guide

## Quick Start

### Generate SBOM

```bash
# Generate all SBOMs
python scripts/generate-sbom.py

# Output: sbom-artifacts/sbom-complete-<timestamp>.json
```

### Scan for Vulnerabilities

```bash
# Automatic (included in generate-sbom.py)
python scripts/generate-sbom.py

# Manual scan
grype sbom:sbom-artifacts/sbom-complete-*.json
```

### Generate Reports

```bash
# HTML and JSON vulnerability reports
python scripts/vulnerability-report-generator.py

# Output: sbom-artifacts/vulnerability-report-*.html
```

### Compare SBOMs

```bash
# Compare two versions
python scripts/compare-sboms.py sbom-old.json sbom-new.json

# Output: sbom-comparison-<timestamp>.json
```

---

## Installation

### Syft (SBOM Generator)

```bash
# Linux/macOS
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Verify
syft version
```

### Grype (Vulnerability Scanner)

```bash
# Linux/macOS
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Verify
grype version
```

---

## CI/CD Integration

### Automatic Triggers

1. **Every Push/PR**: `.github/workflows/ci-cd-pipeline.yml`
   - Generates SBOMs
   - Scans vulnerabilities
   - Fails on critical vulnerabilities
   - Comments on PR with results

2. **Weekly**: `.github/workflows/sbom-weekly.yml`
   - Runs every Monday at 2 AM UTC
   - Uploads to S3
   - Sends SNS notifications
   - Creates GitHub issues for critical vulnerabilities

### View Results

- GitHub Actions → Workflow run → Download "sbom-artifacts"
- S3: `s3://aquachain-sbom-<account-id>/latest/`

---

## S3 Storage

### Bucket Structure

```
s3://aquachain-sbom-<account-id>/
├── latest/              # Most recent
├── weekly/2025-W43/     # Weekly snapshots
└── <timestamp>/         # All versions
```

### Access SBOMs

```bash
# List latest
aws s3 ls s3://aquachain-sbom-<account-id>/latest/

# Download latest
aws s3 cp s3://aquachain-sbom-<account-id>/latest/sbom-complete-*.json ./

# Download specific week
aws s3 sync s3://aquachain-sbom-<account-id>/weekly/2025-W43/ ./
```

---

## Common Commands

### Generate Component-Specific SBOM

```bash
# Frontend
syft dir:frontend -o spdx-json --file sbom-frontend.json

# Backend
syft dir:lambda -o spdx-json --file sbom-backend.json

# Infrastructure
syft dir:infrastructure -o spdx-json --file sbom-infrastructure.json
```

### Scan Specific Severity

```bash
# Fail on high or critical
grype sbom:sbom.json --fail-on high

# Only show critical
grype sbom:sbom.json -o json | jq '.matches[] | select(.vulnerability.severity=="Critical")'
```

### Extract License Information

```bash
# All licenses
syft dir:. -o json | jq '.artifacts[] | {name: .name, licenses: .licenses}'

# Count by license
syft dir:. -o json | jq '.artifacts[].licenses[].value' | sort | uniq -c
```

---

## Troubleshooting

### Syft Not Found

```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
```

### Grype Not Found

```bash
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
```

### S3 Access Denied

```bash
# Verify credentials
aws sts get-caller-identity

# Attach policy
aws iam attach-user-policy \
  --user-name <username> \
  --policy-arn arn:aws:iam::<account-id>:policy/AquaChain-SBOM-Upload-Policy
```

### Large Files

```bash
# Compress before upload
gzip sbom-artifacts/*.json

# Upload compressed
aws s3 cp sbom.json.gz s3://bucket/ --content-encoding gzip
```

---

## Vulnerability Severity

| Severity | Action Required |
|----------|----------------|
| **Critical** | Immediate fix required |
| **High** | Fix in next sprint |
| **Medium** | Plan for future release |
| **Low** | Address when convenient |
| **Negligible** | Informational only |

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/generate-sbom.py` | Main SBOM generator |
| `scripts/vulnerability-report-generator.py` | Generate HTML/JSON reports |
| `scripts/compare-sboms.py` | Compare two SBOMs |
| `.github/workflows/ci-cd-pipeline.yml` | CI/CD SBOM generation |
| `.github/workflows/sbom-weekly.yml` | Weekly scheduled scan |
| `infrastructure/cdk/stacks/sbom_storage_stack.py` | S3 storage infrastructure |

---

## Useful Links

- [Full Documentation](DOCS/sbom-generation-guide.md)
- [Syft Docs](https://github.com/anchore/syft)
- [Grype Docs](https://github.com/anchore/grype)
- [SPDX Spec](https://spdx.dev/specifications/)

---

## Support

- Create GitHub issue
- Contact DevOps team
- Review logs: GitHub Actions or CloudWatch

---

**Last Updated:** October 25, 2025
