# Security Policy

## Overview

AquaChain takes security seriously. This document outlines our security policy, supported versions, and procedures for reporting vulnerabilities. We are committed to maintaining a secure IoT water quality monitoring system that protects user data and device integrity.

---

## Supported Versions

We actively maintain and provide security updates for the following versions of AquaChain:

| Version | Supported          | Status | End of Support |
| ------- | ------------------ | ------ | -------------- |
| 1.1.x   | :white_check_mark: | Current stable release | TBD |
| 1.0.x   | :white_check_mark: | Security fixes only | March 2026 |
| 0.9.x (Beta) | :x:       | No longer supported | October 2025 |
| < 0.9   | :x:                | No longer supported | N/A |

**Note**: We recommend always using the latest stable version (1.1.x) to ensure you have the most recent security patches and features.

---

## Reporting a Vulnerability

We appreciate the security research community's efforts in helping us maintain a secure system. If you discover a security vulnerability, please follow these guidelines:

### Where to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:

- **Email**: security@aquachain.com (preferred)
- **Alternative**: contactaquachain@gmail.com with subject line "SECURITY VULNERABILITY"
- **Encrypted**: Use our PGP key (available upon request) for sensitive disclosures

### What to Include

Please provide the following information in your report:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and severity assessment
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Proof of Concept**: Code, screenshots, or video demonstration (if applicable)
5. **Affected Components**: Which parts of the system are affected (frontend, backend, IoT devices, etc.)
6. **Suggested Fix**: If you have recommendations (optional)
7. **Your Contact Information**: For follow-up questions

### Response Timeline

We are committed to responding promptly to security reports:

| Timeline | Action |
|----------|--------|
| **24 hours** | Initial acknowledgment of your report |
| **72 hours** | Preliminary assessment and severity classification |
| **7 days** | Detailed response with our remediation plan |
| **30 days** | Target resolution for critical vulnerabilities |
| **90 days** | Target resolution for non-critical vulnerabilities |

### What to Expect

**If the vulnerability is accepted:**
- We will work with you to understand and reproduce the issue
- You will receive updates on our progress toward a fix
- We will credit you in our security advisory (unless you prefer to remain anonymous)
- For significant findings, we may offer a bug bounty (see below)
- We will coordinate disclosure timing with you

**If the vulnerability is declined:**
- We will provide a clear explanation of why we don't consider it a security issue
- We may suggest alternative reporting channels if appropriate
- You are free to disclose the issue publicly after our response

### Disclosure Policy

We follow **coordinated disclosure**:

- Please allow us 90 days to address the vulnerability before public disclosure
- We will work with you to agree on a disclosure timeline
- We will publish a security advisory when the fix is released
- We appreciate advance notice if you plan to publish research about the vulnerability

---

## Security Features

AquaChain implements multiple layers of security:

### Authentication & Authorization
- **AWS Cognito** for user authentication with MFA support
- **Role-Based Access Control (RBAC)** - Admin, Technician, Consumer roles
- **JWT tokens** with short expiration times
- **Session management** with automatic timeout

### Data Protection
- **Encryption at rest**: All data encrypted using AWS KMS
- **Encryption in transit**: TLS 1.2+ for all communications
- **MQTT over TLS**: Secure IoT device communication
- **X.509 certificates**: Per-device authentication for IoT devices

### API Security
- **API Gateway** with request throttling and rate limiting
- **AWS WAF** for protection against common web exploits
- **Input validation** on all API endpoints
- **CORS policies** properly configured

### Infrastructure Security
- **VPC isolation** for backend resources
- **Security groups** with least-privilege access
- **IAM roles** with minimal required permissions
- **CloudWatch monitoring** for suspicious activity
- **AWS GuardDuty** for threat detection

### IoT Security
- **Device provisioning** with unique certificates
- **Certificate rotation** every 90 days
- **Device shadow** for secure state management
- **IoT policies** with least-privilege access

### Compliance
- **GDPR compliant** with data export and deletion capabilities
- **Audit logging** with blockchain-inspired immutable logs
- **Data retention policies** configurable per regulation
- **Privacy by design** principles

---

## Security Best Practices

### For Developers

1. **Never commit sensitive data**:
   ```bash
   # Before committing, check for secrets
   git secrets --scan
   grep -r "AKIA" . --exclude-dir={node_modules,venv,cdk.out}
   ```

2. **Use environment variables**:
   - Store secrets in `.env` files (never commit these)
   - Use AWS Secrets Manager for production secrets
   - Follow the `.env.example` template

3. **Keep dependencies updated**:
   ```bash
   # Check for vulnerabilities
   npm audit
   pip-audit
   
   # Update dependencies
   npm update
   pip install --upgrade -r requirements.txt
   ```

4. **Run security scans**:
   ```bash
   # SBOM generation
   npm run sbom
   
   # Security scanning
   scripts/security/scan-all.bat
   ```

### For Deployment

1. **Rotate credentials regularly**:
   - IoT certificates: Every 90 days
   - API keys: Monthly
   - Database credentials: Quarterly

2. **Enable monitoring**:
   - CloudWatch alarms for failed authentication attempts
   - GuardDuty for threat detection
   - CloudTrail for audit logging

3. **Apply least privilege**:
   - IAM roles with minimal permissions
   - Security groups with specific IP ranges
   - API Gateway resource policies

4. **Regular security audits**:
   - Quarterly penetration testing
   - Monthly dependency vulnerability scans
   - Weekly log reviews

### For IoT Devices

1. **Secure device provisioning**:
   - Use unique certificates per device
   - Store certificates securely on device
   - Never hardcode credentials in firmware

2. **Firmware updates**:
   - Implement OTA (Over-The-Air) updates
   - Sign firmware updates
   - Verify signatures before applying

3. **Network security**:
   - Use WPA2/WPA3 for WiFi
   - Disable unnecessary services
   - Implement device firewall rules

---

## Known Security Considerations

### Current Limitations

1. **Local Development Mode**:
   - Uses mock authentication (not for production)
   - Demo credentials are publicly known
   - No rate limiting in local mode

2. **IoT Simulator**:
   - Generates predictable device IDs
   - Should not be used with production credentials
   - For testing purposes only

3. **Cost Optimization Mode**:
   - May disable some security features (e.g., WAF)
   - Review security implications before enabling

### Mitigations

- Local development is isolated from production
- Clear documentation warns against production use
- Separate AWS accounts for dev/staging/production recommended

---

## Security Updates

### How We Handle Security Issues

1. **Assessment**: We evaluate severity using CVSS v3.1
2. **Development**: We develop and test a fix
3. **Testing**: We verify the fix doesn't introduce regressions
4. **Release**: We release a patch version
5. **Notification**: We notify users via:
   - GitHub Security Advisory
   - Release notes
   - Email (for critical issues)

### Severity Levels

| Severity | CVSS Score | Response Time | Example |
|----------|------------|---------------|---------|
| **Critical** | 9.0-10.0 | 24-48 hours | Remote code execution |
| **High** | 7.0-8.9 | 7 days | Authentication bypass |
| **Medium** | 4.0-6.9 | 30 days | Information disclosure |
| **Low** | 0.1-3.9 | 90 days | Minor information leak |

### Subscribing to Security Updates

To receive security notifications:

1. **Watch this repository** on GitHub
2. **Enable security alerts** in your GitHub settings
3. **Subscribe to releases** for email notifications
4. **Follow our security advisories** at github.com/yourusername/aquachain/security/advisories

---

## Bug Bounty Program

We appreciate security researchers who help us maintain a secure system.

### Scope

**In Scope:**
- Authentication and authorization vulnerabilities
- Data exposure or leakage
- Injection vulnerabilities (SQL, NoSQL, Command, etc.)
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Server-Side Request Forgery (SSRF)
- IoT device security issues
- API security vulnerabilities
- Infrastructure misconfigurations

**Out of Scope:**
- Social engineering attacks
- Physical attacks
- Denial of Service (DoS) attacks
- Issues in third-party dependencies (report to the vendor)
- Issues in local development mode
- Known issues already documented

### Rewards

While we don't currently offer monetary rewards, we provide:

- **Public acknowledgment** in our security hall of fame
- **Detailed credit** in security advisories
- **Swag and merchandise** for significant findings
- **Direct communication** with our security team
- **Early access** to new features

We may introduce a paid bug bounty program in the future.

### Rules

- Do not access or modify user data without permission
- Do not perform attacks that could harm system availability
- Do not publicly disclose vulnerabilities before we've had time to fix them
- Respect user privacy and data protection laws
- Only test against your own accounts or test environments

---

## Security Contact

For security-related inquiries:

- **Security Team**: security@aquachain.com
- **General Contact**: contactaquachain@gmail.com
- **Response Time**: Within 24 hours for security issues

For non-security issues, please use:
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community support

---

## Additional Resources

- **[Security Best Practices](DOCS/reports/PROJECT_REPORT.md#appendix-l-security--compliance)** - Detailed security guide
- **[AWS Security](https://aws.amazon.com/security/)** - AWS security documentation
- **[OWASP Top 10](https://owasp.org/www-project-top-ten/)** - Common web vulnerabilities
- **[IoT Security Foundation](https://www.iotsecurityfoundation.org/)** - IoT security best practices

---

## Policy Updates

This security policy is reviewed and updated quarterly. Last updated: **November 10, 2025**

Changes to this policy will be announced via:
- GitHub commit history
- Release notes
- Security advisories (for significant changes)

---

## Acknowledgments

We thank the following security researchers for their responsible disclosure:

*No vulnerabilities reported yet. Be the first to help us improve security!*

---

**Thank you for helping keep AquaChain and our users safe!**

For questions about this policy, contact: contact.aquachain@gmail.com
