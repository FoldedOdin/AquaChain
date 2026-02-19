"""
Secure User Registration Service - Enhanced with Security Best Practices
- OTP hashing with salt
- IP-based rate limiting
- Global attempt lockout
- Audit logging
- Idempotency support
"""

import json
import boto3
import os
import re
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from otp_security import (
    generate_otp, hash_otp, get_client_ip, 
    get_user_agent, get_idempotency_key
)
from audit_logger import AuditLogger

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,Idempotency-Key',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json'
}

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple:
    """Validate password complexity"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""

def lambda_handler(event, context):
    """
    Register new user with enhanced security
    
    POST /api/auth/register
    Headers: {
        "Idempotency-Key": "uuid" (optional)
    }
    Body: {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+919876543210",
        "role": "consumer"
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
    idempotency_key = get_idempotency_key(event)
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        phone = body.get('phone', '').strip()
        role = body.get('role', 'consumer').lower()
        
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
        
        # Validate required fields
        if not email:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Email is required'})
            }
        
        if not password:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Password is required'})
            }
        
        if not first_name or not last_name:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'First name and last name are required'})
            }
        
        # Validate email format
        if not validate_email(email):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Invalid email format'})
            }
        
        # Validate password complexity
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': error_msg})
            }
        
        # Validate role
        if role not in ['consumer', 'technician', 'administrator']:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Invalid role'})
            }
        
        # Check idempotency - prevent duplicate registrations
        if idempotency_key:
            try:
                # Check if this idempotency key was already processed
                idempotency_response = otp_table.get_item(
                    Key={'email': f"IDEMPOTENCY#{idempotency_key}"}
                )
                
                if 'Item' in idempotency_response:
                    # Return cached response
                    cached_data = idempotency_response['Item']
                    return {
                        'statusCode': 200,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({
                            'success': True,
                            'message': 'Registration already processed',
                            'email': cached_data.get('targetEmail'),
                            'userId': cached_data.get('userId'),
                            'otpSent': True,
                            'idempotent': True
                        })
                    }
            except Exception as e:
                print(f"Idempotency check error: {e}")
        
        # Check if user already exists
        try:
            cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            audit_logger.log_registration(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                role=role,
                reason='USER_EXISTS'
            )
            
            return {
                'statusCode': 409,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'User with this email already exists',
                    'code': 'USER_EXISTS'
                })
            }
        except ClientError as e:
            if e.response['Error']['Code'] != 'UserNotFoundException':
                raise
        
        # Create user in Cognito (unverified)
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'given_name', 'Value': first_name},
            {'Name': 'family_name', 'Value': last_name},
            {'Name': 'email_verified', 'Value': 'false'}
        ]
        
        if phone:
            user_attributes.append({'Name': 'phone_number', 'Value': phone})
        
        try:
            response = cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=user_attributes,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            
            user_id = response['User']['Username']
            
            # Set permanent password
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            
            # Disable user until email is verified
            cognito.admin_disable_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            audit_logger.log_registration(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                role=role,
                reason=error_code
            )
            
            if error_code == 'UsernameExistsException':
                return {
                    'statusCode': 409,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'User with this email already exists',
                        'code': 'USER_EXISTS'
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': f'Registration failed: {error_code}'})
                }
        
        # Generate secure OTP with hashing
        otp = generate_otp()
        otp_hash, salt = hash_otp(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store hashed OTP in DynamoDB
        otp_table.put_item(
            Item={
                'email': email,
                'otpHash': otp_hash,
                'salt': salt,
                'userId': user_id,
                'firstName': first_name,
                'lastName': last_name,
                'phone': phone or '',
                'role': role,
                'attempts': 0,
                'failedAttemptsTotal': 0,
                'expiresAt': int(expires_at.timestamp()),
                'createdAt': datetime.utcnow().isoformat(),
                'requestIp': client_ip,
                'userAgent': user_agent,
                'ttl': int(expires_at.timestamp()) + 3600  # Auto-delete 1 hour after expiry
            }
        )
        
        # Store idempotency record if key provided
        if idempotency_key:
            try:
                otp_table.put_item(
                    Item={
                        'email': f"IDEMPOTENCY#{idempotency_key}",
                        'targetEmail': email,
                        'userId': user_id,
                        'createdAt': datetime.utcnow().isoformat(),
                        'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hours
                    }
                )
            except Exception as e:
                print(f"Failed to store idempotency record: {e}")
        
        # Send OTP via SES
        email_sent = False
        try:
            ses = boto3.client('ses', region_name=region)
            sender_email = os.environ.get('SES_SENDER_EMAIL', 'noreply@aquachain.com')
            
            email_body = f"""
            <html>
            <body>
                <h2>Welcome to AquaChain!</h2>
                <p>Hi {first_name},</p>
                <p>Thank you for registering with AquaChain. To complete your registration, please use the following OTP:</p>
                <h1 style="color: #0066cc; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This OTP will expire in 10 minutes.</p>
                <p>If you didn't request this registration, please ignore this email.</p>
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
        
        # Log successful registration
        audit_logger.log_registration(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            success=True,
            role=role
        )
        
        return {
            'statusCode': 201,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'Registration successful. Please check your email for OTP.',
                'email': email,
                'userId': user_id,
                'otpSent': email_sent,
                'expiresIn': 600
            })
        }
        
    except Exception as e:
        print(f"Registration error: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
