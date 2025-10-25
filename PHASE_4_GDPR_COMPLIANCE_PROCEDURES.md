# Phase 4 GDPR Compliance Procedures

## Overview

This document outlines the procedures for GDPR (General Data Protection Regulation) compliance in the AquaChain IoT water quality monitoring system. It provides operational guidance for handling data subject requests, managing consent, and maintaining compliance.

## Table of Contents

1. [GDPR Principles](#gdpr-principles)
2. [Data Subject Rights](#data-subject-rights)
3. [Data Export Procedures](#data-export-procedures)
4. [Data Deletion Procedures](#data-deletion-procedures)
5. [Consent Management](#consent-management)
6. [Data Breach Response](#data-breach-response)
7. [Compliance Verification](#compliance-verification)

---

## GDPR Principles

### Core Principles

The AquaChain system adheres to the following GDPR principles:

1. **Lawfulness, Fairness, and Transparency**: Data processing is lawful, fair, and transparent to data subjects
2. **Purpose Limitation**: Data is collected for specified, explicit, and legitimate purposes
3. **Data Minimization**: Only necessary data is collected and processed
4. **Accuracy**: Personal data is accurate and kept up to date
5. **Storage Limitation**: Data is kept only as long as necessary
6. **Integrity and Confidentiality**: Data is processed securely
7. **Accountability**: We can demonstrate compliance with GDPR

### Legal Basis for Processing

| Processing Activity | Legal Basis | Documentation |
|---------------------|-------------|---------------|
| User account management | Contract | Terms of Service |
| Device monitoring | Contract | Service Agreement |
| Marketing communications | Consent | Consent records in UserConsents table |
| Analytics | Legitimate interest | Privacy Policy |
| Third-party integrations | Consent | Consent records in UserConsents table |

---

## Data Subject Rights

### Right to Access (Article 15)

**What**: Data subjects can request a copy of their personal data.

**Timeline**: Respond within 30 days (extendable by 2 months if complex).

**Process**: See [Data Export Procedures](#data-export-procedures).

### Right to Rectification (Article 16)

**What**: Data subjects can request correction of inaccurate personal data.

**Timeline**: Respond within 30 days.

**Process**:
1. User submits correction request via Privacy Settings
2. Verify user identity
3. Update data in relevant tables
4. Notify user of completion
5. Log action in audit trail

### Right to Erasure (Article 17)

**What**: Data subjects can request deletion of their personal data ("right to be forgotten").

**Timeline**: Respond within 30 days.

**Process**: See [Data Deletion Procedures](#data-deletion-procedures).

### Right to Restrict Processing (Article 18)

**What**: Data subjects can request restriction of processing in certain circumstances.

**Timeline**: Respond within 30 days.

**Process**:
1. User submits restriction request
2. Verify user identity
3. Mark account as "restricted" in Users table
4. Suspend non-essential processing
5. Notify user of completion
6. Log action in audit trail

### Right to Data Portability (Article 20)

**What**: Data subjects can receive their data in a structured, machine-readable format.

**Timeline**: Respond within 30 days.

**Process**: Same as data export, but format must be machine-readable (JSON).

### Right to Object (Article 21)

**What**: Data subjects can object to processing based on legitimate interests or for direct marketing.

**Timeline**: Respond immediately for marketing; within 30 days for other objections.

**Process**:
1. User submits objection via Privacy Settings
2. Verify user identity
3. Update consent settings in UserConsents table
4. Stop relevant processing activities
5. Notify user of completion
6. Log action in audit trail

---

## Data Export Procedures

### Overview

Data exports provide users with a complete copy of their personal data in JSON format.

### Request Process

#### 1. User Initiates Request

**Location**: Privacy Settings page → "Request Data Export" button

**User Action**:
```
1. Navigate to Privacy Settings
2. Click "Request Data Export"
3. Confirm request in dialog
4. Receive confirmation message
```

#### 2. System Processing

**Backend Flow**:

```python
# lambda/gdpr_service/export_handler.py

def lambda_handler(event, context):
    """Handle data export request"""
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    # Create GDPR request record
    gdpr_request = {
        'request_id': str(uuid.uuid4()),
        'user_id': user_id,
        'request_type': 'EXPORT',
        'status': 'PENDING',
        'created_at': datetime.utcnow().isoformat(),
        'processing_deadline': (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    gdpr_requests_table.put_item(Item=gdpr_request)
    
    # Trigger async export process
    export_service = DataExportService()
    export_url = export_service.export_user_data(user_id)
    
    # Update request status
    gdpr_requests_table.update_item(
        Key={'request_id': gdpr_request['request_id']},
        UpdateExpression='SET #status = :status, export_url = :url, completed_at = :completed',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'COMPLETED',
            ':url': export_url,
            ':completed': datetime.utcnow().isoformat()
        }
    )
    
    return {'statusCode': 200, 'body': json.dumps({'request_id': gdpr_request['request_id']})}
```

#### 3. Data Collection

**Data Sources**:

| Table | Data Collected | PII Fields |
|-------|----------------|------------|
| Users | Profile information | email, name, phone |
| Devices | Device registrations | device_name, location |
| SensorReadings | Historical readings | location (if present) |
| Alerts | Alert history | None |
| AuditLogs | User actions | ip_address, user_agent |
| UserConsents | Consent history | ip_address, user_agent |
| GDPRRequests | Previous requests | None |

**Export Format**:

```json
{
  "export_date": "2025-10-25T10:30:00Z",
  "user_id": "user-123",
  "profile": {
    "user_id": "user-123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "consumer",
    "created_at": "2024-01-15T08:00:00Z"
  },
  "devices": [
    {
      "device_id": "device-456",
      "name": "Home Water Monitor",
      "status": "active",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "created_at": "2024-02-01T10:00:00Z"
    }
  ],
  "sensor_readings": [
    {
      "device_id": "device-456",
      "timestamp": "2025-10-25T09:00:00Z",
      "metrics": {
        "ph": 7.2,
        "temperature": 20.5,
        "turbidity": 3.2
      }
    }
  ],
  "alerts": [],
  "audit_logs": [],
  "consents": []
}
```

#### 4. Secure Storage

**S3 Bucket Configuration**:
- Bucket: `aquachain-gdpr-exports-{region}`
- Encryption: AES-256
- Access: Private (presigned URLs only)
- Lifecycle: Delete after 30 days

**File Naming**:
```
gdpr-exports/{user_id}/{timestamp}.json
```

#### 5. User Notification

**Email Template**:

```
Subject: Your Data Export is Ready

Dear [User Name],

Your data export request has been completed. You can download your data using the link below:

[Download Link]

This link will expire in 7 days. The export includes all personal data we hold about you in JSON format.

If you have any questions, please contact our privacy team at privacy@aquachain.com.

Best regards,
AquaChain Privacy Team
```

**Frontend Display**:
```typescript
// Show download link in Privacy Settings
<div className="export-status">
  <p>Your data export is ready!</p>
  <a href={exportUrl} download>Download Export</a>
  <p>Link expires: {expirationDate}</p>
</div>
```

### Timeline

| Stage | Duration | SLA |
|-------|----------|-----|
| Request submission | Immediate | N/A |
| Data collection | 5-30 minutes | 1 hour |
| File generation | 1-5 minutes | 15 minutes |
| User notification | Immediate | 5 minutes |
| **Total** | **< 1 hour** | **48 hours** |

### Monitoring

**Metrics to Track**:
- Export request volume
- Processing time
- Success/failure rate
- Download rate

**Alerts**:
- Export processing exceeds 1 hour
- Export failure rate > 5%
- Approaching 48-hour SLA

---

## Data Deletion Procedures

### Overview

Data deletion permanently removes all user data from the system in compliance with GDPR Article 17 (Right to Erasure).

### Request Process

#### 1. User Initiates Request

**Location**: Privacy Settings page → "Delete My Account" button

**User Action**:
```
1. Navigate to Privacy Settings
2. Click "Delete My Account"
3. Read warning about permanent deletion
4. Type "DELETE" to confirm
5. Click "Confirm Deletion"
6. Receive confirmation message
```

**Warning Message**:
```
⚠️ WARNING: Account Deletion

This action will permanently delete:
- Your user profile
- All registered devices
- All sensor readings
- All alerts and notifications
- All personal data

This action cannot be undone.

Processing will begin immediately and complete within 30 days.

Type "DELETE" to confirm.
```

#### 2. System Processing

**Backend Flow**:

```python
# lambda/gdpr_service/deletion_handler.py

def lambda_handler(event, context):
    """Handle data deletion request"""
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    # Create GDPR request record
    gdpr_request = {
        'request_id': str(uuid.uuid4()),
        'user_id': user_id,
        'request_type': 'DELETION',
        'status': 'PENDING',
        'created_at': datetime.utcnow().isoformat(),
        'processing_deadline': (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    gdpr_requests_table.put_item(Item=gdpr_request)
    
    # Trigger async deletion process
    deletion_service = DataDeletionService()
    deletion_summary = deletion_service.delete_user_data(user_id)
    
    # Update request status
    gdpr_requests_table.update_item(
        Key={'request_id': gdpr_request['request_id']},
        UpdateExpression='SET #status = :status, deletion_summary = :summary, completed_at = :completed',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'COMPLETED',
            ':summary': deletion_summary,
            ':completed': datetime.utcnow().isoformat()
        }
    )
    
    return {'statusCode': 200, 'body': json.dumps({'request_id': gdpr_request['request_id']})}
```

#### 3. Data Deletion

**Deletion Order** (to maintain referential integrity):

1. **SensorReadings**: Delete all readings for user's devices
2. **Alerts**: Delete all alerts for user's devices
3. **Devices**: Delete all user's devices
4. **UserConsents**: Delete consent records
5. **GDPRRequests**: Keep for compliance (anonymized)
6. **AuditLogs**: Anonymize (cannot delete for compliance)
7. **Users**: Delete user profile
8. **Cognito**: Delete authentication account

**Anonymization vs Deletion**:

| Data Type | Action | Reason |
|-----------|--------|--------|
| User profile | DELETE | No legal requirement to retain |
| Devices | DELETE | No legal requirement to retain |
| Sensor readings | DELETE | No legal requirement to retain |
| Audit logs | ANONYMIZE | Legal requirement to retain for 7 years |
| GDPR requests | ANONYMIZE | Compliance documentation |

**Anonymization Process**:

```python
def anonymize_audit_logs(user_id: str):
    """Anonymize audit logs while preserving compliance data"""
    
    # Replace PII with anonymized values
    audit_logs_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET user_id = :anon_id, email = :anon_email, ip_address = :anon_ip',
        ExpressionAttributeValues={
            ':anon_id': f'DELETED_USER_{uuid.uuid4().hex[:8]}',
            ':anon_email': 'deleted@anonymized.local',
            ':anon_ip': '0.0.0.0'
        }
    )
```

#### 4. Deletion Summary

**Summary Format**:

```json
{
  "user_id": "user-123",
  "deletion_date": "2025-10-25T10:30:00Z",
  "deleted_items": {
    "profile": 1,
    "devices": 3,
    "sensor_readings": 15420,
    "alerts": 47,
    "consents": 4
  },
  "anonymized_items": {
    "audit_logs": 234,
    "gdpr_requests": 2
  },
  "cognito_deleted": true
}
```

#### 5. User Notification

**Email Template**:

```
Subject: Your Account Has Been Deleted

Dear Former User,

Your account deletion request has been completed. All your personal data has been permanently deleted from our systems.

Deletion Summary:
- User profile: Deleted
- Devices: 3 deleted
- Sensor readings: 15,420 deleted
- Audit logs: Anonymized (retained for compliance)

If you did not request this deletion, please contact us immediately at privacy@aquachain.com.

Best regards,
AquaChain Privacy Team
```

### Timeline

| Stage | Duration | SLA |
|-------|----------|-----|
| Request submission | Immediate | N/A |
| Data deletion | 5-30 minutes | 1 hour |
| Cognito deletion | 1-5 minutes | 15 minutes |
| User notification | Immediate | 5 minutes |
| **Total** | **< 1 hour** | **30 days** |

### Special Cases

#### Active Subscriptions

If user has active paid subscription:
1. Cancel subscription first
2. Process refund if applicable
3. Wait for billing cycle to complete
4. Then proceed with deletion

#### Legal Hold

If user data is under legal hold:
1. Deny deletion request
2. Notify user of legal hold
3. Provide contact information for legal team
4. Document denial in audit log

#### Shared Data

If user has shared devices with other users:
1. Remove user from shared device access
2. Transfer ownership if user is owner
3. Notify other users of ownership change
4. Then proceed with deletion

---

## Consent Management

### Consent Types

The system tracks four types of consent:

| Consent Type | Purpose | Required | Default |
|--------------|---------|----------|---------|
| `data_processing` | Core service functionality | Yes | Granted |
| `marketing` | Marketing communications | No | Not granted |
| `analytics` | Usage analytics | No | Not granted |
| `third_party` | Third-party integrations | No | Not granted |

### Consent Collection

**Initial Consent** (during registration):

```typescript
// frontend/src/pages/Registration.tsx
<ConsentForm>
  <ConsentCheckbox
    type="data_processing"
    required={true}
    label="I agree to data processing for service functionality"
  />
  <ConsentCheckbox
    type="marketing"
    required={false}
    label="I agree to receive marketing communications"
  />
  <ConsentCheckbox
    type="analytics"
    required={false}
    label="I agree to usage analytics"
  />
  <ConsentCheckbox
    type="third_party"
    required={false}
    label="I agree to third-party integrations"
  />
</ConsentForm>
```

**Consent Storage**:

```python
# lambda/gdpr_service/consent_service.py

def record_consent(user_id: str, consent_type: str, granted: bool, metadata: Dict):
    """Record consent with full audit trail"""
    
    consent_record = {
        'user_id': user_id,
        'consent_type': consent_type,
        'granted': granted,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': metadata.get('ip_address'),
        'user_agent': metadata.get('user_agent'),
        'consent_version': '1.0'
    }
    
    user_consents_table.put_item(Item=consent_record)
    
    # Log in audit trail
    audit_logger.log_action(
        user_id=user_id,
        action_type='CONSENT_UPDATE',
        resource_type='consent',
        resource_id=consent_type,
        details={'granted': granted}
    )
```

### Consent Enforcement

**Check consent before processing**:

```python
from lambda.shared.consent_checker import ConsentChecker

consent_checker = ConsentChecker()

def send_marketing_email(user_id: str, email_content: str):
    """Send marketing email only if user has consented"""
    
    # Check consent
    if not consent_checker.check_consent(user_id, 'marketing'):
        logger.info(
            'Marketing email blocked - no consent',
            user_id=user_id
        )
        return {'status': 'blocked', 'reason': 'no_consent'}
    
    # Send email
    ses.send_email(...)
    
    return {'status': 'sent'}
```

### Consent Withdrawal

**User Action**:
```
1. Navigate to Privacy Settings → Consent Management
2. Toggle consent switches
3. Click "Save Changes"
4. Receive confirmation
```

**Backend Processing**:

```python
def update_consent(user_id: str, consent_type: str, granted: bool):
    """Update consent and enforce immediately"""
    
    # Update consent record
    record_consent(user_id, consent_type, granted, get_request_metadata())
    
    # Immediate enforcement
    if not granted:
        if consent_type == 'marketing':
            # Unsubscribe from marketing lists
            unsubscribe_from_marketing(user_id)
        elif consent_type == 'analytics':
            # Stop analytics tracking
            disable_analytics(user_id)
        elif consent_type == 'third_party':
            # Revoke third-party access
            revoke_third_party_access(user_id)
```

---

## Data Breach Response

### Breach Detection

**Indicators**:
- Unauthorized access to S3 buckets
- Unusual database query patterns
- Failed authentication attempts spike
- CloudWatch security alarms

### Response Procedure

#### 1. Immediate Actions (0-1 hour)

1. **Contain the breach**:
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable additional security controls

2. **Assess the scope**:
   - Identify affected data
   - Determine number of affected users
   - Document timeline of breach

3. **Notify incident response team**:
   - Security team
   - Legal team
   - Privacy officer
   - Executive management

#### 2. Investigation (1-24 hours)

1. **Forensic analysis**:
   - Review audit logs
   - Analyze access patterns
   - Identify attack vector
   - Preserve evidence

2. **Impact assessment**:
   - Categorize data types affected
   - Assess risk to data subjects
   - Determine if PII was compromised

#### 3. Notification (24-72 hours)

**Supervisory Authority** (if high risk):
- Notify within 72 hours of becoming aware
- Provide breach details
- Describe likely consequences
- Outline remediation measures

**Data Subjects** (if high risk to rights and freedoms):
- Notify without undue delay
- Use clear and plain language
- Provide contact information
- Describe remediation measures

**Notification Template**:

```
Subject: Important Security Notice

Dear [User Name],

We are writing to inform you of a security incident that may have affected your personal data.

What Happened:
[Description of incident]

What Data Was Affected:
[List of data types]

What We're Doing:
[Remediation measures]

What You Should Do:
[Recommended actions]

For more information, please contact our privacy team at privacy@aquachain.com.

We sincerely apologize for this incident.

Best regards,
AquaChain Security Team
```

#### 4. Remediation (Ongoing)

1. **Fix vulnerabilities**
2. **Enhance security controls**
3. **Update incident response plan**
4. **Conduct security training**
5. **Monitor for further incidents**

---

## Compliance Verification

### Regular Audits

**Monthly**:
- Review GDPR request metrics
- Check response times
- Verify consent records
- Review audit logs

**Quarterly**:
- Data protection impact assessment
- Security controls review
- Privacy policy review
- Staff training

**Annually**:
- Full GDPR compliance audit
- Third-party security assessment
- Data retention review
- Incident response drill

### Compliance Checklist

- [ ] Privacy policy is up to date
- [ ] Consent mechanisms are working
- [ ] Data subject rights are honored
- [ ] Audit logs are complete
- [ ] Data retention policies are enforced
- [ ] Security controls are effective
- [ ] Staff are trained on GDPR
- [ ] Incident response plan is tested
- [ ] Third-party processors are compliant
- [ ] Data protection officer is appointed

### Documentation

**Required Records**:
- Processing activities register
- Data protection impact assessments
- Consent records
- Data breach incidents
- GDPR request logs
- Security incident reports
- Staff training records

**Retention**:
- Audit logs: 7 years
- GDPR requests: 7 years
- Consent records: 7 years after withdrawal
- Breach reports: Indefinitely

---

## Contact Information

**Data Protection Officer**:
- Email: dpo@aquachain.com
- Phone: [Phone Number]

**Privacy Team**:
- Email: privacy@aquachain.com
- Response time: 24 hours

**Security Team**:
- Email: security@aquachain.com
- Emergency: [Emergency Number]

---

**Document Version**: 1.0  
**Last Updated**: Phase 4 Implementation  
**Owner**: Privacy and Compliance Team  
**Review Cycle**: Quarterly
