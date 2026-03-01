"""
Data Classification Schema for AquaChain System.
Defines classification levels and field mappings for data protection.
Requirements: 11.3
"""

from enum import Enum
from typing import Dict, Set


class DataClassification(Enum):
    """
    Data classification levels for AquaChain system.
    
    Classification Levels:
    - PUBLIC: Data that can be freely shared without restrictions
    - INTERNAL: Data for internal use only, not for public disclosure
    - SENSITIVE: Data requiring protection, business-critical information
    - PII: Personally Identifiable Information requiring highest protection
    """
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    PII = "pii"


# Field classification mapping for all data fields in the system
FIELD_CLASSIFICATIONS: Dict[str, DataClassification] = {
    # User Profile Fields
    'user_id': DataClassification.INTERNAL,
    'email': DataClassification.PII,
    'name': DataClassification.PII,
    'first_name': DataClassification.PII,
    'last_name': DataClassification.PII,
    'phone': DataClassification.PII,
    'phone_number': DataClassification.PII,
    'address': DataClassification.PII,
    'street_address': DataClassification.PII,
    'city': DataClassification.PII,
    'state': DataClassification.PII,
    'postal_code': DataClassification.PII,
    'country': DataClassification.PII,
    'date_of_birth': DataClassification.PII,
    'ssn': DataClassification.PII,
    'tax_id': DataClassification.PII,
    'organization': DataClassification.INTERNAL,
    'organization_id': DataClassification.INTERNAL,
    'role': DataClassification.INTERNAL,
    'department': DataClassification.INTERNAL,
    'job_title': DataClassification.INTERNAL,
    'created_at': DataClassification.INTERNAL,
    'updated_at': DataClassification.INTERNAL,
    'last_login': DataClassification.INTERNAL,
    'profile_picture_url': DataClassification.INTERNAL,
    
    # Authentication & Security Fields
    'password': DataClassification.SENSITIVE,  # Should never be stored in plaintext
    'password_hash': DataClassification.SENSITIVE,
    'api_key': DataClassification.SENSITIVE,
    'access_token': DataClassification.SENSITIVE,
    'refresh_token': DataClassification.SENSITIVE,
    'session_id': DataClassification.SENSITIVE,
    'mfa_secret': DataClassification.SENSITIVE,
    'security_question': DataClassification.PII,
    'security_answer': DataClassification.SENSITIVE,
    
    # Device Fields
    'device_id': DataClassification.INTERNAL,
    'device_name': DataClassification.INTERNAL,
    'device_type': DataClassification.INTERNAL,
    'device_model': DataClassification.INTERNAL,
    'firmware_version': DataClassification.INTERNAL,
    'hardware_version': DataClassification.INTERNAL,
    'serial_number': DataClassification.SENSITIVE,
    'mac_address': DataClassification.SENSITIVE,
    'ip_address': DataClassification.SENSITIVE,
    'location': DataClassification.SENSITIVE,
    'latitude': DataClassification.SENSITIVE,
    'longitude': DataClassification.SENSITIVE,
    'altitude': DataClassification.SENSITIVE,
    'installation_date': DataClassification.INTERNAL,
    'last_seen': DataClassification.INTERNAL,
    'status': DataClassification.INTERNAL,
    'owner_id': DataClassification.INTERNAL,
    
    # Sensor Reading Fields
    'reading_id': DataClassification.INTERNAL,
    'reading_value': DataClassification.INTERNAL,
    'metric_type': DataClassification.INTERNAL,
    'metric_name': DataClassification.INTERNAL,
    'unit': DataClassification.INTERNAL,
    'timestamp': DataClassification.INTERNAL,
    'quality_score': DataClassification.INTERNAL,
    'alert_level': DataClassification.INTERNAL,
    'calibration_offset': DataClassification.INTERNAL,
    
    # Water Quality Metrics (Public for transparency)
    'ph_level': DataClassification.PUBLIC,
    'temperature': DataClassification.PUBLIC,
    'turbidity': DataClassification.PUBLIC,
    'dissolved_oxygen': DataClassification.PUBLIC,
    'conductivity': DataClassification.PUBLIC,
    'tds': DataClassification.PUBLIC,  # Total Dissolved Solids
    'chlorine_level': DataClassification.PUBLIC,
    'hardness': DataClassification.PUBLIC,
    
    # Alert Fields
    'alert_id': DataClassification.INTERNAL,
    'alert_type': DataClassification.INTERNAL,
    'severity': DataClassification.INTERNAL,
    'message': DataClassification.INTERNAL,
    'acknowledged': DataClassification.INTERNAL,
    'acknowledged_by': DataClassification.INTERNAL,
    'acknowledged_at': DataClassification.INTERNAL,
    'resolved': DataClassification.INTERNAL,
    'resolved_by': DataClassification.INTERNAL,
    'resolved_at': DataClassification.INTERNAL,
    
    # Audit Log Fields
    'log_id': DataClassification.INTERNAL,
    'action_type': DataClassification.INTERNAL,
    'resource_type': DataClassification.INTERNAL,
    'resource_id': DataClassification.INTERNAL,
    'details': DataClassification.INTERNAL,
    'request_id': DataClassification.INTERNAL,
    'user_agent': DataClassification.INTERNAL,
    'source': DataClassification.INTERNAL,
    
    # GDPR & Consent Fields
    'consent_id': DataClassification.INTERNAL,
    'consent_type': DataClassification.INTERNAL,
    'granted': DataClassification.INTERNAL,
    'consent_version': DataClassification.INTERNAL,
    'export_request_id': DataClassification.INTERNAL,
    'deletion_request_id': DataClassification.INTERNAL,
    'request_status': DataClassification.INTERNAL,
    'export_url': DataClassification.SENSITIVE,
    
    # Financial Fields (if applicable)
    'payment_method': DataClassification.SENSITIVE,
    'credit_card_number': DataClassification.PII,
    'credit_card_last4': DataClassification.SENSITIVE,
    'bank_account_number': DataClassification.PII,
    'billing_address': DataClassification.PII,
    'invoice_id': DataClassification.INTERNAL,
    'transaction_id': DataClassification.INTERNAL,
    'amount': DataClassification.INTERNAL,
    
    # System Metadata
    'version': DataClassification.INTERNAL,
    'checksum': DataClassification.INTERNAL,
    'ttl': DataClassification.INTERNAL,
    'partition_key': DataClassification.INTERNAL,
    'sort_key': DataClassification.INTERNAL,
}


# Classification rationale documentation
CLASSIFICATION_RATIONALE: Dict[DataClassification, str] = {
    DataClassification.PUBLIC: """
        PUBLIC data can be freely shared without restrictions.
        This includes water quality metrics that are meant for public transparency
        and environmental monitoring purposes. No encryption required.
        
        Examples: pH levels, temperature, turbidity readings
        
        Regulatory Basis: Environmental data transparency requirements
    """,
    
    DataClassification.INTERNAL: """
        INTERNAL data is for internal use only and should not be publicly disclosed.
        This includes system identifiers, operational metadata, and business logic data.
        Requires access controls but not necessarily encryption at rest.
        
        Examples: user_id, device_id, timestamps, alert metadata
        
        Regulatory Basis: Business confidentiality, operational security
    """,
    
    DataClassification.SENSITIVE: """
        SENSITIVE data requires protection due to business-critical nature or
        potential security implications if disclosed. Must be encrypted at rest
        using dedicated KMS keys and access strictly controlled.
        
        Examples: device serial numbers, IP addresses, location data, API keys
        
        Regulatory Basis: Trade secrets, security best practices, competitive advantage
    """,
    
    DataClassification.PII: """
        PII (Personally Identifiable Information) requires the highest level of
        protection under GDPR and other privacy regulations. Must be encrypted
        at rest using dedicated KMS keys, with strict access controls, audit logging,
        and data subject rights support (export, deletion, consent).
        
        Examples: email, name, phone, address, payment information
        
        Regulatory Basis: GDPR Article 4(1), CCPA, HIPAA (if health data),
        PCI-DSS (if payment data)
    """,
}


# Fields that require encryption at rest
ENCRYPTION_REQUIRED_FIELDS: Set[str] = {
    field for field, classification in FIELD_CLASSIFICATIONS.items()
    if classification in [DataClassification.PII, DataClassification.SENSITIVE]
}


# Fields that require audit logging on access
AUDIT_REQUIRED_FIELDS: Set[str] = {
    field for field, classification in FIELD_CLASSIFICATIONS.items()
    if classification in [DataClassification.PII, DataClassification.SENSITIVE]
}


# Fields subject to GDPR data subject rights
GDPR_SUBJECT_FIELDS: Set[str] = {
    field for field, classification in FIELD_CLASSIFICATIONS.items()
    if classification == DataClassification.PII
}


def get_field_classification(field_name: str) -> DataClassification:
    """
    Get the classification level for a specific field.
    
    Args:
        field_name: Name of the field to classify
        
    Returns:
        DataClassification enum value
        
    Defaults to INTERNAL if field is not explicitly classified.
    """
    return FIELD_CLASSIFICATIONS.get(field_name, DataClassification.INTERNAL)


def requires_encryption(field_name: str) -> bool:
    """
    Check if a field requires encryption at rest.
    
    Args:
        field_name: Name of the field to check
        
    Returns:
        True if encryption is required, False otherwise
    """
    return field_name in ENCRYPTION_REQUIRED_FIELDS


def requires_audit_logging(field_name: str) -> bool:
    """
    Check if a field requires audit logging on access.
    
    Args:
        field_name: Name of the field to check
        
    Returns:
        True if audit logging is required, False otherwise
    """
    return field_name in AUDIT_REQUIRED_FIELDS


def is_gdpr_subject_data(field_name: str) -> bool:
    """
    Check if a field is subject to GDPR data subject rights.
    
    Args:
        field_name: Name of the field to check
        
    Returns:
        True if field contains PII subject to GDPR, False otherwise
    """
    return field_name in GDPR_SUBJECT_FIELDS


def get_classification_summary() -> Dict[str, int]:
    """
    Get a summary of field classifications.
    
    Returns:
        Dictionary with counts for each classification level
    """
    summary = {
        'PUBLIC': 0,
        'INTERNAL': 0,
        'SENSITIVE': 0,
        'PII': 0,
        'TOTAL': len(FIELD_CLASSIFICATIONS)
    }
    
    for classification in FIELD_CLASSIFICATIONS.values():
        summary[classification.value.upper()] += 1
    
    return summary


def validate_data_classification() -> bool:
    """
    Validate that all critical fields have appropriate classifications.
    
    Returns:
        True if validation passes, False otherwise
    """
    # Critical PII fields that must be classified as PII
    critical_pii_fields = ['email', 'name', 'phone', 'address']
    
    for field in critical_pii_fields:
        if field not in FIELD_CLASSIFICATIONS:
            return False
        if FIELD_CLASSIFICATIONS[field] != DataClassification.PII:
            return False
    
    # Critical sensitive fields that must be encrypted
    critical_sensitive_fields = ['password_hash', 'api_key', 'access_token']
    
    for field in critical_sensitive_fields:
        if field not in FIELD_CLASSIFICATIONS:
            return False
        if FIELD_CLASSIFICATIONS[field] != DataClassification.SENSITIVE:
            return False
    
    return True
