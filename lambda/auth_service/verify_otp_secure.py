"""
Secure OTP Verification Service - Enhanced with Security Best Practices
- Constant-time OTP comparison
- Global attempt lockout
- Audit logging
- IP tracking
"""

import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from otp_security import (
    verify_otp_hash, should_lockout, is_locked_out,
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
    Verify OTP with enhanced security
    
    POST /api/auth/verify-otp
    Body: {
        "email": "user@example.com",
        "otp": "123456"
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
        otp = body.get('otp', '').strip()
        
        if not email or not otp:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Email and OTP are required'})
            }
        
        # Get configuration
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        region = os.environ.get('REGION', 'ap-south-1')
        otp_table_name = os.environ.get('OTP_TABLE_NAME', 'AquaChain-OTP')
        users_table_name = os.environ.get('USERS_TABLE_NAME', 'AquaChain-Users')
        
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
        users_table = dynamodb.Table(users_table_name)
        audit_logger = AuditLogger(region=region)
        
        # Get OTP from DynamoDB
        try:
            otp_response = otp_table.get_item(Key={'email': email})
            
            if 'Item' not in otp_response:
                audit_logger.log_otp_verification(
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    success=False,
                    attempts=0,
                    reason='OTP_NOT_FOUND'
                )
                
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'No OTP found. Please request a new one.',
                        'code': 'OTP_NOT_FOUND'
                    })
                }
            
            otp_data = otp_response['Item']
            
        except Exception as e:
            print(f"Error retrieving OTP: {e}")
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Failed to retrieve OTP'})
            }
        
        # Check if OTP expired
        expires_at = int(otp_data.get('expiresAt', 0))
        if datetime.utcnow().timestamp() > expires_at:
            otp_table.delete_item(Key={'email': email})
            
            audit_logger.log_otp_verification(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                attempts=int(otp_data.get('attempts', 0)),
                reason='OTP_EXPIRED'
            )
            
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'OTP expired. Please request a new one.',
                    'code': 'OTP_EXPIRED'
                })
            }
        
        # Check global lockout
        lock_until_str = otp_data.get('lockUntil')
        if lock_until_str:
            lock_until = datetime.fromisoformat(lock_until_str)
            locked, remaining = is_locked_out(lock_until)
            
            if locked:
                audit_logger.log_otp_verification(
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    success=False,
                    attempts=int(otp_data.get('failedAttemptsTotal', 0)),
                    reason='ACCOUNT_LOCKED'
                )
                
                return {
                    'statusCode': 429,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': f'Account temporarily locked. Try again in {remaining} seconds.',
                        'code': 'ACCOUNT_LOCKED',
                        'remainingSeconds': remaining
                    })
                }
        
        # Check per-OTP attempts
        attempts = int(otp_data.get('attempts', 0))
        if attempts >= 3:
            otp_table.delete_item(Key={'email': email})
            
            audit_logger.log_otp_verification(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                attempts=attempts,
                reason='MAX_ATTEMPTS_EXCEEDED'
            )
            
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Too many failed attempts. Please request a new OTP.',
                    'code': 'MAX_ATTEMPTS_EXCEEDED'
                })
            }
        
        # Verify OTP using constant-time comparison
        stored_hash = otp_data.get('otpHash', '')
        salt = otp_data.get('salt', '')
        
        # Fallback for old plaintext OTPs (backward compatibility)
        if not stored_hash and 'otp' in otp_data:
            is_valid = (otp == otp_data.get('otp', ''))
        else:
            is_valid = verify_otp_hash(otp, stored_hash, salt)
        
        if not is_valid:
            # Increment attempts
            failed_attempts_total = int(otp_data.get('failedAttemptsTotal', 0)) + 1
            
            update_expr = 'SET attempts = attempts + :inc, failedAttemptsTotal = :total'
            expr_values = {':inc': 1, ':total': failed_attempts_total}
            
            # Check if should lockout
            should_lock, lock_until = should_lockout(failed_attempts_total)
            
            if should_lock:
                update_expr += ', lockUntil = :lockUntil'
                expr_values[':lockUntil'] = lock_until.isoformat()
                
                audit_logger.log_lockout(
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    failed_attempts=failed_attempts_total,
                    lock_duration_minutes=15
                )
            
            otp_table.update_item(
                Key={'email': email},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            audit_logger.log_otp_verification(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                attempts=attempts + 1,
                reason='INVALID_OTP'
            )
            
            remaining_attempts = 3 - (attempts + 1)
            
            if should_lock:
                return {
                    'statusCode': 429,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'Too many failed attempts. Account locked for 15 minutes.',
                        'code': 'ACCOUNT_LOCKED',
                        'lockDurationMinutes': 15
                    })
                }
            
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': f'Invalid OTP. {remaining_attempts} attempts remaining.',
                    'code': 'INVALID_OTP',
                    'remainingAttempts': remaining_attempts
                })
            }
        
        # OTP is valid - proceed with account activation
        user_id = otp_data.get('userId')
        first_name = otp_data.get('firstName', '')
        last_name = otp_data.get('lastName', '')
        phone = otp_data.get('phone', '')
        role = otp_data.get('role', 'consumer')
        
        try:
            # Update Cognito user
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
            )
            
            # Enable user account
            cognito.admin_enable_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            # Add user to group
            group_name = f"{role}s"
            try:
                cognito.admin_add_user_to_group(
                    UserPoolId=user_pool_id,
                    Username=email,
                    GroupName=group_name
                )
            except ClientError as e:
                print(f"Warning: Failed to add user to group {group_name}: {e}")
            
        except ClientError as e:
            print(f"Cognito error: {e}")
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Failed to activate account'})
            }
        
        # Create user profile in DynamoDB
        try:
            profile_data = {
                'userId': user_id,
                'email': email,
                'role': role,
                'profile': {
                    'firstName': first_name,
                    'lastName': last_name,
                    'phone': phone,
                    'address': {}
                },
                'deviceIds': [],
                'preferences': {
                    'notifications': {
                        'push': True,
                        'sms': True,
                        'email': True
                    },
                    'theme': 'auto',
                    'language': 'en'
                },
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat(),
                'emailVerified': True,
                'accountStatus': 'active'
            }
            
            if role == 'technician':
                profile_data['workSchedule'] = {
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'},
                    'saturday': {'start': '00:00', 'end': '00:00'},
                    'sunday': {'start': '00:00', 'end': '00:00'}
                }
                profile_data['performanceScore'] = 100.0
                profile_data['availabilityStatus'] = 'available'
            
            users_table.put_item(Item=profile_data)
            
        except Exception as e:
            print(f"DynamoDB error: {e}")
        
        # Delete OTP from table
        try:
            otp_table.delete_item(Key={'email': email})
        except Exception as e:
            print(f"Warning: Failed to delete OTP: {e}")
        
        # Log successful verification
        audit_logger.log_otp_verification(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            success=True,
            attempts=attempts + 1
        )
        
        # Send welcome email
        try:
            ses = boto3.client('ses', region_name=region)
            sender_email = os.environ.get('SES_SENDER_EMAIL', 'noreply@aquachain.com')
            
            email_body = f"""
            <html>
            <body>
                <h2>Welcome to AquaChain!</h2>
                <p>Hi {first_name},</p>
                <p>Your email has been successfully verified and your account is now active.</p>
                <p>You can now log in to your AquaChain dashboard and start monitoring your water quality.</p>
                <br>
                <p>Best regards,<br>The AquaChain Team</p>
            </body>
            </html>
            """
            
            ses.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'Welcome to AquaChain - Account Activated'},
                    'Body': {'Html': {'Data': email_body}}
                }
            )
            
        except Exception as e:
            print(f"Warning: Failed to send welcome email: {e}")
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'Email verified successfully. You can now log in.',
                'userId': user_id,
                'email': email,
                'verified': True
            })
        }
        
    except Exception as e:
        print(f"Verify OTP error: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
