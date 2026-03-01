"""
Secure OTP Request Service - Enhanced with Security Best Practices
- IP-based rate limiting
- Hashed OTP storage
- Audit logging
- Smart cooldown tracking
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from otp_security import (
    generate_otp, hash_otp, check_rate_limit,
    get_client_ip, get_user_agent
)
from audit_logger import AuditLogger

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json'
}

def lambda_handler(event, context):
    """
    Request new OTP with enhanced security
    
    POST /api/auth/request-otp
    Body: {
        "email": "user@example.com"
    }
    """
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    # Extract request metadata
    client_ip = get_client_ip(event)
    user_agent = get_user_agent(event)
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        
        if not email:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # Get configuration
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        region = os.environ.get('REGION', 'ap-south-1')
        otp_table_name = os.environ.get('OTP_TABLE_NAME', 'AquaChain-OTP')
        
        if not user_pool_id:
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Service configuration error'})
            }
        
        # Initialize services
        cognito = boto3.client('cognito-idp', region_name=region)
        dynamodb = boto3.resource('dynamodb', region_name=region)
        otp_table = dynamodb.Table(otp_table_name)
        audit_logger = AuditLogger(region=region)
        
        # Check if user exists in Cognito
        try:
            user_response = cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            # Check if already verified
            email_verified = False
            user_enabled = user_response.get('Enabled', False)
            
            for attr in user_response.get('UserAttributes', []):
                if attr['Name'] == 'email_verified':
                    email_verified = attr['Value'].lower() == 'true'
                    break
            
            if email_verified and user_enabled:
                audit_logger.log_otp_request(
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    success=False,
                    reason='ALREADY_VERIFIED'
                )
                
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'Email already verified',
                        'code': 'ALREADY_VERIFIED'
                    })
                }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                audit_logger.log_otp_request(
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    success=False,
                    reason='USER_NOT_FOUND'
                )
                
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'User not found. Please register first.',
                        'code': 'USER_NOT_FOUND'
                    })
                }
            raise
        
        # Check rate limiting - per email
        try:
            otp_response = otp_table.get_item(Key={'email': email})
            
            if 'Item' in otp_response:
                existing_otp = otp_response['Item']
                created_at_str = existing_otp.get('createdAt', '')
                
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    is_allowed, remaining = check_rate_limit(created_at, cooldown_seconds=120)
                    
                    if not is_allowed:
                        audit_logger.log_rate_limit(
                            email=email,
                            ip_address=client_ip,
                            user_agent=user_agent,
                            event_type='OTP_REQUESTED',
                            remaining_seconds=remaining
                        )
                        
                        return {
                            'statusCode': 429,
                            'headers': CORS_HEADERS,
                            'body': json.dumps({
                                'error': f'Please wait {remaining} seconds before requesting a new OTP',
                                'code': 'RATE_LIMITED',
                                'remainingSeconds': remaining
                            })
                        }
        except Exception as e:
            print(f"Error checking rate limit: {e}")
        
        # Check IP-based rate limiting (prevent spam from single IP)
        try:
            # Query for recent OTP requests from this IP
            # Note: This requires a GSI on requestIp if we want efficient queries
            # For now, we'll implement a simple check
            ip_key = f"IP#{client_ip}"
            ip_response = otp_table.get_item(Key={'email': ip_key})
            
            if 'Item' in ip_response:
                ip_data = ip_response['Item']
                last_request_str = ip_data.get('lastRequest', '')
                request_count = int(ip_data.get('requestCount', 0))
                
                if last_request_str:
                    last_request = datetime.fromisoformat(last_request_str)
                    time_window = datetime.utcnow() - timedelta(minutes=5)
                    
                    # Reset counter if outside 5-minute window
                    if last_request < time_window:
                        request_count = 0
                    
                    # Max 5 requests per IP per 5 minutes
                    if request_count >= 5:
                        audit_logger.log_rate_limit(
                            email=email,
                            ip_address=client_ip,
                            user_agent=user_agent,
                            event_type='OTP_REQUESTED',
                            remaining_seconds=300
                        )
                        
                        return {
                            'statusCode': 429,
                            'headers': CORS_HEADERS,
                            'body': json.dumps({
                                'error': 'Too many OTP requests from this IP. Please try again later.',
                                'code': 'IP_RATE_LIMITED'
                            })
                        }
        except Exception as e:
            print(f"Error checking IP rate limit: {e}")
        
        # Get user details from Cognito
        user_id = user_response['Username']
        first_name = ''
        last_name = ''
        phone = ''
        
        for attr in user_response.get('UserAttributes', []):
            if attr['Name'] == 'given_name':
                first_name = attr['Value']
            elif attr['Name'] == 'family_name':
                last_name = attr['Value']
            elif attr['Name'] == 'phone_number':
                phone = attr['Value']
        
        # Generate secure OTP with hashing
        otp = generate_otp()
        otp_hash, salt = hash_otp(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        now = datetime.utcnow()
        
        # Store hashed OTP in DynamoDB
        otp_table.put_item(
            Item={
                'email': email,
                'otpHash': otp_hash,
                'salt': salt,
                'userId': user_id,
                'firstName': first_name,
                'lastName': last_name,
                'phone': phone,
                'role': 'consumer',
                'attempts': 0,
                'failedAttemptsTotal': 0,
                'expiresAt': int(expires_at.timestamp()),
                'createdAt': now.isoformat(),
                'requestIp': client_ip,
                'userAgent': user_agent,
                'ttl': int(expires_at.timestamp()) + 3600
            }
        )
        
        # Update IP rate limiting counter
        try:
            ip_key = f"IP#{client_ip}"
            ip_ttl = int((now + timedelta(minutes=10)).timestamp())
            
            otp_table.put_item(
                Item={
                    'email': ip_key,
                    'lastRequest': now.isoformat(),
                    'requestCount': 1,
                    'ttl': ip_ttl
                },
                ConditionExpression='attribute_not_exists(email)'
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Item exists, increment counter
                try:
                    otp_table.update_item(
                        Key={'email': ip_key},
                        UpdateExpression='SET requestCount = requestCount + :inc, lastRequest = :now, #ttl = :ttl',
                        ExpressionAttributeNames={'#ttl': 'ttl'},
                        ExpressionAttributeValues={
                            ':inc': 1,
                            ':now': now.isoformat(),
                            ':ttl': ip_ttl
                        }
                    )
                except Exception as update_error:
                    print(f"Failed to update IP counter: {update_error}")
        except Exception as e:
            print(f"Failed to track IP rate limit: {e}")
        
        # Send OTP via SES
        email_sent = False
        try:
            ses = boto3.client('ses', region_name=region)
            sender_email = os.environ.get('SES_SENDER_EMAIL', 'noreply@aquachain.com')
            
            email_body = f"""
            <html>
            <body>
                <h2>AquaChain Email Verification</h2>
                <p>Hi {first_name},</p>
                <p>You requested a new OTP for email verification. Please use the following code:</p>
                <h1 style="color: #0066cc; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This OTP will expire in 10 minutes.</p>
                <p>If you didn't request this OTP, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The AquaChain Team</p>
            </body>
            </html>
            """
            
            ses.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'AquaChain - Email Verification OTP'},
                    'Body': {'Html': {'Data': email_body}}
                }
            )
            
            print(f"OTP sent to {email}")
            email_sent = True
            
        except ClientError as e:
            print(f"SES error: {e}")
        
        # Log successful OTP request
        audit_logger.log_otp_request(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        # Calculate actual cooldown remaining for smart frontend timer
        cooldown_remaining = 120  # Default 2 minutes
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'OTP sent to your email' if email_sent else 'OTP generated (email delivery pending)',
                'email': email,
                'expiresIn': 600,
                'cooldownRemaining': cooldown_remaining,
                'emailSent': email_sent
            })
        }
        
    except Exception as e:
        print(f"Request OTP error: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
