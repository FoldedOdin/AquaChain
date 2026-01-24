"""
JWT Middleware Package for AquaChain Dashboard Overhaul.

This package provides JWT token validation, session management, and 
multi-factor authentication functionality including:
- JWT token validation with Cognito
- Session management with timeout and concurrent session limits
- Multi-factor authentication for sensitive operations
- Token blacklisting for secure logout
- Comprehensive audit logging
"""

from .handler import JWTValidator, SessionManager, MFAValidator, JWTMiddleware

__all__ = [
    'JWTValidator',
    'SessionManager', 
    'MFAValidator',
    'JWTMiddleware'
]