"""
Lambda handler for PagerDuty incident management
Processes CloudWatch alarms and creates PagerDuty incidents
"""

import json
import os
import sys
import requests
from datetime import datetime
from typing import Dict, Any

# Add shared utilities to path
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='pagerduty-integration')


def create_pagerduty_incident(integration_key: str, 
                             title: str, 
                             description: str, 
                             severity: str = "error",
                             custom_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a PagerDuty incident"""
    
    events_api_url = "https://events.pagerduty.com/v2/enqueue"
    
    payload = {
        "routing_key": integration_key,
        "event_action": "trigger",
        "dedup_key": f"aquachain-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "payload": {
            "summary": title,
            "source": "AquaChain System",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "custom_details": custom_details or {}
        }
    }
    
    response = requests.post(
        events_api_url,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


def handle_alert_latency_breach(integration_key: str, latency_seconds: float) -> Dict[str, Any]:
    """Handle alert latency SLA breach"""
    threshold = 30.0
    title = f"🚨 Alert Latency SLA Breach: {latency_seconds:.1f}s (>{threshold}s)"
    description = f"""
CRITICAL: Alert notification latency has exceeded the 30-second SLA.

📊 Metrics:
• Current Latency: {latency_seconds:.1f} seconds
• SLA Threshold: {threshold} seconds  
• Breach Amount: {latency_seconds - threshold:.1f} seconds

🎯 Impact: Critical - Water quality alerts delayed
📖 Runbook: https://docs.aquachain.io/runbooks/alert-latency-breach

⚡ Immediate Actions Required:
1. Check Lambda function performance and concurrency
2. Verify DynamoDB write performance
3. Check SNS delivery status
4. Review API Gateway latency
"""
    
    custom_details = {
        "metric": "alert_latency",
        "current_value": latency_seconds,
        "threshold": threshold,
        "breach_amount": latency_seconds - threshold,
        "impact": "Critical - Water quality alerts delayed",
        "runbook": "https://docs.aquachain.io/runbooks/alert-latency-breach",
        "priority": "P1"
    }
    
    return create_pagerduty_incident(
        integration_key=integration_key,
        title=title,
        description=description,
        severity="critical",
        custom_details=custom_details
    )


def handle_data_ingestion_failure(integration_key: str, error_rate: float, duration_minutes: int = 15) -> Dict[str, Any]:
    """Handle data ingestion pipeline failure"""
    title = f"🔥 Data Ingestion Failure: {error_rate:.1f}% error rate for {duration_minutes} minutes"
    description = f"""
CRITICAL: Data ingestion pipeline is experiencing high error rates.

📊 Metrics:
• Error Rate: {error_rate:.1f}%
• Duration: {duration_minutes} minutes
• Threshold: 5% for >5 minutes

🎯 Impact: Critical - Water quality data not being processed
📖 Runbook: https://docs.aquachain.io/runbooks/data-ingestion-failure

⚡ Immediate Actions Required:
1. Check IoT Core message processing
2. Verify Lambda function health (data-processing, ml-inference)
3. Check DynamoDB throttling and capacity
4. Review dead letter queue for failed messages
"""
    
    custom_details = {
        "metric": "data_ingestion_error_rate",
        "current_value": error_rate,
        "duration_minutes": duration_minutes,
        "threshold": 5.0,
        "impact": "Critical - Water quality data not being processed",
        "runbook": "https://docs.aquachain.io/runbooks/data-ingestion-failure",
        "priority": "P1"
    }
    
    return create_pagerduty_incident(
        integration_key=integration_key,
        title=title,
        description=description,
        severity="critical",
        custom_details=custom_details
    )


def handle_system_uptime_breach(integration_key: str, current_uptime: float) -> Dict[str, Any]:
    """Handle system uptime SLA breach"""
    target_uptime = 99.5
    title = f"📉 System Uptime SLA Breach: {current_uptime:.2f}% (target: {target_uptime}%)"
    description = f"""
HIGH: System uptime has fallen below the 99.5% SLA target.

📊 Metrics:
• Current Uptime: {current_uptime:.2f}%
• Target Uptime: {target_uptime}%
• Shortfall: {target_uptime - current_uptime:.2f}%

🎯 Impact: High - SLA breach affects customer trust
📖 Runbook: https://docs.aquachain.io/runbooks/uptime-sla-breach

⚡ Actions Required:
1. Review recent incidents and outages
2. Check system health metrics
3. Verify auto-scaling and failover mechanisms
4. Prepare customer communication if needed
"""
    
    custom_details = {
        "metric": "system_uptime",
        "current_value": current_uptime,
        "target": target_uptime,
        "shortfall": target_uptime - current_uptime,
        "impact": "High - SLA breach affects customer trust",
        "runbook": "https://docs.aquachain.io/runbooks/uptime-sla-breach",
        "priority": "P2"
    }
    
    return create_pagerduty_incident(
        integration_key=integration_key,
        title=title,
        description=description,
        severity="error",
        custom_details=custom_details
    )


def handle_technician_assignment_failure(integration_key: str, service_request_id: str, location: str) -> Dict[str, Any]:
    """Handle technician assignment failure"""
    title = f"👥 Technician Assignment Failure: No available technicians for {location}"
    description = f"""
HIGH: Unable to assign technician for service request.

📊 Details:
• Service Request ID: {service_request_id}
• Location: {location}
• Issue: No available technicians within service zone

🎯 Impact: High - Customer service degradation
📖 Runbook: https://docs.aquachain.io/runbooks/technician-assignment-failure

⚡ Actions Required:
1. Review technician availability and schedules
2. Check for technicians in nearby service zones
3. Consider overtime assignments
4. Update customer with realistic timeline
5. Escalate to operations manager if needed
"""
    
    custom_details = {
        "service_request_id": service_request_id,
        "location": location,
        "issue": "no_available_technicians",
        "customer_notified": True,
        "impact": "High - Customer service degradation",
        "runbook": "https://docs.aquachain.io/runbooks/technician-assignment-failure",
        "priority": "P2"
    }
    
    return create_pagerduty_incident(
        integration_key=integration_key,
        title=title,
        description=description,
        severity="error",
        custom_details=custom_details
    )


def lambda_handler(event, context):
    """
    Lambda handler for PagerDuty incident creation
    Triggered by CloudWatch alarms via SNS
    """
    
    # Get PagerDuty integration key from environment
    integration_key = os.environ.get('PAGERDUTY_INTEGRATION_KEY')
    if not integration_key:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'PAGERDUTY_INTEGRATION_KEY environment variable not set'})
        }
    
    try:
        # Parse SNS message
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        alarm_name = sns_message.get('AlarmName', 'Unknown Alarm')
        alarm_description = sns_message.get('AlarmDescription', '')
        metric_name = sns_message.get('MetricName', '')
        new_state_value = sns_message.get('NewStateValue', '')
        new_state_reason = sns_message.get('NewStateReason', '')
        
        logger.info(
            "Processing CloudWatch alarm",
            alarm_name=alarm_name,
            alarm_state=new_state_value
        )
        
        # Only process ALARM state (not OK or INSUFFICIENT_DATA)
        if new_state_value != 'ALARM':
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'Ignoring alarm state: {new_state_value}'})
            }
        
        # Handle different alarm types
        response = None
        
        if 'AlertLatency' in alarm_name:
            # Extract latency value from alarm reason
            try:
                # Parse latency from reason string like "Threshold Crossed: 1 out of the last 2 datapoints [35.2 (19/10/25 14:23:00)] was greater than the threshold (30.0)"
                import re
                match = re.search(r'\[(\d+\.?\d*)', new_state_reason)
                latency = float(match.group(1)) if match else 35.0
            except:
                latency = 35.0  # Default assumption if parsing fails
            
            response = handle_alert_latency_breach(integration_key, latency)
            
        elif 'ErrorRate' in alarm_name:
            # Extract error rate from alarm reason
            try:
                import re
                match = re.search(r'\[(\d+\.?\d*)', new_state_reason)
                error_rate = float(match.group(1)) if match else 10.0
            except:
                error_rate = 10.0  # Default assumption if parsing fails
            
            response = handle_data_ingestion_failure(integration_key, error_rate)
            
        elif 'DeviceUptime' in alarm_name:
            # Extract uptime value
            try:
                import re
                match = re.search(r'\[(\d+\.?\d*)', new_state_reason)
                uptime = float(match.group(1)) if match else 94.0
            except:
                uptime = 94.0  # Default assumption if parsing fails
            
            response = handle_system_uptime_breach(integration_key, uptime)
            
        else:
            # Generic incident creation for other alarms
            response = create_pagerduty_incident(
                integration_key=integration_key,
                title=f"CloudWatch Alarm: {alarm_name}",
                description=f"{alarm_description}\n\nAlarm State: {new_state_value}\nReason: {new_state_reason}",
                severity="error",
                custom_details={
                    "alarm_name": alarm_name,
                    "metric_name": metric_name,
                    "state": new_state_value,
                    "reason": new_state_reason,
                    "priority": "P3"
                }
            )
        
        logger.info(
            "PagerDuty incident created",
            alarm_name=alarm_name,
            incident_key=response.get('dedup_key')
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'PagerDuty incident created successfully',
                'incident_key': response.get('dedup_key'),
                'status': response.get('status')
            })
        }
        
    except Exception as e:
        logger.error(
            "Error processing alarm",
            error_message=str(e)
        )
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }