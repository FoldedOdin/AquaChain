"""
PagerDuty Integration for AquaChain System
Handles incident escalation and on-call management
"""

import boto3
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import os


class PagerDutyIntegration:
    def __init__(self, integration_key: str, api_token: str = None):
        self.integration_key = integration_key
        self.api_token = api_token
        self.events_api_url = "https://events.pagerduty.com/v2/enqueue"
        self.api_url = "https://api.pagerduty.com"
        
    def create_incident(self, 
                       title: str, 
                       description: str, 
                       severity: str = "error",
                       source: str = "AquaChain System",
                       custom_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a PagerDuty incident
        
        Args:
            title: Brief description of the incident
            description: Detailed description
            severity: error, warning, info, critical
            source: Source system name
            custom_details: Additional context data
        """
        
        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": f"aquachain-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "payload": {
                "summary": title,
                "source": source,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "custom_details": custom_details or {}
            }
        }
        
        try:
            response = requests.post(
                self.events_api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating PagerDuty incident: {e}")
            raise
    
    def resolve_incident(self, dedup_key: str) -> Dict[str, Any]:
        """Resolve a PagerDuty incident"""
        payload = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key
        }
        
        try:
            response = requests.post(
                self.events_api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error resolving PagerDuty incident: {e}")
            raise
    
    def create_maintenance_window(self, 
                                 service_id: str,
                                 start_time: str,
                                 end_time: str,
                                 description: str) -> Dict[str, Any]:
        """Create a maintenance window"""
        if not self.api_token:
            raise ValueError("API token required for maintenance window operations")
            
        payload = {
            "maintenance_window": {
                "type": "maintenance_window",
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "services": [{"id": service_id, "type": "service_reference"}]
            }
        }
        
        headers = {
            "Authorization": f"Token token={self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/maintenance_windows",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating maintenance window: {e}")
            raise


class AquaChainIncidentHandler:
    """Handles AquaChain-specific incident scenarios"""
    
    def __init__(self, pagerduty_integration: PagerDutyIntegration):
        self.pagerduty = pagerduty_integration
        
    def handle_alert_latency_breach(self, latency_seconds: float, threshold: float = 30.0):
        """Handle alert latency SLA breach"""
        title = f"Alert Latency SLA Breach: {latency_seconds:.1f}s (>{threshold}s)"
        description = f"""
        Alert notification latency has exceeded the 30-second SLA.
        
        Current Latency: {latency_seconds:.1f} seconds
        SLA Threshold: {threshold} seconds
        Breach Amount: {latency_seconds - threshold:.1f} seconds
        
        This affects the critical path for water quality alerts and requires immediate attention.
        """
        
        custom_details = {
            "metric": "alert_latency",
            "current_value": latency_seconds,
            "threshold": threshold,
            "breach_amount": latency_seconds - threshold,
            "impact": "Critical - Water quality alerts delayed",
            "runbook": "https://docs.aquachain.io/runbooks/alert-latency-breach"
        }
        
        return self.pagerduty.create_incident(
            title=title,
            description=description,
            severity="critical",
            custom_details=custom_details
        )
    
    def handle_data_ingestion_failure(self, error_rate: float, duration_minutes: int):
        """Handle data ingestion pipeline failure"""
        title = f"Data Ingestion Failure: {error_rate:.1f}% error rate for {duration_minutes} minutes"
        description = f"""
        Critical data ingestion path is experiencing high error rates.
        
        Error Rate: {error_rate:.1f}%
        Duration: {duration_minutes} minutes
        Threshold: 5% for >5 minutes
        
        This affects the core functionality of water quality monitoring.
        """
        
        custom_details = {
            "metric": "data_ingestion_error_rate",
            "current_value": error_rate,
            "duration_minutes": duration_minutes,
            "threshold": 5.0,
            "impact": "Critical - Water quality data not being processed",
            "runbook": "https://docs.aquachain.io/runbooks/data-ingestion-failure"
        }
        
        return self.pagerduty.create_incident(
            title=title,
            description=description,
            severity="critical",
            custom_details=custom_details
        )
    
    def handle_technician_assignment_failure(self, service_request_id: str, location: str):
        """Handle technician assignment failure"""
        title = f"Technician Assignment Failure: No available technicians for {location}"
        description = f"""
        Unable to assign technician for service request.
        
        Service Request ID: {service_request_id}
        Location: {location}
        Issue: No available technicians within service zone
        
        Customer has been notified of delay. Manual intervention required.
        """
        
        custom_details = {
            "service_request_id": service_request_id,
            "location": location,
            "issue": "no_available_technicians",
            "customer_notified": True,
            "impact": "High - Customer service degradation",
            "runbook": "https://docs.aquachain.io/runbooks/technician-assignment-failure"
        }
        
        return self.pagerduty.create_incident(
            title=title,
            description=description,
            severity="error",
            custom_details=custom_details
        )
    
    def handle_system_uptime_breach(self, current_uptime: float, target_uptime: float = 99.5):
        """Handle system uptime SLA breach"""
        title = f"System Uptime SLA Breach: {current_uptime:.2f}% (target: {target_uptime}%)"
        description = f"""
        System uptime has fallen below the 99.5% SLA target.
        
        Current Uptime: {current_uptime:.2f}%
        Target Uptime: {target_uptime}%
        Shortfall: {target_uptime - current_uptime:.2f}%
        
        This affects service reliability and customer trust.
        """
        
        custom_details = {
            "metric": "system_uptime",
            "current_value": current_uptime,
            "target": target_uptime,
            "shortfall": target_uptime - current_uptime,
            "impact": "High - SLA breach affects customer trust",
            "runbook": "https://docs.aquachain.io/runbooks/uptime-sla-breach"
        }
        
        return self.pagerduty.create_incident(
            title=title,
            description=description,
            severity="error",
            custom_details=custom_details
        )


def create_lambda_handler_for_pagerduty():
    """Create Lambda function handler for PagerDuty integration"""
    
    lambda_code = '''
import json
import os
from pagerduty_integration import PagerDutyIntegration, AquaChainIncidentHandler

def lambda_handler(event, context):
    """
    Lambda handler for PagerDuty incident creation
    Triggered by CloudWatch alarms via SNS
    """
    
    # Get PagerDuty integration key from environment
    integration_key = os.environ.get('PAGERDUTY_INTEGRATION_KEY')
    if not integration_key:
        raise ValueError("PAGERDUTY_INTEGRATION_KEY environment variable not set")
    
    # Initialize PagerDuty integration
    pagerduty = PagerDutyIntegration(integration_key)
    incident_handler = AquaChainIncidentHandler(pagerduty)
    
    # Parse SNS message
    try:
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        alarm_name = sns_message.get('AlarmName', 'Unknown Alarm')
        alarm_description = sns_message.get('AlarmDescription', '')
        metric_name = sns_message.get('MetricName', '')
        new_state_value = sns_message.get('NewStateValue', '')
        
        # Handle different alarm types
        if 'AlertLatency' in alarm_name and new_state_value == 'ALARM':
            # Extract latency value from alarm data
            latency = float(sns_message.get('NewStateReason', '0').split()[-1])
            response = incident_handler.handle_alert_latency_breach(latency)
            
        elif 'ErrorRate' in alarm_name and new_state_value == 'ALARM':
            # Extract error rate from alarm data
            error_rate = float(sns_message.get('NewStateReason', '0').split()[-1])
            response = incident_handler.handle_data_ingestion_failure(error_rate, 15)
            
        elif 'DeviceUptime' in alarm_name and new_state_value == 'ALARM':
            # Extract uptime value
            uptime = float(sns_message.get('NewStateReason', '99.5').split()[-1])
            response = incident_handler.handle_system_uptime_breach(uptime)
            
        else:
            # Generic incident creation
            response = pagerduty.create_incident(
                title=f"CloudWatch Alarm: {alarm_name}",
                description=f"{alarm_description}\\n\\nAlarm State: {new_state_value}",
                severity="error" if new_state_value == 'ALARM' else "info",
                custom_details={
                    "alarm_name": alarm_name,
                    "metric_name": metric_name,
                    "state": new_state_value,
                    "reason": sns_message.get('NewStateReason', '')
                }
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
        print(f"Error processing alarm: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
'''
    
    return lambda_code


if __name__ == "__main__":
    # Example usage
    integration_key = os.environ.get('PAGERDUTY_INTEGRATION_KEY', 'test-key')
    pagerduty = PagerDutyIntegration(integration_key)
    incident_handler = AquaChainIncidentHandler(pagerduty)
    
    print("PagerDuty integration configured successfully!")
    print("Lambda handler code generated for CloudWatch alarm integration.")