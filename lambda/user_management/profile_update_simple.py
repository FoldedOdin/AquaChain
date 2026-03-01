"""
Simple, reliable profile update handler
Minimal dependencies, clear error handling
"""
import json
import boto3
import base64
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
users_table = dynamodb.Table('AquaChain-Users')

def cors_response(status_code, body):
    """Return CORS-enabled response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body)
    }

def extract_email_from_token(auth_header):
    """Extract email from JWT token"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    try:
        token = auth_header.split(' ')[1]
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        token_data = json.loads(decoded)
        return token_data.get('email')
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def find_user_by_email(email):
    """Find user by email using scan"""
    try:
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email},
            Limit=1
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"Error finding user: {e}")
        return None

def lambda_handler(event, context):
    """Handle profile requests (GET and PUT)"""
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        # Extract email from token
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        email = extract_email_from_token(auth_header)
        
        if not email:
            return cors_response(401, {'error': 'Unauthorized', 'message': 'Invalid or missing token'})
        
        # Find user
        user = find_user_by_email(email)
        if not user:
            return cors_response(404, {'error': 'Not Found', 'message': 'User not found'})
        
        user_id = user['userId']
        
        # Handle GET request - return current profile
        if event.get('httpMethod') == 'GET':
            # Return user data with profile properly structured
            return cors_response(200, {
                'success': True,
                'profile': {
                    'userId': user.get('userId'),
                    'email': user.get('email'),
                    'role': user.get('role'),
                    'firstName': user.get('profile', {}).get('firstName', ''),
                    'lastName': user.get('profile', {}).get('lastName', ''),
                    'phone': user.get('profile', {}).get('phone', ''),
                    'address': user.get('profile', {}).get('address'),
                    'deviceIds': user.get('deviceIds', []),
                    'preferences': user.get('preferences', {}),
                    'createdAt': user.get('createdAt'),
                    'updatedAt': user.get('updatedAt')
                }
            })
        
        # Handle PUT request - update profile
        if event.get('httpMethod') != 'PUT':
            return cors_response(405, {'error': 'Method Not Allowed'})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Build update expression
        update_parts = []
        expr_values = {}
        
        if 'firstName' in body:
            update_parts.append('profile.firstName = :firstName')
            expr_values[':firstName'] = body['firstName']
        
        if 'lastName' in body:
            update_parts.append('profile.lastName = :lastName')
            expr_values[':lastName'] = body['lastName']
        
        if 'phone' in body:
            update_parts.append('profile.phone = :phone')
            expr_values[':phone'] = body['phone']
        
        if 'address' in body:
            update_parts.append('profile.address = :address')
            expr_values[':address'] = body['address']
        
        # Always update timestamp
        update_parts.append('updatedAt = :updatedAt')
        expr_values[':updatedAt'] = datetime.utcnow().isoformat()
        
        if not update_parts:
            return cors_response(400, {'error': 'Bad Request', 'message': 'No fields to update'})
        
        # Update DynamoDB
        update_expression = 'SET ' + ', '.join(update_parts)
        
        response = users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_user = response['Attributes']
        
        return cors_response(200, {
            'success': True,
            'message': 'Profile updated successfully',
            'profile': updated_user
        })
        
    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return cors_response(500, {'error': 'Database Error', 'message': str(e)})
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return cors_response(500, {'error': 'Internal Server Error', 'message': str(e)})
