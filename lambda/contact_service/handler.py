"""
Contact Form Service Lambda Handler
Handles contact form submissions, stores in DynamoDB, and sends email notifications
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import uuid

# AWS Clients
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Environment variables
CONTACT_TABLE_NAME = os.environ.get('CONTACT_TABLE_NAME', 'aquachain-contact-submissions')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@aquachain.io')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@aquachain.io')

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for contact form submissions
    """
    try:
        # Handle OPTIONS request for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        validation_error = validate_contact_form(body)
        if validation_error:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': validation_error})
            }
        
        # Create submission record
        submission = create_submission_record(body)
        
        # Store in DynamoDB
        store_submission(submission)
        
        # Send email notifications
        send_email_notifications(submission)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': 'Contact form submitted successfully',
                'submissionId': submission['submissionId']
            })
        }
        
    except Exception as e:
        print(f"Error processing contact form: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }


def validate_contact_form(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate contact form data
    Returns error message if validation fails, None if valid
    """
    required_fields = ['name', 'email', 'message', 'inquiryType']
    
    for field in required_fields:
        if not data.get(field):
            return f"Missing required field: {field}"
    
    # Validate email format
    email = data.get('email', '')
    if '@' not in email or '.' not in email:
        return "Invalid email format"
    
    # Validate inquiry type
    valid_inquiry_types = ['technician', 'general', 'support']
    if data.get('inquiryType') not in valid_inquiry_types:
        return "Invalid inquiry type"
    
    # Validate message length
    if len(data.get('message', '')) < 10:
        return "Message must be at least 10 characters"
    
    return None


def create_submission_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a submission record with metadata
    """
    submission_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    return {
        'submissionId': submission_id,
        'name': data['name'].strip(),
        'email': data['email'].strip().lower(),
        'phone': data.get('phone', '').strip(),
        'message': data['message'].strip(),
        'inquiryType': data['inquiryType'],
        'status': 'pending',
        'createdAt': timestamp,
        'updatedAt': timestamp,
        'source': 'web_form'
    }


def store_submission(submission: Dict[str, Any]) -> None:
    """
    Store submission in DynamoDB
    """
    table = dynamodb.Table(CONTACT_TABLE_NAME)
    
    table.put_item(Item=submission)
    print(f"Stored submission: {submission['submissionId']}")


def send_email_notifications(submission: Dict[str, Any]) -> None:
    """
    Send email notifications to admin and user
    """
    try:
        # Send confirmation email to user
        send_user_confirmation_email(submission)
        
        # Send notification email to admin
        send_admin_notification_email(submission)
        
        print(f"Sent email notifications for submission: {submission['submissionId']}")
        
    except Exception as e:
        print(f"Error sending email notifications: {str(e)}")
        # Don't fail the request if email fails


def send_user_confirmation_email(submission: Dict[str, Any]) -> None:
    """
    Send confirmation email to the user
    """
    subject = "Thank you for contacting AquaChain"
    
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h2>Thank you for contacting AquaChain!</h2>
        <p>Dear {submission['name']},</p>
        <p>We have received your inquiry and will get back to you within 24 hours.</p>
        
        <h3>Your Submission Details:</h3>
        <ul>
            <li><strong>Inquiry Type:</strong> {submission['inquiryType'].replace('_', ' ').title()}</li>
            <li><strong>Submission ID:</strong> {submission['submissionId']}</li>
            <li><strong>Date:</strong> {submission['createdAt']}</li>
        </ul>
        
        <p><strong>Your Message:</strong></p>
        <p>{submission['message']}</p>
        
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated confirmation email. Please do not reply to this email.
            If you have any questions, please contact us at {ADMIN_EMAIL}
        </p>
    </body>
    </html>
    """
    
    body_text = f"""
    Thank you for contacting AquaChain!
    
    Dear {submission['name']},
    
    We have received your inquiry and will get back to you within 24 hours.
    
    Your Submission Details:
    - Inquiry Type: {submission['inquiryType'].replace('_', ' ').title()}
    - Submission ID: {submission['submissionId']}
    - Date: {submission['createdAt']}
    
    Your Message:
    {submission['message']}
    
    ---
    This is an automated confirmation email. Please do not reply to this email.
    If you have any questions, please contact us at {ADMIN_EMAIL}
    """
    
    ses_client.send_email(
        Source=FROM_EMAIL,
        Destination={'ToAddresses': [submission['email']]},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': body_text},
                'Html': {'Data': body_html}
            }
        }
    )


def send_admin_notification_email(submission: Dict[str, Any]) -> None:
    """
    Send notification email to admin
    """
    subject = f"New Contact Form Submission - {submission['inquiryType'].title()}"
    
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h2>New Contact Form Submission</h2>
        
        <h3>Contact Information:</h3>
        <ul>
            <li><strong>Name:</strong> {submission['name']}</li>
            <li><strong>Email:</strong> {submission['email']}</li>
            <li><strong>Phone:</strong> {submission.get('phone', 'Not provided')}</li>
            <li><strong>Inquiry Type:</strong> {submission['inquiryType'].replace('_', ' ').title()}</li>
        </ul>
        
        <h3>Message:</h3>
        <p>{submission['message']}</p>
        
        <hr>
        <p style="color: #666; font-size: 12px;">
            <strong>Submission ID:</strong> {submission['submissionId']}<br>
            <strong>Submitted At:</strong> {submission['createdAt']}<br>
            <strong>Source:</strong> {submission['source']}
        </p>
    </body>
    </html>
    """
    
    body_text = f"""
    New Contact Form Submission
    
    Contact Information:
    - Name: {submission['name']}
    - Email: {submission['email']}
    - Phone: {submission.get('phone', 'Not provided')}
    - Inquiry Type: {submission['inquiryType'].replace('_', ' ').title()}
    
    Message:
    {submission['message']}
    
    ---
    Submission ID: {submission['submissionId']}
    Submitted At: {submission['createdAt']}
    Source: {submission['source']}
    """
    
    ses_client.send_email(
        Source=FROM_EMAIL,
        Destination={'ToAddresses': [ADMIN_EMAIL]},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': body_text},
                'Html': {'Data': body_html}
            }
        }
    )
