# Consent Management Quick Reference

## Overview

Quick reference for using the consent management system in the AquaChain platform.

## Consent Types

| Type | Description | Required | Use Case |
|------|-------------|----------|----------|
| `data_processing` | Essential data processing | ✅ Yes | Core platform functionality |
| `marketing` | Marketing communications | ❌ No | Promotional emails, newsletters |
| `analytics` | Usage analytics | ❌ No | Behavior tracking, performance metrics |
| `third_party_sharing` | Third-party data sharing | ❌ No | Research partners, industry insights |

## Quick Start

### Check Consent (Python)

```python
from shared.consent_checker import check_marketing_consent

# Check if user has granted marketing consent
if check_marketing_consent(user_id):
    send_marketing_email(user_id, content)
else:
    logger.info(f"Skipping marketing email - no consent")
```

### Require Consent (Python Decorator)

```python
from shared.consent_checker import require_marketing_consent

@require_marketing_consent
def send_promotional_email(user_id: str, message: str):
    # This only executes if user has granted marketing consent
    send_email(user_id, message)
```

### Frontend API Calls (TypeScript)

```typescript
import { gdprService } from '../services/gdprService';

// Get all consents
const consents = await gdprService.getUserConsents();

// Update single consent
await gdprService.updateConsent('marketing', true);

// Bulk update
await gdprService.bulkUpdateConsents({
  marketing: true,
  analytics: false
});

// Check specific consent
const hasConsent = await gdprService.checkConsent('marketing');
```

## Common Patterns

### Pattern 1: Conditional Processing

```python
def process_user_data(user_id: str, data: dict):
    # Check consent before processing
    if not check_analytics_consent(user_id):
        logger.info("Analytics skipped - no consent")
        return
    
    # Process analytics
    track_user_behavior(user_id, data)
```

### Pattern 2: Try-Catch with Decorator

```python
from shared.errors import AuthorizationError

@require_marketing_consent
def send_newsletter(user_id: str, content: dict):
    send_email(user_id, content)

# Usage
try:
    send_newsletter(user_id, newsletter_content)
except AuthorizationError:
    logger.info("Newsletter not sent - no consent")
```

### Pattern 3: Multiple Consent Checks

```python
def share_data_with_partner(user_id: str, partner_id: str, data: dict):
    # Check both analytics and third-party consent
    if not check_analytics_consent(user_id):
        return False
    
    if not check_third_party_consent(user_id):
        return False
    
    # Proceed with sharing
    share_anonymized_data(partner_id, data)
    return True
```

## API Endpoints

### Get All Consents
```bash
GET /api/gdpr/consents
Authorization: Bearer <token>
```

### Update Single Consent
```bash
POST /api/gdpr/consents
Authorization: Bearer <token>
Content-Type: application/json

{
  "consent_type": "marketing",
  "granted": true
}
```

### Bulk Update Consents
```bash
POST /api/gdpr/consents/bulk
Authorization: Bearer <token>
Content-Type: application/json

{
  "consents": {
    "marketing": true,
    "analytics": false,
    "third_party_sharing": false
  }
}
```

### Check Specific Consent
```bash
GET /api/gdpr/consents/check?consent_type=marketing
Authorization: Bearer <token>
```

### Get Consent History
```bash
GET /api/gdpr/consents/history
Authorization: Bearer <token>

# Optional: Filter by consent type
GET /api/gdpr/consents/history?consent_type=marketing
```

## Helper Functions

### All Available Functions

```python
# Direct checks
from shared.consent_checker import (
    check_data_processing_consent,
    check_marketing_consent,
    check_analytics_consent,
    check_third_party_consent
)

# Decorators
from shared.consent_checker import (
    require_data_processing_consent,
    require_marketing_consent,
    require_analytics_consent,
    require_third_party_consent
)

# ConsentChecker class
from shared.consent_checker import ConsentChecker
checker = ConsentChecker()
```

### Analytics Tracker

```python
from shared.analytics_tracker import analytics_tracker

# Track event (automatically checks consent)
analytics_tracker.track_event(
    user_id='user-123',
    event_type='page_view',
    event_data={'page': '/dashboard'}
)

# Track page view
analytics_tracker.track_page_view(
    user_id='user-123',
    page_path='/dashboard',
    duration_ms=5000
)

# Track feature usage
analytics_tracker.track_feature_usage(
    user_id='user-123',
    feature_name='data_export',
    action='click'
)
```

### Third-Party Integration

```python
from shared.third_party_integration import third_party_integration

# Share data (automatically checks consent)
shared = third_party_integration.share_anonymized_data(
    user_id='user-123',
    partner_id='partner-456',
    data={'insights': 'data'},
    purpose='research'
)

# Get sharing history
history = third_party_integration.get_sharing_history('user-123')
```

## Environment Variables

```bash
# Required for Lambda functions
USER_CONSENTS_TABLE=aquachain-user-consents-dev
```

## Error Handling

### Authorization Error

```python
from shared.errors import AuthorizationError

try:
    send_marketing_email(user_id, content)
except AuthorizationError as e:
    if e.error_code == 'CONSENT_NOT_GRANTED':
        # Handle no consent
        return {'status': 'skipped'}
    raise
```

### Validation Error

```python
from shared.errors import ValidationError

try:
    consent_service.update_consent(user_id, 'invalid_type', True, {})
except ValidationError as e:
    # Handle invalid consent type
    logger.error(f"Invalid consent type: {e.message}")
```

## Logging

All consent operations are logged with structured logging:

```json
{
  "timestamp": "2025-10-25T12:00:00Z",
  "level": "info",
  "message": "Consent check completed",
  "user_id": "user-123",
  "consent_type": "marketing",
  "granted": false
}
```

## Best Practices

### ✅ DO

- Check consent before non-essential operations
- Log when consent is not granted
- Use appropriate consent type for each operation
- Handle authorization errors gracefully
- Default to deny on errors

### ❌ DON'T

- Block essential functionality with optional consent
- Send marketing emails without checking consent
- Track analytics without checking consent
- Share data with third parties without consent
- Ignore consent check failures

## Testing

### Unit Test Example

```python
from moto import mock_dynamodb
from shared.consent_checker import ConsentChecker

@mock_dynamodb
def test_consent_check():
    checker = ConsentChecker()
    
    # Setup consent
    setup_test_consent('user-123', 'marketing', True)
    
    # Test check
    assert checker.check_consent('user-123', 'marketing') == True
```

### Integration Test Example

```python
def test_marketing_email_workflow():
    # Grant consent
    consent_service.update_consent('user-123', 'marketing', True, {})
    
    # Send email
    result = send_marketing_email('user-123', content)
    
    # Verify
    assert result['status'] == 'sent'
```

## Troubleshooting

### Issue: Consent check always returns False

**Solution:** Check that:
1. User has a consent record in DynamoDB
2. Environment variable `USER_CONSENTS_TABLE` is set correctly
3. Lambda has permissions to read from UserConsents table

### Issue: Authorization error when using decorator

**Solution:** Ensure the first parameter of the decorated function is `user_id`:

```python
# ✅ Correct
@require_marketing_consent
def my_function(user_id: str, other_param: str):
    pass

# ❌ Wrong - user_id not first parameter
@require_marketing_consent
def my_function(other_param: str, user_id: str):
    pass
```

### Issue: Consent UI not loading

**Solution:** Check that:
1. API endpoints are configured correctly
2. Authentication token is valid
3. CORS is configured for API Gateway
4. Frontend environment variables are set

## Support

For detailed documentation, see:
- `lambda/gdpr_service/CONSENT_INTEGRATION_GUIDE.md` - Full integration guide
- `TASK_17_CONSENT_MANAGEMENT_IMPLEMENTATION.md` - Implementation details
- `lambda/gdpr_service/consent_service.py` - Service implementation
- `lambda/shared/consent_checker.py` - Consent checker implementation

## Quick Links

- [Frontend Component](frontend/src/components/Privacy/ConsentManagementPanel.tsx)
- [Backend Service](lambda/gdpr_service/consent_service.py)
- [Consent Checker](lambda/shared/consent_checker.py)
- [Integration Guide](lambda/gdpr_service/CONSENT_INTEGRATION_GUIDE.md)
