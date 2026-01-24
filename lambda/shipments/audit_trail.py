"""
Audit trail utilities for shipment tracking compliance

This module ensures:
1. Timeline completeness - all status changes are recorded
2. Chronological ordering - timeline entries are properly ordered
3. Required fields - location and description for each entry
4. Webhook event storage - raw payloads are preserved
5. Admin action logging - user actions are tracked

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib


def validate_timeline_entry(entry: Dict[str, Any]) -> bool:
    """
    Validate that a timeline entry has all required fields.
    
    Required fields:
    - status: Internal status code
    - timestamp: ISO 8601 timestamp
    - location: Physical location or hub name
    - description: Human-readable description
    
    Args:
        entry: Timeline entry dictionary
        
    Returns:
        True if valid, False otherwise
        
    Requirements: 15.1
    """
    required_fields = ['status', 'timestamp', 'location', 'description']
    
    for field in required_fields:
        if field not in entry:
            print(f"ERROR: Timeline entry missing required field: {field}")
            return False
        
        # Check for empty values
        if not entry[field] or (isinstance(entry[field], str) and not entry[field].strip()):
            print(f"ERROR: Timeline entry has empty {field}")
            return False
    
    return True


def create_timeline_entry(
    status: str,
    timestamp: str,
    location: str,
    description: str,
    additional_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create a properly formatted timeline entry with all required fields.
    
    Args:
        status: Internal status code (e.g., 'in_transit', 'delivered')
        timestamp: ISO 8601 timestamp
        location: Physical location or hub name
        description: Human-readable description of the event
        additional_data: Optional additional metadata
        
    Returns:
        Timeline entry dictionary with all required fields
        
    Requirements: 15.1
    """
    # Ensure timestamp is in ISO format
    if not timestamp:
        timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Ensure location is not empty
    if not location or not location.strip():
        location = 'Unknown'
    
    # Ensure description is not empty
    if not description or not description.strip():
        description = f'Status changed to {status}'
    
    entry = {
        'status': status,
        'timestamp': timestamp,
        'location': location.strip(),
        'description': description.strip()
    }
    
    # Add optional additional data
    if additional_data:
        entry.update(additional_data)
    
    return entry


def validate_timeline_chronology(timeline: List[Dict]) -> bool:
    """
    Validate that timeline entries are in chronological order.
    
    Checks that each entry's timestamp is >= the previous entry's timestamp.
    
    Args:
        timeline: List of timeline entries
        
    Returns:
        True if chronologically ordered, False otherwise
        
    Requirements: 15.1
    """
    if not timeline or len(timeline) <= 1:
        return True
    
    for i in range(len(timeline) - 1):
        current_time = timeline[i].get('timestamp', '')
        next_time = timeline[i + 1].get('timestamp', '')
        
        if not current_time or not next_time:
            print(f"ERROR: Timeline entry missing timestamp at index {i}")
            return False
        
        try:
            # Parse timestamps for comparison
            current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            next_dt = datetime.fromisoformat(next_time.replace('Z', '+00:00'))
            
            if next_dt < current_dt:
                print(f"ERROR: Timeline not chronological at index {i}: {current_time} > {next_time}")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to parse timeline timestamps: {str(e)}")
            return False
    
    return True


def sort_timeline_chronologically(timeline: List[Dict]) -> List[Dict]:
    """
    Sort timeline entries by timestamp in ascending order.
    
    Args:
        timeline: List of timeline entries
        
    Returns:
        Sorted timeline list
        
    Requirements: 15.1
    """
    if not timeline:
        return []
    
    try:
        return sorted(
            timeline,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '').replace('Z', '+00:00'))
        )
    except Exception as e:
        print(f"ERROR: Failed to sort timeline: {str(e)}")
        return timeline


def create_webhook_event(
    event_id: str,
    courier_status: str,
    raw_payload: Dict,
    max_payload_size: int = 1000
) -> Dict[str, Any]:
    """
    Create a webhook event entry for audit trail.
    
    Stores raw webhook payload with truncation to avoid DynamoDB size limits.
    
    Args:
        event_id: Unique event identifier
        courier_status: Status code from courier
        raw_payload: Raw webhook payload dictionary
        max_payload_size: Maximum size for payload string (default 1000 chars)
        
    Returns:
        Webhook event dictionary
        
    Requirements: 15.2
    """
    # Serialize payload to JSON
    payload_str = json.dumps(raw_payload)
    
    # Truncate if too large
    if len(payload_str) > max_payload_size:
        payload_str = payload_str[:max_payload_size]
        truncated = True
    else:
        truncated = False
    
    return {
        'event_id': event_id,
        'received_at': datetime.utcnow().isoformat() + 'Z',
        'courier_status': courier_status,
        'raw_payload': payload_str,
        'truncated': truncated
    }


def create_admin_action_log(
    action_type: str,
    user_id: str,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create an admin action log entry.
    
    Logs admin actions such as:
    - Shipment creation
    - Address changes
    - Manual cancellations
    - Status overrides
    
    Args:
        action_type: Type of action (e.g., 'SHIPMENT_CREATED', 'ADDRESS_CHANGED')
        user_id: Admin user ID performing the action
        details: Optional additional details about the action
        
    Returns:
        Admin action log entry
        
    Requirements: 15.3
    """
    log_entry = {
        'action_type': action_type,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if details:
        log_entry['details'] = details
    
    return log_entry


def calculate_ttl_timestamp(years: int = 2) -> int:
    """
    Calculate TTL timestamp for DynamoDB (Unix epoch seconds).
    
    Used for data retention policy - audit data expires after specified years.
    
    Args:
        years: Number of years until expiration (default 2)
        
    Returns:
        Unix timestamp (seconds since epoch)
        
    Requirements: 15.5
    """
    from datetime import timedelta
    
    expiration_date = datetime.utcnow() + timedelta(days=365 * years)
    return int(expiration_date.timestamp())


def validate_audit_trail_completeness(shipment: Dict) -> Dict[str, Any]:
    """
    Validate that a shipment has a complete audit trail.
    
    Checks:
    1. Timeline exists and has entries
    2. All timeline entries have required fields
    3. Timeline is chronologically ordered
    4. Webhook events are stored
    5. Admin actions are logged (if applicable)
    
    Args:
        shipment: Shipment record from DynamoDB
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str]
        }
        
    Requirements: 15.1, 15.2, 15.3, 15.4
    """
    errors = []
    warnings = []
    
    # Check timeline exists
    timeline = shipment.get('timeline', [])
    if not timeline:
        errors.append('Timeline is empty')
    else:
        # Validate each timeline entry
        for i, entry in enumerate(timeline):
            if not validate_timeline_entry(entry):
                errors.append(f'Timeline entry {i} is invalid or incomplete')
        
        # Check chronological ordering
        if not validate_timeline_chronology(timeline):
            errors.append('Timeline is not in chronological order')
    
    # Check webhook events
    webhook_events = shipment.get('webhook_events', [])
    if not webhook_events:
        warnings.append('No webhook events recorded (may be expected for new shipments)')
    else:
        # Validate webhook event structure
        for i, event in enumerate(webhook_events):
            required_fields = ['event_id', 'received_at', 'courier_status']
            for field in required_fields:
                if field not in event:
                    errors.append(f'Webhook event {i} missing required field: {field}')
    
    # Check admin actions (if shipment was created by admin)
    created_by = shipment.get('created_by')
    if not created_by:
        warnings.append('No created_by field - admin action not logged')
    
    # Check for admin_actions array if manual interventions occurred
    admin_actions = shipment.get('admin_actions', [])
    if admin_actions:
        for i, action in enumerate(admin_actions):
            required_fields = ['action_type', 'user_id', 'timestamp']
            for field in required_fields:
                if field not in action:
                    errors.append(f'Admin action {i} missing required field: {field}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def generate_audit_report(shipment: Dict) -> str:
    """
    Generate a human-readable audit report for a shipment.
    
    Args:
        shipment: Shipment record from DynamoDB
        
    Returns:
        Formatted audit report string
        
    Requirements: 15.4
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"SHIPMENT AUDIT REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Shipment ID: {shipment.get('shipment_id', 'N/A')}")
    report_lines.append(f"Order ID: {shipment.get('order_id', 'N/A')}")
    report_lines.append(f"Tracking Number: {shipment.get('tracking_number', 'N/A')}")
    report_lines.append(f"Created At: {shipment.get('created_at', 'N/A')}")
    report_lines.append(f"Created By: {shipment.get('created_by', 'N/A')}")
    report_lines.append("")
    
    # Timeline section
    report_lines.append("TIMELINE:")
    report_lines.append("-" * 80)
    timeline = shipment.get('timeline', [])
    if timeline:
        for i, entry in enumerate(timeline, 1):
            report_lines.append(f"{i}. {entry.get('timestamp', 'N/A')}")
            report_lines.append(f"   Status: {entry.get('status', 'N/A')}")
            report_lines.append(f"   Location: {entry.get('location', 'N/A')}")
            report_lines.append(f"   Description: {entry.get('description', 'N/A')}")
            report_lines.append("")
    else:
        report_lines.append("No timeline entries")
        report_lines.append("")
    
    # Webhook events section
    report_lines.append("WEBHOOK EVENTS:")
    report_lines.append("-" * 80)
    webhook_events = shipment.get('webhook_events', [])
    if webhook_events:
        for i, event in enumerate(webhook_events, 1):
            report_lines.append(f"{i}. Event ID: {event.get('event_id', 'N/A')}")
            report_lines.append(f"   Received At: {event.get('received_at', 'N/A')}")
            report_lines.append(f"   Courier Status: {event.get('courier_status', 'N/A')}")
            if event.get('truncated'):
                report_lines.append(f"   Payload: [TRUNCATED]")
            report_lines.append("")
    else:
        report_lines.append("No webhook events")
        report_lines.append("")
    
    # Admin actions section
    report_lines.append("ADMIN ACTIONS:")
    report_lines.append("-" * 80)
    admin_actions = shipment.get('admin_actions', [])
    if admin_actions:
        for i, action in enumerate(admin_actions, 1):
            report_lines.append(f"{i}. {action.get('timestamp', 'N/A')}")
            report_lines.append(f"   Action: {action.get('action_type', 'N/A')}")
            report_lines.append(f"   User: {action.get('user_id', 'N/A')}")
            if 'details' in action:
                report_lines.append(f"   Details: {json.dumps(action['details'])}")
            report_lines.append("")
    else:
        report_lines.append("No admin actions")
        report_lines.append("")
    
    # Validation section
    report_lines.append("AUDIT VALIDATION:")
    report_lines.append("-" * 80)
    validation = validate_audit_trail_completeness(shipment)
    report_lines.append(f"Valid: {validation['valid']}")
    if validation['errors']:
        report_lines.append("Errors:")
        for error in validation['errors']:
            report_lines.append(f"  - {error}")
    if validation['warnings']:
        report_lines.append("Warnings:")
        for warning in validation['warnings']:
            report_lines.append(f"  - {warning}")
    
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)
