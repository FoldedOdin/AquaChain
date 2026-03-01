"""
Verify OTP Service - Final step of registration
Verifies OTP, enables user account, and creates DynamoDB profile
"""

import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json'
}

def lambda_handler(event, context):
    """
    Verify OTP and complete registration
    
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
        
        cognito = boto3.client('cognito-idp', region_name=region)
        dynamodb = boto3.resource('dynamodb', region_name=region)
        otp_table = dynamodb.Table(otp_table_name)
        users_table = dynamodb.Table(users_table_name)
        
        # Get OTP from DynamoDB
        try:
            otp_response = otp_table.get_item(Key={'email': email})
            
            if 'Item' not in otp_response:
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
            # Delete expired OTP
            otp_table.delete_item(Key={'email': email})
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'OTP expired. Please request a new one.',
                    'code': 'OTP_EXPIRED'
                })
            }
        
        # Check attempts
        attempts = int(otp_data.get('attempts', 0))
        if attempts >= 3:
            # Delete OTP after max attempts
            otp_table.delete_item(Key={'email': email})
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Too many failed attempts. Please request a new OTP.',
                    'code': 'MAX_ATTEMPTS_EXCEEDED'
                })
            }
        
        # Verify OTP
        stored_otp = otp_data.get('otp', '')
        if otp != stored_otp:
            # Increment attempts
            otp_table.update_item(
                Key={'email': email},
                UpdateExpression='SET attempts = attempts + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            remaining_attempts = 3 - (attempts + 1)
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
            # Update Cognito user - mark email as verified and enable account
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
            
            # Add user to appropriate group
            group_name = f"{role}s"  # consumers, technicians, administrators
            try:
                cognito.admin_add_user_to_group(
                    UserPoolId=user_pool_id,
                    Username=email,
                    GroupName=group_name
                )
            except ClientError as e:
                print(f"Warning: Failed to add user to group {group_name}: {e}")
                # Continue even if group assignment fails
            
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
            
            # Add role-specific fields
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
            # Account is activated in Cognito, but profile creation failed
            # User can still log in, profile will be created on first login
        
        # Delete OTP from table
        try:
            otp_table.delete_item(Key={'email': email})
        except Exception as e:
            print(f"Warning: Failed to delete OTP: {e}")
        
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
                <p>If you have any questions, feel free to contact our support team.</p>
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
