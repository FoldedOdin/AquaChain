"""
Legacy table name mapping for existing DynamoDB tables
These tables were created before the standardized naming convention
"""

# Mapping of resource names to actual table names in AWS
LEGACY_TABLE_NAMES = {
    "readings": "AquaChain-Readings",
    "ledger": "AquaChain-Ledger",
    "sequence": "AquaChain-Sequence",
    "users": "AquaChain-Users",
    "service-requests": "AquaChain-ServiceRequests",
    "devices": "AquaChain-Devices",
    "audit-logs": "AquaChain-AuditLogs",
    "system-config": "AquaChain-SystemConfig",
}

def get_legacy_table_name(resource_name: str) -> str:
    """
    Get the legacy table name for a given resource
    
    Args:
        resource_name: Base resource name (e.g., "users", "readings")
        
    Returns:
        Legacy table name if it exists, otherwise None
    """
    return LEGACY_TABLE_NAMES.get(resource_name)
