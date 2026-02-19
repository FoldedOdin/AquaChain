"""
OTP Security Utilities
Provides secure OTP handling with hashing, rate limiting, and constant-time comparison
"""

import hashlib
import hmac
import secrets
from typing import Tuple, Optional
from datetime import datetime, timedelta


def generate_otp(length: int = 6) -> str:
    """
    Generate cryptographically secure OTP
    
    Args:
        length: OTP length (default 6)
    
    Returns:
        Numeric OTP string
    """
    # Use secrets module for cryptographically secure random numbers
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(otp: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash OTP using SHA-256 with salt
    
    Args:
        otp: Plain text OTP
        salt: Optional salt (generated if not provided)
    
    Returns:
        Tuple of (hashed_otp, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine OTP with salt and hash
    salted_otp = f"{otp}{salt}"
    hashed = hashlib.sha256(salted_otp.encode()).hexdigest()
    
    return hashed, salt


def verify_otp_hash(input_otp: str, stored_hash: str, salt: str) -> bool:
    """
    Verify OTP using constant-time comparison to prevent timing attacks
    
    Args:
        input_otp: User-provided OTP
        stored_hash: Stored hash from database
        salt: Salt used for hashing
    
    Returns:
        True if OTP matches, False otherwise
    """
    # Hash the input OTP with the same salt
    input_hash, _ = hash_otp(input_otp, salt)
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(input_hash, stored_hash)


def check_rate_limit(
    last_request_time: datetime,
    cooldown_seconds: int = 120
) -> Tuple[bool, int]:
    """
    Check if rate limit cooldown has passed
    
    Args:
        last_request_time: Timestamp of last OTP request
        cooldown_seconds: Cooldown period in seconds (default 120)
    
    Returns:
        Tuple of (is_allowed, remaining_seconds)
    """
    now = datetime.utcnow()
    time_since_last = (now - last_request_time).total_seconds()
    
    if time_since_last < cooldown_seconds:
        remaining = int(cooldown_seconds - time_since_last)
        return False, remaining
    
    return True, 0


def should_lockout(
    failed_attempts: int,
    lockout_threshold: int = 5,
    lockout_duration_minutes: int = 15
) -> Tuple[bool, Optional[datetime]]:
    """
    Determine if account should be locked out due to failed attempts
    
    Args:
        failed_attempts: Number of failed verification attempts
        lockout_threshold: Max attempts before lockout (default 5)
        lockout_duration_minutes: Lockout duration in minutes (default 15)
    
    Returns:
        Tuple of (should_lock, lock_until_timestamp)
    """
    if failed_attempts >= lockout_threshold:
        lock_until = datetime.utcnow() + timedelta(minutes=lockout_duration_minutes)
        return True, lock_until
    
    return False, None


def is_locked_out(lock_until: Optional[datetime]) -> Tuple[bool, int]:
    """
    Check if account is currently locked out
    
    Args:
        lock_until: Timestamp when lockout expires
    
    Returns:
        Tuple of (is_locked, remaining_seconds)
    """
    if lock_until is None:
        return False, 0
    
    now = datetime.utcnow()
    
    if now < lock_until:
        remaining = int((lock_until - now).total_seconds())
        return True, remaining
    
    return False, 0


def get_client_ip(event: dict) -> str:
    """
    Extract client IP address from API Gateway event
    
    Args:
        event: Lambda event from API Gateway
    
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header first (for proxies)
    headers = event.get('headers', {})
    
    # Headers can be case-insensitive
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    x_forwarded_for = headers_lower.get('x-forwarded-for', '')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return x_forwarded_for.split(',')[0].strip()
    
    # Fallback to requestContext
    request_context = event.get('requestContext', {})
    identity = request_context.get('identity', {})
    
    return identity.get('sourceIp', 'unknown')


def get_user_agent(event: dict) -> str:
    """
    Extract User-Agent from API Gateway event
    
    Args:
        event: Lambda event from API Gateway
    
    Returns:
        User-Agent string
    """
    headers = event.get('headers', {})
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    return headers_lower.get('user-agent', 'unknown')


def get_idempotency_key(event: dict) -> Optional[str]:
    """
    Extract idempotency key from request headers
    
    Args:
        event: Lambda event from API Gateway
    
    Returns:
        Idempotency key or None
    """
    headers = event.get('headers', {})
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    return headers_lower.get('idempotency-key')
