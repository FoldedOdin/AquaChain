"""
Automatic Technician Assignment Lambda

This Lambda function is triggered by EventBridge when an order reaches ORDER_PLACED status.
It automatically assigns the nearest available technician with a complete profile.

Requirements:
- Technician must have complete profile (name, phone, email, location, skills)
- Select nearest technician within 50km radius
- Alert technicians with incomplete profiles to complete their profile
"""

import sys
import os
import json
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
from botocore.exceptions import ClientError

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'technician_assignment'))

from structured_logger import get_logger
from error_handler import AquaChainError, ErrorCode
from technician_assignment_service import TechnicianAssignmentService

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
ses = boto3.client('ses')

# Environment variables
ORDERS_TABLE = os.environ.get('ENHANCED_ORDERS_TABLE', 'aquachain-orders')
TECHNICIANS_TABLE = os.environ.get('ENHANCED_TECHNICIANS_TABLE', 'aquachain-technicians')
USERS_TABLE = os.environ.get('USERS_TABLE', 'aquachain-users')
SNS_TOPIC_ARN = os.environ.get('TECHNICIAN_ALERTS_TOPIC_ARN')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@aquachain.com')

# Initialize logger
logger = get_logger(__name__, service='auto-technician-assignment')


class ProfileCompletionValidator:
    """Validates technician profile completion"""
    
    REQUIRED_FIELDS = [
        'name',
        'phone',
        'email',
        'location',
        'skills',
        'address'
    ]
    
    @staticmethod
    def is_profile_complete(technician: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check if technician profile is complete
        
        Returns:
            (is_complete, missing_fields)
        """
        missing_fields = []
        
        # Check basic fields
        if not technician.get('name') or not technician['name'].strip():
            missing_fields.append('name')
        
        if not technician.get('phone') or not technician['phone'].strip():
            missing_fields.append('phone')
        
        if not technician.get('email') or not technician['email'].strip():
            missing_fields.append('email')
        
        # Check location
        location = technician.get('location', {})
        if not location or not location.get('latitude') or not location.get('longitude'):
            missing_fields.append('location')
        
        # Check skills
        skills = technician.get('skills', [])
        if not skills or len(skills) == 0:
            missing_fields.append('skills')
        
        # Check address
        address = technician.get('address', {})
        if not address or not address.get('street') or not address.get('city'):
            missing_fields.append('address')
        
        is_complete = len(missing_fields) == 0
        
        return is_complete, missing_fields


class AutoTechnicianAssignmentService:
    """Service for automatic technician assignment"""
    
    def __init__(self):
        self.orders_table = dynamodb.Table(ORDERS_TABLE)
        self.technicians_table = dynamodb.Table(TECHNICIANS_TABLE)
        self.users_table = dynamodb.Table(USERS_TABLE)
        self.assignment_service = TechnicianAssignmentService()
        self.profile_validator = ProfileCompletionValidator()
    
    def process_order_placed_event(self, event_detail: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """
        Process ORDER_PLACED event and assign technician automatically
        
        Args:
            event_detail: EventBridge event detail
            correlation_id: Correlation ID for tracing
            
        Returns:
            Assignment result
        """
        logger.start_operation('process_order_placed_event')
        
        try:
            order_id = event_detail.get('orderId')
            consumer_id = event_detail.get('consumerId')
            
            if not order_id:
                logger.error('Missing orderId in event', event_detail=event_detail)
                raise ValueError('Missing orderId in event')
            
            # Get order details
            order = self._get_order(order_id)
            if not order:
                logger.error('Order not found', order_id=order_id)
                raise ValueError(f'Order {order_id} not found')
            
            # Extract service location from order
            service_location = order.get('deliveryAddress', {}).get('coordinates')
            if not service_location:
                logger.warning('No service location in order, using default', order_id=order_id)
                # Use a default location or skip assignment
                return {
                    'success': False,
                    'message': 'No service location available for technician assignment'
                }
            
            # Get all available technicians
            all_technicians = self._get_all_technicians()
            
            # Filter technicians with complete profiles
            eligible_technicians = []
            incomplete_profile_technicians = []
            
            for tech in all_technicians:
                is_complete, missing_fields = self.profile_validator.is_profile_complete(tech)
                
                if is_complete and tech.get('available', False):
                    eligible_technicians.append(tech)
                elif not is_complete:
                    incomplete_profile_technicians.append({
                        'technician': tech,
                        'missing_fields': missing_fields
                    })
            
            # Alert technicians with incomplete profiles
            if incomplete_profile_technicians:
                self._alert_incomplete_profiles(incomplete_profile_technicians, correlation_id)
            
            # Check if any eligible technicians available
            if not eligible_technicians:
                logger.warning('No eligible technicians with complete profiles', 
                             order_id=order_id, 
                             total_technicians=len(all_technicians),
                             incomplete_profiles=len(incomplete_profile_technicians))
                
                return {
                    'success': False,
                    'message': f'No eligible technicians available. {len(incomplete_profile_technicians)} technicians have incomplete profiles.',
                    'incomplete_profile_count': len(incomplete_profile_technicians)
                }
            
            # Assign nearest technician
            assignment_result = self.assignment_service.assign_technician({
                'orderId': order_id,
                'serviceLocation': service_location
            }, correlation_id)
            
            logger.end_operation('process_order_placed_event', success=True, 
                               order_id=order_id, 
                               assigned=assignment_result.get('success', False))
            
            return assignment_result
            
        except Exception as e:
            logger.error('Error processing order placed event', error=str(e), correlation_id=correlation_id)
            logger.end_operation('process_order_placed_event', success=False)
            raise
    
    def _get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order from DynamoDB"""
        try:
            response = self.orders_table.get_item(
                Key={
                    'PK': f'ORDER#{order_id}',
                    'SK': f'ORDER#{order_id}'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error('Error getting order', order_id=order_id, error=str(e))
            return None
    
    def _get_all_technicians(self) -> List[Dict[str, Any]]:
        """Get all technicians from DynamoDB"""
        try:
            # Scan technicians table (in production, use GSI for better performance)
            response = self.technicians_table.scan()
            
            technicians = []
            for item in response.get('Items', []):
                # Convert DynamoDB item to technician dict
                technician = {
                    'id': item.get('technicianId'),
                    'userId': item.get('userId'),
                    'name': item.get('name'),
                    'phone': item.get('phone'),
                    'email': item.get('email'),
                    'location': item.get('location', {}),
                    'address': item.get('address', {}),
                    'skills': item.get('skills', []),
                    'available': item.get('available', False),
                    'rating': float(item.get('rating', 0))
                }
                technicians.append(technician)
            
            return technicians
            
        except Exception as e:
            logger.error('Error getting technicians', error=str(e))
            return []
    
    def _alert_incomplete_profiles(self, incomplete_technicians: List[Dict[str, Any]], correlation_id: str):
        """Send alerts to technicians with incomplete profiles"""
        logger.info('Alerting technicians with incomplete profiles', 
                   count=len(incomplete_technicians))
        
        for item in incomplete_technicians:
            technician = item['technician']
            missing_fields = item['missing_fields']
            
            try:
                # Send SNS notification
                if SNS_TOPIC_ARN:
                    message = {
                        'type': 'PROFILE_INCOMPLETE',
                        'technicianId': technician.get('id'),
                        'technicianName': technician.get('name', 'Unknown'),
                        'missingFields': missing_fields,
                        'message': f'Please complete your profile to be eligible for order assignments. Missing: {", ".join(missing_fields)}',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'correlationId': correlation_id
                    }
                    
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=json.dumps(message),
                        Subject='Complete Your Technician Profile',
                        MessageAttributes={
                            'type': {'DataType': 'String', 'StringValue': 'PROFILE_INCOMPLETE'},
                            'technicianId': {'DataType': 'String', 'StringValue': technician.get('id', '')}
                        }
                    )
                
                # Send email if email is available
                email = technician.get('email')
                if email and email.strip():
                    self._send_profile_completion_email(
                        email, 
                        technician.get('name', 'Technician'),
                        missing_fields
                    )
                
                logger.info('Profile completion alert sent', 
                           technician_id=technician.get('id'),
                           missing_fields=missing_fields)
                
            except Exception as e:
                logger.warning('Failed to send profile completion alert', 
                             technician_id=technician.get('id'),
                             error=str(e))
    
    def _send_profile_completion_email(self, email: str, name: str, missing_fields: List[str]):
        """Send email to technician about profile completion"""
        try:
            subject = 'Complete Your AquaChain Technician Profile'
            
            body_html = f"""
            <html>
            <head></head>
            <body>
                <h2>Complete Your Technician Profile</h2>
                <p>Hello {name},</p>
                <p>Your technician profile is incomplete. To be eligible for order assignments, please complete the following fields:</p>
                <ul>
                    {''.join(f'<li>{field.replace("_", " ").title()}</li>' for field in missing_fields)}
                </ul>
                <p>Please log in to your dashboard and update your profile to start receiving order assignments.</p>
                <p>Thank you,<br>AquaChain Team</p>
            </body>
            </html>
            """
            
            body_text = f"""
            Complete Your Technician Profile
            
            Hello {name},
            
            Your technician profile is incomplete. To be eligible for order assignments, please complete the following fields:
            
            {chr(10).join(f'- {field.replace("_", " ").title()}' for field in missing_fields)}
            
            Please log in to your dashboard and update your profile to start receiving order assignments.
            
            Thank you,
            AquaChain Team
            """
            
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': body_text},
                        'Html': {'Data': body_html}
                    }
                }
            )
            
        except Exception as e:
            logger.warning('Failed to send profile completion email', 
                         email=email, error=str(e))


# Initialize service
auto_assignment_service = AutoTechnicianAssignmentService()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for automatic technician assignment
    
    Triggered by EventBridge when order status changes to ORDER_PLACED
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        logger.info('Auto technician assignment triggered', event=event)
        
        # Extract event detail
        event_detail = event.get('detail', {})
        event_type = event_detail.get('eventType')
        
        if event_type != 'ORDER_STATUS_UPDATED':
            logger.warning('Unexpected event type', event_type=event_type)
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Event type not handled'})
            }
        
        # Check if status is ORDER_PLACED
        new_status = event_detail.get('status')
        if new_status != 'ORDER_PLACED':
            logger.info('Order status not ORDER_PLACED, skipping assignment', status=new_status)
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Status not ORDER_PLACED, skipping'})
            }
        
        # Process assignment
        result = auto_assignment_service.process_order_placed_event(event_detail, correlation_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'result': result,
                'correlationId': correlation_id
            })
        }
        
    except Exception as e:
        logger.error('Error in auto technician assignment', error=str(e), correlation_id=correlation_id)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'correlationId': correlation_id
            })
        }
