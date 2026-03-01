"""
Razorpay Webhook Handler Lambda Function

This Lambda function handles incoming webhooks from Razorpay for payment status updates.
It verifies webhook signatures and processes payment events.

Events Handled:
- payment.captured: Payment successfully captured
- payment.failed: Payment failed
- payment.authorized: Payment authorized (for manual capture)
- order.paid: Order fully paid

Security:
- HMAC SHA256 signature verification
- Webhook secret stored in AWS Secrets Manager
"""

import json
import logging
import os
from typing import Dict, Any

from payment_service import PaymentService

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize payment service
payment_service = PaymentService()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Razorpay webhooks
    
    Args:
        event: API Gateway event containing webhook payload
        context: Lambda context
        
    Returns:
        API Gateway response with status code and body
    """
    try:
        logger.info("Received Razorpay webhook")
        
        # Extract webhook signature from headers
        headers = event.get('headers', {})
        signature = headers.get('X-Razorpay-Signature') or headers.get('x-razorpay-signature')
        
        if not signature:
            logger.warning("Webhook received without signature")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing webhook signature'
                })
            }
        
        # Parse webhook payload
        try:
            if isinstance(event.get('body'), str):
                payload = json.loads(event['body'])
            else:
                payload = event.get('body', {})
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid JSON payload'
                })
            }
        
        # Log event type for debugging
        event_type = payload.get('event', 'unknown')
        logger.info(f"Processing webhook event: {event_type}")
        
        # Process webhook using payment service
        result = payment_service.handle_payment_webhook(payload, signature)
        
        if result.get('success'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Webhook processed successfully'
                })
            }
        else:
            # Signature verification failed or processing error
            status_code = 401 if 'signature' in result.get('error', '').lower() else 500
            return {
                'statusCode': status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': result.get('error', 'Webhook processing failed')
                })
            }
            
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }
