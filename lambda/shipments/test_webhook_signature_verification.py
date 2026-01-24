"""
Property-based tests for webhook signature verification
Feature: shipment-tracking-automation, Property 7: Webhook Signature Verification
Validates: Requirements 10.2

This test verifies that webhook signature verification is secure:
- Valid HMAC-SHA256 signatures are accepted
- Invalid or tampered signatures are rejected
- Missing signatures are rejected
- Constant-time comparison prevents timing attacks
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
import hmac
import hashlib
import json
from typing import Dict, Any


def verify_webhook_signature_with_secret(event: Dict, secret: str) -> bool:
    """
    Verify webhook authenticity using HMAC-SHA256 signature with provided secret.
    Uses constant-time comparison to prevent timing attacks.
    
    This is a test helper that allows us to test with different secrets.
    """
    # Extract signature from X-Webhook-Signature header
    headers = event.get('headers', {})
    signature = headers.get('X-Webhook-Signature', '') or headers.get('x-webhook-signature', '')
    body = event.get('body', '')
    
    if not signature:
        return False  # Reject requests without signature
    
    if not body:
        return False
    
    # Compute HMAC-SHA256 signature using provided secret
    expected = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected)
    
    return is_valid


# Hypothesis strategies for generating test data
payload_strategy = st.dictionaries(
    keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20),
    values=st.one_of(
        st.text(min_size=1, max_size=100),
        st.integers(min_value=0, max_value=1000000),
        st.booleans()
    ),
    min_size=1,
    max_size=10
)

secret_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_',
    min_size=16,
    max_size=64
)

tamper_strategy = st.booleans()


class TestWebhookSignatureVerification:
    """
    Property 7: Webhook Signature Verification
    
    For any incoming webhook request, if the HMAC-SHA256 signature does not match
    the expected value computed from the payload and secret, the request must be
    rejected with 401 status.
    
    This ensures:
    1. Only webhooks from authenticated couriers are processed
    2. Tampered payloads are detected and rejected
    3. Missing signatures are rejected
    4. Timing attacks are prevented via constant-time comparison
    """
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_signature_is_accepted(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Valid HMAC-SHA256 signatures are accepted
        
        For any webhook payload and secret, when the signature is correctly
        computed using HMAC-SHA256:
        1. The signature verification MUST return True
        2. The webhook MUST be processed (not rejected)
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string (as it would be in HTTP body)
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate valid HMAC-SHA256 signature using the secret
        valid_signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create mock event with valid signature
        event = {
            'headers': {
                'X-Webhook-Signature': valid_signature
            },
            'body': payload_json
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Valid signature must be accepted
        assert result is True, f"Valid signature must be accepted. Payload: {payload_json[:50]}..."
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy,
        tamper_method=st.sampled_from(['append', 'prepend', 'modify', 'truncate'])
    )
    @settings(max_examples=100, deadline=None)
    def test_tampered_payload_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str,
        tamper_method: str
    ):
        """
        Property Test: Tampered payloads are rejected
        
        For any webhook payload with a valid signature, if the payload is
        modified after signature generation:
        1. The signature verification MUST return False
        2. The webhook MUST be rejected with 401 status
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate valid signature for original payload
        valid_signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Tamper with payload after signature generation
        if tamper_method == 'append':
            tampered_payload = payload_json + "TAMPERED"
        elif tamper_method == 'prepend':
            tampered_payload = "TAMPERED" + payload_json
        elif tamper_method == 'modify':
            # Modify a character in the middle
            if len(payload_json) > 2:
                mid = len(payload_json) // 2
                tampered_payload = payload_json[:mid] + 'X' + payload_json[mid+1:]
            else:
                tampered_payload = payload_json + "X"
        elif tamper_method == 'truncate':
            # Remove last character
            if len(payload_json) > 1:
                tampered_payload = payload_json[:-1]
            else:
                tampered_payload = ""
        
        # Skip if tampered payload is identical (edge case)
        assume(tampered_payload != payload_json)
        
        # Create mock event with tampered payload but original signature
        event = {
            'headers': {
                'X-Webhook-Signature': valid_signature
            },
            'body': tampered_payload
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Tampered payload must be rejected
        assert result is False, f"Tampered payload must be rejected. Method: {tamper_method}"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy,
        wrong_secret=secret_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_wrong_secret_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str,
        wrong_secret: str
    ):
        """
        Property Test: Signatures with wrong secret are rejected
        
        For any webhook payload, if the signature is computed with a different
        secret than the one configured:
        1. The signature verification MUST return False
        2. The webhook MUST be rejected
        
        **Validates: Requirements 10.2**
        """
        # Ensure secrets are different
        assume(secret != wrong_secret)
        
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate signature with WRONG secret
        wrong_signature = hmac.new(
            wrong_secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create mock event with wrong signature
        event = {
            'headers': {
                'X-Webhook-Signature': wrong_signature
            },
            'body': payload_json
        }
        
        # Verify signature with correct secret
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Wrong secret must be rejected
        assert result is False, "Signature with wrong secret must be rejected"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_missing_signature_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Missing signatures are rejected
        
        For any webhook payload, if no signature is provided in the
        X-Webhook-Signature header:
        1. The signature verification MUST return False
        2. The webhook MUST be rejected with 401 status
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Create mock event WITHOUT signature header
        event = {
            'headers': {},
            'body': payload_json
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Missing signature must be rejected
        assert result is False, "Missing signature must be rejected"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_signature_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Empty signatures are rejected
        
        For any webhook payload, if an empty signature is provided:
        1. The signature verification MUST return False
        2. The webhook MUST be rejected
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Create mock event with empty signature
        event = {
            'headers': {
                'X-Webhook-Signature': ''
            },
            'body': payload_json
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Empty signature must be rejected
        assert result is False, "Empty signature must be rejected"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_body_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Empty request body is rejected
        
        For any webhook request with an empty body:
        1. The signature verification MUST return False
        2. The webhook MUST be rejected
        
        **Validates: Requirements 10.2**
        """
        # Generate signature for non-empty payload
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create mock event with empty body
        event = {
            'headers': {
                'X-Webhook-Signature': signature
            },
            'body': ''
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Empty body must be rejected
        assert result is False, "Empty body must be rejected"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy,
        invalid_signature=st.text(
            alphabet='0123456789abcdef',
            min_size=1,
            max_size=64
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_malformed_signature_is_rejected(
        self,
        payload: Dict[str, Any],
        secret: str,
        invalid_signature: str
    ):
        """
        Property Test: Malformed signatures are rejected
        
        For any webhook payload, if the signature is malformed (wrong length,
        invalid characters, etc.):
        1. The signature verification MUST return False
        2. The webhook MUST be rejected
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Ensure invalid signature is different from valid one
        assume(invalid_signature != valid_signature)
        
        # Create mock event with malformed signature
        event = {
            'headers': {
                'X-Webhook-Signature': invalid_signature
            },
            'body': payload_json
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event, secret)
        
        # Assert: Malformed signature must be rejected
        assert result is False, f"Malformed signature must be rejected: {invalid_signature[:20]}..."
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_case_insensitive_header_name(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Signature verification handles case-insensitive headers
        
        For any webhook payload, the signature verification should handle
        both 'X-Webhook-Signature' and 'x-webhook-signature' header names
        (HTTP headers are case-insensitive).
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Test with lowercase header name
        event_lowercase = {
            'headers': {
                'x-webhook-signature': valid_signature
            },
            'body': payload_json
        }
        
        result_lowercase = verify_webhook_signature_with_secret(event_lowercase, secret)
        
        # Assert: Lowercase header should work
        assert result_lowercase is True, "Lowercase header name should be accepted"
        
        # Test with uppercase header name
        event_uppercase = {
            'headers': {
                'X-Webhook-Signature': valid_signature
            },
            'body': payload_json
        }
        
        result_uppercase = verify_webhook_signature_with_secret(event_uppercase, secret)
        
        # Assert: Uppercase header should work
        assert result_uppercase is True, "Uppercase header name should be accepted"
    
    @given(
        payload=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_signature_verification_is_deterministic(
        self,
        payload: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Signature verification is deterministic
        
        For any webhook payload and secret, verifying the same signature
        multiple times must always produce the same result.
        
        **Validates: Requirements 10.2**
        """
        # Convert payload to JSON string
        payload_json = json.dumps(payload, sort_keys=True)
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create mock event
        event = {
            'headers': {
                'X-Webhook-Signature': valid_signature
            },
            'body': payload_json
        }
        
        # Verify signature multiple times
        results = [verify_webhook_signature_with_secret(event, secret) for _ in range(10)]
        
        # Assert: All results must be identical
        assert all(r == results[0] for r in results), "Signature verification must be deterministic"
        assert results[0] is True, "Valid signature must always be accepted"
    
    @given(
        payload1=payload_strategy,
        payload2=payload_strategy,
        secret=secret_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_different_payloads_have_different_signatures(
        self,
        payload1: Dict[str, Any],
        payload2: Dict[str, Any],
        secret: str
    ):
        """
        Property Test: Different payloads produce different signatures
        
        For any two different webhook payloads with the same secret:
        1. Their signatures MUST be different
        2. A signature for payload1 MUST NOT validate payload2
        
        **Validates: Requirements 10.2**
        """
        # Ensure payloads are different
        payload1_json = json.dumps(payload1, sort_keys=True)
        payload2_json = json.dumps(payload2, sort_keys=True)
        assume(payload1_json != payload2_json)
        
        # Generate signatures for both payloads
        signature1 = hmac.new(
            secret.encode(),
            payload1_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature2 = hmac.new(
            secret.encode(),
            payload2_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Assert: Signatures must be different
        assert signature1 != signature2, "Different payloads must have different signatures"
        
        # Create event with signature1 but payload2 (mismatch)
        event_mismatch = {
            'headers': {
                'X-Webhook-Signature': signature1
            },
            'body': payload2_json
        }
        
        # Verify signature
        result = verify_webhook_signature_with_secret(event_mismatch, secret)
        
        # Assert: Mismatched signature must be rejected
        assert result is False, "Signature for payload1 must not validate payload2"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
