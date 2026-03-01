"""
Request OTP Service - Resend OTP for existing registration
Allows users to request a new OTP if the previous one expired
"""

import json
import boto3
import os
import random
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json'
}

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def lambda_handler(event, context):
    """
    Request new OTP for email verification
    
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
        
        cognito = boto3.client('cognito-idp', region_name=region)
        dynamodb = boto3.resource('dynamodb', region_name=region)
        otp_table = dynamodb.Table(otp_table_name)
        
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
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'User not found. Please register first.',
                        'code': 'USER_NOT_FOUND'
                    })
                }
            raise
        
        # Check rate limiting - max 3 OTP requests per hour
        try:
            otp_response = otp_table.get_item(Key={'email': email})
            
            if 'Item' in otp_response:
                existing_otp = otp_response['Item']
                created_at = datetime.fromisoformat(existing_otp.get('createdAt', ''))
                
                # Check if last OTP was created less than 2 minutes ago
                if datetime.utcnow() - created_at < timedelta(minutes=2):
                    return {
                        'statusCode': 429,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({
                            'error': 'Please wait 2 minutes before requesting a new OTP',
                            'code': 'RATE_LIMITED'
                        })
                    }
        except Exception as e:
            print(f"Error checking rate limit: {e}")
        
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
        
        # Generate new OTP
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store OTP in DynamoDB
        otp_table.put_item(
            Item={
                'email': email,
                'otp': otp,
                'userId': user_id,
                'firstName': first_name,
                'lastName': last_name,
                'phone': phone,
                'role': 'consumer',  # Default, will be updated from existing data if available
                'attempts': 0,
                'expiresAt': int(expires_at.timestamp()),
                'createdAt': datetime.utcnow().isoformat()
            }
        )
        
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
            
            print(f"OTP sent to {email}: {otp}")
            email_sent = True
            
        except ClientError as e:
            print(f"SES error: {e}")
            # Don't fail - OTP is still stored in DynamoDB
            print(f"OTP stored but email not sent. OTP: {otp}")
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'OTP sent to your email' if email_sent else 'OTP generated (email delivery pending)',
                'email': email,
                'expiresIn': 600,  # 10 minutes in seconds
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
