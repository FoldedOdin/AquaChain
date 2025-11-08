# Consent Management Integration Guide

This guide explains how to integrate consent checks into Lambda functions and services.

## Overview

The consent management system ensures that user data is only processed when users have granted appropriate consent. This is required for GDPR compliance.

## Consent Types

The system supports four types of consent:

1. **data_processing** - Essential data processing (required for platform use)
2. **marketing** - Marketing communications and promotional emails
3. **analytics** - Usage analytics and behavior tracking
4. **third_party_sharing** - Sharing anonymized data with partners

## Using Consent Checks

### Method 1: Direct Consent Check

Use this method when you need to conditionally execute code based on consent:

```python
from shared.consent_checker import check_marketing_consent

def send_promotional_email(user_id: str, message: str):
    # Check if user has granted marketing consent
    if not check_marketing_consent(user_id):
        logger.info(f"Skipping marketing email for user {user_id} - no consent")
        return False
    
    # Proceed with sending email
    send_email(user_id, message)
    return True
```

### Method 2: Decorator-Based Consent Check

Use decorators to automatically enforce consent requirements:

```python
from shared.consent_checker import require_marketing_consent

@require_marketing_consent
def send_promotional_email(user_id: str, message: str):
    # This function will only execute if user has granted marketing consent
    # Otherwise, an AuthorizationError will be raised
    send_email(user_id, message)
```

## Integration Examples

### Example 1: Marketing Communications

```python
from shared.consent_checker import check_marketing_consent

def send_newsletter(user_id: str, newsletter_content: dict):
    """Send newsletter only to users who have consented to marketing."""
    
    # Check marketing consent
    if not check_marketing_consent(user_id):
        logger.info(f"User {user_id} has not consented to marketing")
        return {
            'status': 'skipped',
            'reason': 'no_marketing_consent'
        }
    
    # Send newsletter
    result = email_service.send(user_id, newsletter_content)
    
    return {
        'status': 'sent',
        'message_id': result['message_id']
    }
```

### Example 2: Analytics Tracking

```python
from shared.analytics_tracker import analytics_tracker

def track_user_behavior(user_id: str, event_type: str, event_data: dict):
    """Track user behavior with automatic consent check."""
    
    # The analytics_tracker automatically checks consent
    tracked = analytics_tracker.track_event(
        user_id=user_id,
        event_type=event_type,
        event_data=event_data
    )
    
    if tracked:
        logger.info(f"Event tracked for user {user_id}")
    else:
        logger.info(f"Event not tracked - user {user_id} has not consented to analytics")
```

### Example 3: Third-Party Data Sharing

```python
from shared.third_party_integration import third_party_integration

def share_insights_with_partner(user_id: str, partner_id: str, insights: dict):
    """Share anonymized insights with partner if user has consented."""
    
    # Check third-party sharing consent
    shared = third_party_integration.share_anonymized_data(
        user_id=user_id,
        partner_id=partner_id,
        data=insights,
        purpose='research'
    )
    
    if shared:
        logger.info(f"Data shared with partner {partner_id}")
    else:
        logger.info(f"Data not shared - user {user_id} has not consented")
```

### Example 4: Data Processing (Essential)

```python
from shared.consent_checker import check_data_processing_consent

def process_sensor_data(user_id: str, device_id: str, readings: dict):
    """Process sensor data (essential functionality)."""
    
    # Check essential data processing consent
    # Note: This should always be granted for active users
    if not check_data_processing_consent(user_id):
        logger.error(f"User {user_id} has not granted essential data processing consent")
        raise AuthorizationError(
            "Essential data processing consent required",
            "CONSENT_NOT_GRANTED"
        )
    
    # Process the data
    result = process_readings(device_id, readings)
    return result
```

## Available Functions

### Direct Check Functions

```python
from shared.consent_checker import (
    check_data_processing_consent,
    check_marketing_consent,
    check_analytics_consent,
    check_third_party_consent
)

# Check specific consent
has_consent = check_marketing_consent(user_id)
```

### Decorator Functions

```python
from shared.consent_checker import (
    require_data_processing_consent,
    require_marketing_consent,
    require_analytics_consent,
    require_third_party_consent
)

@require_marketing_consent
def my_function(user_id: str):
    # Function implementation
    pass
```

### ConsentChecker Class

```python
from shared.consent_checker import ConsentChecker

checker = ConsentChecker()

# Check any consent type
has_consent = checker.check_consent(user_id, 'marketing')

# Use as decorator
@checker.require_consent('marketing', 'Custom error message')
def my_function(user_id: str):
    # Function implementation
    pass
```

## Best Practices

### 1. Always Check Consent for Non-Essential Operations

```python
# ✅ Good - Check consent before marketing email
if check_marketing_consent(user_id):
    send_marketing_email(user_id, content)

# ❌ Bad - Send marketing email without checking consent
send_marketing_email(user_id, content)
```

### 2. Log Consent Checks

```python
# ✅ Good - Log when consent is not granted
if not check_marketing_consent(user_id):
    logger.info(f"Marketing action skipped for user {user_id} - no consent")
    return

# ❌ Bad - Silently skip without logging
if not check_marketing_consent(user_id):
    return
```

### 3. Handle Consent Errors Gracefully

```python
# ✅ Good - Handle authorization errors
try:
    send_marketing_email(user_id, content)
except AuthorizationError as e:
    logger.warning(f"Consent not granted: {e.message}")
    return {'status': 'skipped', 'reason': 'no_consent'}

# ❌ Bad - Let errors propagate without handling
send_marketing_email(user_id, content)
```

### 4. Use Appropriate Consent Types

```python
# ✅ Good - Use correct consent type
if check_analytics_consent(user_id):
    track_page_view(user_id, page_path)

# ❌ Bad - Use wrong consent type
if check_marketing_consent(user_id):  # Wrong!
    track_page_view(user_id, page_path)
```

### 5. Don't Block Essential Functionality

```python
# ✅ Good - Essential operations don't require optional consent
def save_user_profile(user_id: str, profile_data: dict):
    # This is essential functionality, no optional consent check needed
    save_to_database(user_id, profile_data)

# ❌ Bad - Blocking essential functionality with optional consent
def save_user_profile(user_id: str, profile_data: dict):
    if not check_analytics_consent(user_id):  # Wrong!
        raise AuthorizationError("Cannot save profile")
    save_to_database(user_id, profile_data)
```

## Testing Consent Integration

### Unit Tests

```python
import pytest
from moto import mock_dynamodb
from shared.consent_checker import ConsentChecker

@mock_dynamodb
def test_marketing_consent_check():
    # Setup
    checker = ConsentChecker()
    user_id = 'test-user-123'
    
    # Test when consent is granted
    setup_consent(user_id, 'marketing', True)
    assert checker.check_consent(user_id, 'marketing') == True
    
    # Test when consent is not granted
    setup_consent(user_id, 'marketing', False)
    assert checker.check_consent(user_id, 'marketing') == False
```

### Integration Tests

```python
def test_marketing_email_with_consent():
    """Test that marketing emails are sent when consent is granted."""
    user_id = 'test-user-123'
    
    # Grant marketing consent
    consent_service.update_consent(user_id, 'marketing', True, {})
    
    # Send marketing email
    result = send_marketing_email(user_id, test_content)
    
    # Verify email was sent
    assert result['status'] == 'sent'

def test_marketing_email_without_consent():
    """Test that marketing emails are skipped when consent is not granted."""
    user_id = 'test-user-456'
    
    # Revoke marketing consent
    consent_service.update_consent(user_id, 'marketing', False, {})
    
    # Attempt to send marketing email
    result = send_marketing_email(user_id, test_content)
    
    # Verify email was skipped
    assert result['status'] == 'skipped'
    assert result['reason'] == 'no_marketing_consent'
```

## Environment Variables

Ensure the following environment variable is set in your Lambda function:

```bash
USER_CONSENTS_TABLE=aquachain-user-consents-dev
```

## Error Handling

When consent is not granted, the system will:

1. **Direct checks**: Return `False`
2. **Decorators**: Raise `AuthorizationError` with code `CONSENT_NOT_GRANTED`

Handle these appropriately in your code:

```python
from shared.errors import AuthorizationError

try:
    result = process_with_consent(user_id, data)
except AuthorizationError as e:
    if e.error_code == 'CONSENT_NOT_GRANTED':
        # Handle consent not granted
        return {'status': 'skipped', 'reason': 'no_consent'}
    raise
```

## Monitoring and Logging

All consent checks are logged with structured logging:

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

Monitor these logs to:
- Track consent check patterns
- Identify features affected by consent
- Ensure compliance with data processing rules

## Support

For questions or issues with consent integration:
- Review this guide
- Check the consent service implementation in `lambda/gdpr_service/consent_service.py`
- Review example integrations in `lambda/shared/analytics_tracker.py` and `lambda/shared/third_party_integration.py`
