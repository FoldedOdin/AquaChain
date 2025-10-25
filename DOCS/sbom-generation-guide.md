# Software Bill of Materials (SBOM) Generation Guide

## Overview

This guide explains how to generate, manage, and analyze Software Bill of Materials (SBOMs) for the AquaChain project. SBOMs provide a comprehensive inventory of all software components, dependencies, and their associated metadata.

## Table of Contents

1. [What is an SBOM?](#what-is-an-sbom)
2. [Prerequisites](#prerequisites)
3. [Generating SBOMs](#generating-sboms)
4. [Vulnerability Scanning](#vulnerability-scanning)
5. [CI/CD Integration](#cicd-integration)
6. [SBOM Storage and Versioning](#sbom-storage-and-versioning)
7. [Comparing SBOMs](#comparing-sboms)
8. [Compliance Reporting](#compliance-reporting)
9. [Troubleshooting](#troubleshooting)

---

## What is an SBOM?

A Software Bill of Materials (SBOM) is a comprehensive inventory of all components in a software application, including:

- **Direct dependencies**: Libraries explicitly included in your project
- **Transitive dependencies**: Dependencies of your dependencies
- **Version information**: Specific versions of each component
- **License information**: Licensing terms for each component
- **Vulnerability data**: Known security vulnerabilities

### Why SBOMs Matter

- **Security**: Identify vulnerable components quickly
- **Compliance**: Meet regulatory requirements (e.g., Executive Order 14028)
- **Supply Chain**: Track software supply chain integrity
- **License Management**: Ensure license compliance
- **Transparency**: Provide visibility into software composition

---

## Prerequisites

### Required Tools

#### 1. Syft (SBOM Generator)

Syft generates SBOMs in various formats including SPDX and CycloneDX.

**Installation:**

```bash
# Linux/macOS
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# macOS (Homebrew)
brew install syft

# Windows (Chocolatey)
choco install syft

# Verify installation
syft version
```

#### 2. Grype (Vulnerability Scanner)

Grype scans SBOMs for known vulnerabilities.

**Installation:**

```bash
# Linux/macOS
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# macOS (Homebrew)
brew install grype

# Windows (Chocolatey)
choco install grype

# Verify installation
grype version
```

#### 3. Python 3.11+

Required for running the SBOM generation scripts.

```bash
python --version  # Should be 3.11 or higher
```

#### 4. Node.js 18+

Required for frontend dependency analysis.

```bash
node --version  # Should be 18 or higher
```

---

## Generating SBOMs

### Manual Generation

#### Generate All SBOMs

```bash
# From project root
python scripts/generate-sbom.py
```

This will:
1. Generate SBOMs for all components (frontend, backend, infrastructure, IoT)
2. Merge them into a comprehensive SBOM
3. Scan for vulnerabilities using Grype
4. Generate summary reports

**Output:**
- `sbom-artifacts/sbom-frontend-<timestamp>.json`
- `sbom-artifacts/sbom-backend-<timestamp>.json`
- `sbom-artifacts/sbom-infrastructure-<timestamp>.json`
- `sbom-artifacts/sbom-iot-firmware-<timestamp>.json`
- `sbom-artifacts/sbom-complete-<timestamp>.json`
- `sbom-artifacts/sbom-report-<timestamp>.json`

#### Generate SBOM for Specific Component

```bash
# Frontend only
syft dir:frontend -o spdx-json --file sbom-frontend.json

# Backend/Lambda functions
syft dir:lambda -o spdx-json --file sbom-backend.json

# Infrastructure
syft dir:infrastructure -o spdx-json --file sbom-infrastructure.json

# IoT firmware
syft dir:iot-simulator -o spdx-json --file sbom-iot.json
```

### Understanding SBOM Output

The generated SBOM follows the SPDX 2.3 format:

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "AquaChain-Complete-SBOM",
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-1",
      "name": "react",
      "versionInfo": "18.2.0",
      "supplier": "Organization: npm",
      "licenseDeclared": "MIT",
      "downloadLocation": "https://registry.npmjs.org/react/-/react-18.2.0.tgz"
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-Package-Root",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-1"
    }
  ]
}
```

---

## Vulnerability Scanning

### Scan SBOM for Vulnerabilities

```bash
# Scan a specific SBOM
grype sbom:sbom-artifacts/sbom-complete-<timestamp>.json -o json

# Scan and save results
grype sbom:sbom-artifacts/sbom-complete-<timestamp>.json -o json --file vulnerabilities.json

# Scan with specific severity threshold
grype sbom:sbom-artifacts/sbom-complete-<timestamp>.json --fail-on high
```

### Generate Vulnerability Reports

```bash
# Generate HTML and JSON reports
python scripts/vulnerability-report-generator.py
```

**Output:**
- `sbom-artifacts/vulnerability-report-<component>-<timestamp>.html` - Human-readable HTML report
- `sbom-artifacts/vulnerability-report-<component>-<timestamp>.json` - Machine-readable JSON report

### Understanding Vulnerability Reports

Vulnerabilities are categorized by severity:

- **Critical**: Immediate action required
- **High**: Address as soon as possible
- **Medium**: Address in next release cycle
- **Low**: Address when convenient
- **Negligible**: Informational only

Each vulnerability includes:
- CVE ID
- CVSS score
- Affected package and version
- Fix version (if available)
- Description and references

---

## CI/CD Integration

### Automatic SBOM Generation

SBOMs are automatically generated in two scenarios:

#### 1. On Every Push/PR

Triggered by: `.github/workflows/ci-cd-pipeline.yml`

**What happens:**
1. Syft and Grype are installed
2. SBOMs are generated for all components
3. Vulnerabilities are scanned
4. Critical vulnerabilities fail the build
5. Results are uploaded as artifacts
6. PR comments show vulnerability summary

**Viewing Results:**
- Go to Actions tab in GitHub
- Click on the workflow run
- Download "sbom-artifacts" artifact

#### 2. Weekly Scheduled Scan

Triggered by: `.github/workflows/sbom-weekly.yml`

**Schedule:** Every Monday at 2 AM UTC

**What happens:**
1. Complete SBOM generation
2. Vulnerability scanning
3. Upload to S3
4. SNS notifications for critical vulnerabilities
5. GitHub issue creation for high/critical vulnerabilities
6. Trend analysis

### Configuring CI/CD

#### GitHub Secrets Required

```yaml
AWS_ACCESS_KEY_ID: <your-access-key>
AWS_SECRET_ACCESS_KEY: <your-secret-key>
AWS_ACCOUNT_ID: <your-account-id>
```

#### Customizing Thresholds

Edit `.github/workflows/ci-cd-pipeline.yml`:

```yaml
- name: Check for critical vulnerabilities
  run: |
    # Modify this section to change failure thresholds
    if critical > 0:
        sys.exit(1)  # Fail on critical
    if high > 10:
        sys.exit(1)  # Fail on more than 10 high
```

---

## SBOM Storage and Versioning

### S3 Bucket Structure

```
s3://aquachain-sbom-<account-id>/
├── latest/                          # Most recent SBOMs
│   ├── sbom-complete-*.json
│   ├── sbom-frontend-*.json
│   ├── sbom-backend-*.json
│   └── vulnerability-report-*.json
├── weekly/                          # Weekly snapshots
│   ├── 2025-W43/
│   ├── 2025-W44/
│   └── 2025-W45/
└── <timestamp>/                     # Timestamped versions
    ├── sbom-complete-*.json
    └── ...
```

### Lifecycle Policies

- **Current versions**: Retained indefinitely
- **Non-current versions**: Retained for 90 days
- **Old versions**: Transitioned to Glacier after 30 days
- **Weekly SBOMs**: Retained for 1 year
- **Latest folder**: Transitioned to Intelligent-Tiering after 90 days

### Accessing SBOMs

#### AWS CLI

```bash
# List all SBOMs
aws s3 ls s3://aquachain-sbom-<account-id>/latest/

# Download latest complete SBOM
aws s3 cp s3://aquachain-sbom-<account-id>/latest/sbom-complete-*.json ./

# Download specific week
aws s3 sync s3://aquachain-sbom-<account-id>/weekly/2025-W43/ ./sboms/
```

#### AWS Console

1. Navigate to S3 in AWS Console
2. Open bucket `aquachain-sbom-<account-id>`
3. Browse to desired folder
4. Download files

### Versioning

All SBOMs are versioned automatically:
- S3 versioning is enabled
- Each upload creates a new version
- Previous versions are retained per lifecycle policy
- Version IDs can be used to retrieve specific versions

```bash
# List all versions of a file
aws s3api list-object-versions \
  --bucket aquachain-sbom-<account-id> \
  --prefix latest/sbom-complete

# Download specific version
aws s3api get-object \
  --bucket aquachain-sbom-<account-id> \
  --key latest/sbom-complete-*.json \
  --version-id <version-id> \
  sbom-old.json
```

---

## Comparing SBOMs

### Compare Two SBOMs

```bash
# Compare old and new SBOMs
python scripts/compare-sboms.py sbom-old.json sbom-new.json

# Save comparison report
python scripts/compare-sboms.py sbom-old.json sbom-new.json comparison-report.json
```

### Comparison Report

The comparison identifies:

- **Added packages**: New dependencies
- **Removed packages**: Removed dependencies
- **Updated packages**: Version changes
- **License changes**: License modifications
- **Unchanged packages**: No changes

**Example Output:**

```
SBOM COMPARISON REPORT
============================================================
Old SBOM: sbom-old.json
New SBOM: sbom-new.json

SUMMARY
------------------------------------------------------------
Total packages (old): 1,234
Total packages (new): 1,256
Net change: +22

Added:           25
Removed:         3
Updated:         47
License changes: 2
Unchanged:       1,184

ADDED PACKAGES (25)
------------------------------------------------------------
  + axios@1.6.0 (MIT)
  + lodash@4.17.21 (MIT)
  ...

UPDATED PACKAGES (47)
------------------------------------------------------------
  ↑ react: 18.2.0 → 18.3.0
  ↑ typescript: 5.0.0 → 5.2.0
  ...
```

### Automated Comparison

SBOMs are automatically compared when uploaded to S3:
- Lambda function triggers on new SBOM uploads
- Compares with previous version
- Generates comparison report
- Sends SNS notification if significant changes detected

---

## Compliance Reporting

### Generating Compliance Reports

#### Executive Summary

```bash
# Generate summary from latest SBOM
python - <<EOF
import json
from pathlib import Path

report_files = list(Path('sbom-artifacts').glob('sbom-report-*.json'))
with open(report_files[0]) as f:
    report = json.load(f)

print("AquaChain SBOM Executive Summary")
print("="*60)
print(f"Total Software Components: {report['total_packages']}")
print(f"Total Vulnerabilities: {report['total_vulnerabilities']}")
print(f"\nVulnerability Breakdown:")
for severity, count in report['vulnerability_summary'].items():
    if count > 0:
        print(f"  {severity}: {count}")
EOF
```

#### License Compliance Report

```bash
# Extract license information
syft dir:. -o json | jq '.artifacts[] | {name: .name, version: .version, licenses: .licenses}'
```

#### Supply Chain Report

The SBOM provides full supply chain visibility:
- All direct and transitive dependencies
- Source locations (npm, PyPI, etc.)
- Version pinning status
- Update availability

### Regulatory Compliance

#### Executive Order 14028 (US)

The SBOM generation process complies with EO 14028 requirements:
- ✅ Machine-readable format (SPDX JSON)
- ✅ Comprehensive component inventory
- ✅ Automated generation and updates
- ✅ Vulnerability tracking
- ✅ Secure storage and access controls

#### NTIA Minimum Elements

Our SBOMs include all NTIA minimum elements:
- ✅ Supplier name
- ✅ Component name
- ✅ Version of component
- ✅ Other unique identifiers
- ✅ Dependency relationships
- ✅ Author of SBOM data
- ✅ Timestamp

---

## Troubleshooting

### Common Issues

#### 1. Syft Not Found

**Error:** `syft: command not found`

**Solution:**
```bash
# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
syft version
```

#### 2. Grype Not Found

**Error:** `grype: command not found`

**Solution:**
```bash
# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
grype version
```

#### 3. Permission Denied on S3 Upload

**Error:** `Access Denied` when uploading to S3

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM policy
aws iam get-policy --policy-arn arn:aws:iam::<account-id>:policy/AquaChain-SBOM-Upload-Policy

# Attach policy to user/role
aws iam attach-user-policy \
  --user-name <username> \
  --policy-arn arn:aws:iam::<account-id>:policy/AquaChain-SBOM-Upload-Policy
```

#### 4. SBOM Generation Fails

**Error:** Script fails during SBOM generation

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check Node.js version
node --version  # Should be 18+

# Install dependencies
cd frontend && npm ci

# Run with verbose output
python scripts/generate-sbom.py --verbose
```

#### 5. Vulnerability Scan Timeout

**Error:** Grype scan times out

**Solution:**
```bash
# Increase timeout
grype sbom:sbom.json --timeout 10m

# Scan specific component only
grype sbom:sbom-frontend.json
```

#### 6. Large SBOM Files

**Issue:** SBOM files are very large

**Solution:**
```bash
# Compress SBOMs before upload
gzip sbom-artifacts/*.json

# Use S3 compression
aws s3 cp sbom.json s3://bucket/ --content-encoding gzip
```

### Getting Help

#### Check Logs

```bash
# CI/CD logs
# Go to GitHub Actions → Select workflow run → View logs

# Lambda logs (SBOM comparison)
aws logs tail /aws/lambda/aquachain-sbom-comparison --follow

# S3 access logs
aws s3 ls s3://aquachain-sbom-logs-<account-id>/
```

#### Debug Mode

```bash
# Run SBOM generation with debug output
PYTHONVERBOSE=1 python scripts/generate-sbom.py

# Syft debug mode
syft dir:. -vv

# Grype debug mode
grype sbom:sbom.json -vv
```

#### Contact

For additional support:
- Create an issue in the GitHub repository
- Contact the DevOps team
- Review the [SBOM specification](https://spdx.dev/specifications/)

---

## Best Practices

### 1. Regular Scanning

- Run SBOM generation weekly (automated)
- Scan on every code change (automated)
- Review vulnerability reports promptly

### 2. Vulnerability Management

- Address critical vulnerabilities immediately
- Plan for high severity vulnerabilities in next sprint
- Track medium/low vulnerabilities for future releases

### 3. License Compliance

- Review license changes in comparison reports
- Maintain approved license list
- Flag incompatible licenses early

### 4. Version Control

- Keep SBOMs in version control for historical tracking
- Tag SBOMs with release versions
- Compare SBOMs between releases

### 5. Documentation

- Document all dependency additions
- Explain why dependencies are needed
- Track dependency update decisions

---

## Additional Resources

### Tools

- [Syft Documentation](https://github.com/anchore/syft)
- [Grype Documentation](https://github.com/anchore/grype)
- [SPDX Specification](https://spdx.dev/specifications/)
- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)

### Standards

- [NTIA SBOM Minimum Elements](https://www.ntia.gov/report/2021/minimum-elements-software-bill-materials-sbom)
- [Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/)
- [CISA SBOM Resources](https://www.cisa.gov/sbom)

### Community

- [SPDX Community](https://spdx.dev/participate/)
- [OpenSSF](https://openssf.org/)
- [Anchore Community](https://github.com/anchore/community)

---

## Appendix

### SBOM Formats

#### SPDX (Software Package Data Exchange)

- ISO/IEC 5962:2021 standard
- Comprehensive metadata
- Wide tool support
- Used by AquaChain

#### CycloneDX

- OWASP project
- Lightweight format
- Security-focused
- Alternative to SPDX

### Vulnerability Databases

Grype uses multiple vulnerability databases:

- **NVD** (National Vulnerability Database)
- **GitHub Security Advisories**
- **Alpine SecDB**
- **Red Hat Security Data**
- **Debian Security Tracker**
- **Ubuntu Security Notices**

### Glossary

- **SBOM**: Software Bill of Materials
- **SPDX**: Software Package Data Exchange
- **CVE**: Common Vulnerabilities and Exposures
- **CVSS**: Common Vulnerability Scoring System
- **NTIA**: National Telecommunications and Information Administration
- **Transitive Dependency**: Dependency of a dependency
- **Supply Chain**: Path from source to deployment

---

**Last Updated:** October 25, 2025  
**Version:** 1.0  
**Maintained By:** AquaChain DevOps Team
