"""
User registration and profile management service for AquaChain.
Implements user registration workflow with email verification and profile management.
Requirements: 8.1, 13.1
"""

import json
import boto3
import logging
import uuid
import sys
import os
import random
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from datetime import datetime, time, timedelta
import re

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import error handling
from errors import ValidationError, AuthenticationError, DatabaseError, ResourceNotFoundError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Import cache service
from cache_service import get_cache_service

# Import audit logging
from audit_logger import audit_logger

# Import CORS utilities
from cors_utils import handle_options, cors_response, success_response, error_response

# Configure structured logging
logger = get_logger(__name__, service='user-management')

class UserManagementService:
    """
    Service for managing user registration, profiles, and device associations.
    Implements requirement 8.1 for user registration workflow with email verification.
    """
    
    def __init__(self, user_pool_id: str, client_id: str, region: str = 'us-east-1'):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.users_table = self.dynamodb.Table('aquachain-users')
        self.cache = get_cache_service()
    
    def register_user(self, email: str, password: str, first_name: str, 
                     last_name: str, phone: str, role: str = 'consumer',
                     address: Optional[Dict] = None) -> Dict:
        """
        Register a new user with email verification.
        Implements requirement 8.1 for user registration workflow.
        """
        try:
            # Validate input
            if not self._validate_email(email):
                raise ValidationError("Invalid email format", details={'email': email})
            
            if not self._validate_password(password):
                raise ValidationError("Password does not meet complexity requirements")
            
            if role not in ['consumer', 'technician', 'administrator']:
                raise ValidationError("Invalid role specified", details={'role': role})
            
            # Create user in Cognito
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'given_name', 'Value': first_name},
                {'Name': 'family_name', 'Value': last_name},
                {'Name': 'phone_number', 'Value': phone},
                {'Name': 'custom:role', 'Value': role}
            ]
            
            response = self.cognito_client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=user_attributes,
                TemporaryPassword=password,
                MessageAction='SUPPRESS',  # We'll handle verification ourselves
                ForceAliasCreation=False
            )
            
            user_id = response['User']['Username']
            
            # Add user to appropriate group
            self.cognito_client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=user_id,
                GroupName=f"{role}s"  # consumers, technicians, administrators
            )
            
            # Set permanent password
            self.cognito_client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=user_id,
                Password=password,
                Permanent=True
            )
            
            # Create user profile in DynamoDB
            profile_data = {
                'userId': user_id,
                'email': email,
                'role': role,
                'profile': {
                    'firstName': first_name,
                    'lastName': last_name,
                    'phone': phone,
                    'address': address or {}
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
                'updatedAt': datetime.utcnow().isoformat()
            }
            
            # Add role-specific fields
            if role == 'technician':
                profile_data['workSchedule'] = self._get_default_work_schedule()
                profile_data['performanceScore'] = 100.0  # Default score
                profile_data['availabilityStatus'] = 'available'
            
            # Store in DynamoDB
            self.users_table.put_item(Item=profile_data)
            
            # Send verification email
            self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            logger.info(f"User registered successfully: {user_id}")
            
            # Log user creation for audit trail
            # Note: request_context would be passed from Lambda handler
            
            return {
                'userId': user_id,
                'email': email,
                'role': role,
                'status': 'registered',
                'emailVerificationRequired': True
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                raise ValidationError("User with this email already exists", details={'email': email})
            elif error_code == 'InvalidPasswordException':
                raise ValidationError("Password does not meet requirements")
            else:
                logger.error(f"Cognito error during registration: {e}")
                raise DatabaseError(f"Registration failed: {error_code}")
        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"User registration error: {e}")
            raise DatabaseError(f"User registration failed: {str(e)}")
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get user profile from DynamoDB with caching.
        """
        cache_key = f"user:profile:{user_id}"
        
        try:
            # Try cache first
            cached_profile = self.cache.get(cache_key)
            if cached_profile:
                logger.info(f"User profile found in cache: {user_id}",
                           user_id=user_id, cache_hit=True)
                return cached_profile
            
            # Cache miss - fetch from DynamoDB
            response = self.users_table.get_item(Key={'userId': user_id})
            profile = response.get('Item')
            
            if profile:
                # Cache for 10 minutes
                self.cache.set(cache_key, profile, ttl=600)
                logger.info(f"User profile found: {user_id}",
                           user_id=user_id, cache_hit=False)
            
            return profile
        except ClientError as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Dict:
        """
        Update user profile information.
        Implements profile management API for user data updates.
        """
        try:
            # Get current profile
            current_profile = self.get_user_profile(user_id)
            if not current_profile:
                raise ResourceNotFoundError("User not found", details={'user_id': user_id})
            
            # Prepare update expression
            update_expression = "SET updatedAt = :updated_at"
            expression_values = {':updated_at': datetime.utcnow().isoformat()}
            
            # Handle profile updates
            if 'profile' in updates:
                profile_updates = updates['profile']
                for key, value in profile_updates.items():
                    if key in ['firstName', 'lastName', 'phone', 'address']:
                        update_expression += f", profile.{key} = :{key}"
                        expression_values[f':{key}'] = value
            
            # Handle preferences updates
            if 'preferences' in updates:
                pref_updates = updates['preferences']
                for key, value in pref_updates.items():
                    update_expression += f", preferences.{key} = :pref_{key}"
                    expression_values[f':pref_{key}'] = value
            
            # Handle work schedule updates (technicians only)
            if 'workSchedule' in updates and current_profile.get('role') == 'technician':
                work_schedule = updates['workSchedule']
                if self._validate_work_schedule(work_schedule):
                    update_expression += ", workSchedule = :work_schedule"
                    expression_values[':work_schedule'] = work_schedule
            
            # Handle availability status (technicians only)
            if 'availabilityStatus' in updates and current_profile.get('role') == 'technician':
                status = updates['availabilityStatus']
                if status in ['available', 'unavailable', 'available_overtime']:
                    update_expression += ", availabilityStatus = :availability_status"
                    expression_values[':availability_status'] = status
            
            # Update DynamoDB
            response = self.users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            # Invalidate cache for this user
            cache_key = f"user:profile:{user_id}"
            self.cache.delete(cache_key)
            
            # Update Cognito attributes if needed
            if 'profile' in updates:
                self._update_cognito_attributes(user_id, updates['profile'])
            
            logger.info(f"User profile updated: {user_id}", cache_invalidated=True)
            return response['Attributes']
            
        except ClientError as e:
            logger.error(f"Error updating user profile: {e}")
            raise DatabaseError("Failed to update profile", details={'user_id': user_id})
        except (ResourceNotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            raise DatabaseError(f"Profile update failed: {str(e)}")
    
    def associate_device(self, user_id: str, device_id: str) -> bool:
        """
        Associate a device with a consumer user.
        Implements device association management for consumers.
        """
        try:
            # Get current profile
            profile = self.get_user_profile(user_id)
            if not profile:
                raise ResourceNotFoundError("User not found", details={'user_id': user_id})
            
            if profile.get('role') != 'consumer':
                raise ValidationError("Only consumers can associate devices", details={'role': profile.get('role')})
            
            # Add device to user's device list
            current_devices = set(profile.get('deviceIds', []))
            current_devices.add(device_id)
            
            # Update DynamoDB
            self.users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression="SET deviceIds = :device_ids, updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':device_ids': list(current_devices),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            # Update Cognito custom attribute
            device_ids_str = ','.join(current_devices)
            self.cognito_client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=user_id,
                UserAttributes=[
                    {'Name': 'custom:deviceIds', 'Value': device_ids_str}
                ]
            )
            
            logger.info(f"Device {device_id} associated with user {user_id}")
            return True
            
        except (ResourceNotFoundError, ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Device association error: {e}")
            raise DatabaseError(f"Device association failed: {str(e)}")
    
    def remove_device_association(self, user_id: str, device_id: str) -> bool:
        """
        Remove device association from user.
        """
        try:
            # Get current profile
            profile = self.get_user_profile(user_id)
            if not profile:
                raise ResourceNotFoundError("User not found", details={'user_id': user_id})
            
            # Remove device from user's device list
            current_devices = set(profile.get('deviceIds', []))
            current_devices.discard(device_id)
            
            # Update DynamoDB
            self.users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression="SET deviceIds = :device_ids, updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':device_ids': list(current_devices),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            # Update Cognito custom attribute
            device_ids_str = ','.join(current_devices)
            self.cognito_client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=user_id,
                UserAttributes=[
                    {'Name': 'custom:deviceIds', 'Value': device_ids_str}
                ]
            )
            
            logger.info(f"Device {device_id} removed from user {user_id}")
            return True
            
        except (ResourceNotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Device removal error: {e}")
            raise DatabaseError(f"Device removal failed: {str(e)}")
    
    def setup_technician_profile(self, user_id: str, work_schedule: Dict, 
                                initial_location: Optional[Dict] = None) -> Dict:
        """
        Set up technician profile with work schedules.
        Implements requirement 13.1 for technician profile setup.
        """
        try:
            # Validate work schedule
            if not self._validate_work_schedule(work_schedule):
                raise ValidationError("Invalid work schedule format")
            
            # Get current profile
            profile = self.get_user_profile(user_id)
            if not profile:
                raise ResourceNotFoundError("User not found", details={'user_id': user_id})
            
            if profile.get('role') != 'technician':
                raise ValidationError("User is not a technician", details={'role': profile.get('role')})
            
            # Update technician-specific fields
            update_data = {
                'workSchedule': work_schedule,
                'availabilityStatus': 'available',
                'performanceScore': 100.0,
                'updatedAt': datetime.utcnow().isoformat()
            }
            
            if initial_location:
                update_data['currentLocation'] = initial_location
            
            # Update profile
            updated_profile = self.update_user_profile(user_id, update_data)
            
            logger.info(f"Technician profile setup completed: {user_id}")
            return updated_profile
            
        except (ValidationError, ResourceNotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Technician setup error: {e}")
            raise DatabaseError(f"Technician setup failed: {str(e)}")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> bool:
        """
        Validate password complexity.
        Implements requirement 8.4 for password complexity.
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _validate_work_schedule(self, schedule: Dict) -> bool:
        """Validate work schedule format."""
        required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in required_days:
            if day not in schedule:
                return False
            
            day_schedule = schedule[day]
            if not isinstance(day_schedule, dict):
                return False
            
            if 'start' not in day_schedule or 'end' not in day_schedule:
                return False
            
            # Validate time format (HH:MM)
            try:
                start_time = datetime.strptime(day_schedule['start'], '%H:%M').time()
                end_time = datetime.strptime(day_schedule['end'], '%H:%M').time()
                
                # Check if end time is after start time
                if end_time <= start_time:
                    return False
                    
            except ValueError:
                return False
        
        return True
    
    def _get_default_work_schedule(self) -> Dict:
        """Get default work schedule for technicians."""
        return {
            'monday': {'start': '09:00', 'end': '17:00'},
            'tuesday': {'start': '09:00', 'end': '17:00'},
            'wednesday': {'start': '09:00', 'end': '17:00'},
            'thursday': {'start': '09:00', 'end': '17:00'},
            'friday': {'start': '09:00', 'end': '17:00'},
            'saturday': {'start': '00:00', 'end': '00:00'},  # Off day
            'sunday': {'start': '00:00', 'end': '00:00'},    # Off day
            'overrideStatus': 'available'
        }
    
    def _update_cognito_attributes(self, user_id: str, profile_updates: Dict):
        """Update Cognito user attributes."""
        try:
            attributes = []
            
            if 'firstName' in profile_updates:
                attributes.append({'Name': 'given_name', 'Value': profile_updates['firstName']})
            
            if 'lastName' in profile_updates:
                attributes.append({'Name': 'family_name', 'Value': profile_updates['lastName']})
            
            if 'phone' in profile_updates:
                attributes.append({'Name': 'phone_number', 'Value': profile_updates['phone']})
            
            if attributes:
                self.cognito_client.admin_update_user_attributes(
                    UserPoolId=self.user_pool_id,
                    Username=user_id,
                    UserAttributes=attributes
                )
                
        except ClientError as e:
            logger.error(f"Error updating Cognito attributes: {e}")
            # Don't raise exception as DynamoDB update was successful
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email using email-index GSI (Phase 4 optimization).
        Replaces scan operations with efficient GSI query.
        """
        try:
            # Import optimized query function
            from dynamodb_queries import query_user_by_email
            
            user = query_user_by_email(email, table_name='aquachain-users')
            
            if user:
                logger.info(f"User found by email: {email}")
            else:
                logger.info(f"User not found by email: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error querying user by email: {e}")
            raise DatabaseError("Failed to query user by email", details={'email': email})
    
    def list_users_by_organization(self, organization_id: str, role: Optional[str] = None,
                                   limit: int = 100, last_key: Optional[Dict] = None) -> Dict:
        """
        List users by organization and optionally role using organization_id-role-index GSI.
        Implements pagination for efficient data retrieval (Phase 4 optimization).
        """
        try:
            # Import optimized query function
            from dynamodb_queries import query_users_by_organization_and_role
            
            result = query_users_by_organization_and_role(
                organization_id=organization_id,
                role=role,
                limit=limit,
                last_key=last_key,
                table_name='aquachain-users'
            )
            
            logger.info(f"Listed {len(result['items'])} users for organization {organization_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing users by organization: {e}")
            raise DatabaseError("Failed to list users", details={
                'organization_id': organization_id,
                'role': role
            })

def _get_request_context(event: Dict) -> Dict:
    """Extract request context for audit logging"""
    return {
        'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
        'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
        'source': 'api'
    }

def _generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def _store_otp(cache, email: str, otp: str, changes: Dict) -> None:
    """Store OTP in cache with 5-minute expiration"""
    otp_data = {
        'otp': otp,
        'changes': changes,
        'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        'attempts': 0
    }
    cache.set(f'otp:{email}', json.dumps(otp_data), ttl=300)  # 5 minutes

def _verify_otp(cache, email: str, provided_otp: str) -> tuple[bool, Optional[Dict], Optional[str]]:
    """
    Verify OTP and return (is_valid, changes, error_message)
    """
    otp_key = f'otp:{email}'
    otp_data_str = cache.get(otp_key)
    
    if not otp_data_str:
        return False, None, 'No OTP request found. Please request a new OTP.'
    
    otp_data = json.loads(otp_data_str)
    
    # Check expiration
    expires_at = datetime.fromisoformat(otp_data['expires_at'])
    if datetime.utcnow() > expires_at:
        cache.delete(otp_key)
        return False, None, 'OTP expired. Please request a new one.'
    
    # Check attempts
    if otp_data['attempts'] >= 3:
        cache.delete(otp_key)
        return False, None, 'Too many failed attempts. Please request a new OTP.'
    
    # Verify OTP
    if otp_data['otp'] != provided_otp:
        otp_data['attempts'] += 1
        cache.set(otp_key, json.dumps(otp_data), ttl=300)
        attempts_remaining = 3 - otp_data['attempts']
        return False, None, f'Invalid OTP. {attempts_remaining} attempts remaining.'
    
    # OTP is valid
    cache.delete(otp_key)
    return True, otp_data['changes'], None

# Lambda handler
@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for user management operations.
    """
    # Handle OPTIONS preflight requests for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()
    
    # Get configuration
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
    client_id = os.environ.get('COGNITO_CLIENT_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id or not client_id:
        raise ValidationError('Missing Cognito configuration')
    
    user_service = UserManagementService(user_pool_id, client_id, region)
    request_context = _get_request_context(event)
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    body = json.loads(event.get('body', '{}'))
    path_params = event.get('pathParameters', {})
        
    if http_method == 'POST' and path.endswith('/register'):
        # User registration
        result = user_service.register_user(
            email=body.get('email'),
            password=body.get('password'),
            first_name=body.get('firstName'),
            last_name=body.get('lastName'),
            phone=body.get('phone'),
            role=body.get('role', 'consumer'),
            address=body.get('address')
        )
        
        # Log user creation
        audit_logger.log_data_modification(
            user_id=result['userId'],
            resource_type='USER',
            resource_id=result['userId'],
            modification_type='CREATE',
            previous_values=None,
            new_values={
                'email': result['email'],
                'role': result['role']
            },
            request_context=request_context
        )
        
        return cors_response(201, result)
    
    elif http_method == 'GET' and '/profile/' in path:
        # Get user profile
        user_id = path_params.get('userId')
        profile = user_service.get_user_profile(user_id)
        
        if not profile:
            raise ResourceNotFoundError('User not found', details={'user_id': user_id})
        
        # Log data access
        audit_logger.log_data_access(
            user_id=event.get('userContext', {}).get('userId', user_id),
            resource_type='USER',
            resource_id=user_id,
            operation='GET',
            request_context=request_context
        )
        
        return success_response(profile)
    
    elif http_method == 'PUT' and '/profile/' in path:
        # Update user profile
        user_id = path_params.get('userId')
        
        # Get current profile for audit log
        current_profile = user_service.get_user_profile(user_id)
        
        updated_profile = user_service.update_user_profile(user_id, body)
        
        # Log data modification
        audit_logger.log_data_modification(
            user_id=event.get('userContext', {}).get('userId', user_id),
            resource_type='USER',
            resource_id=user_id,
            modification_type='UPDATE',
            previous_values=current_profile,
            new_values=body,
            request_context=request_context
        )
        
        return success_response(updated_profile)
    
    elif http_method == 'POST' and '/devices/associate' in path:
        # Associate device
        user_id = body.get('userId')
        device_id = body.get('deviceId')
        
        user_service.associate_device(user_id, device_id)
        
        return success_response({'message': 'Device associated successfully'})
    
    elif http_method == 'DELETE' and '/devices/associate' in path:
        # Remove device association
        user_id = body.get('userId')
        device_id = body.get('deviceId')
        
        user_service.remove_device_association(user_id, device_id)
        
        return success_response({'message': 'Device association removed'})
    
    elif http_method == 'POST' and '/technician/setup' in path:
        # Setup technician profile
        user_id = body.get('userId')
        work_schedule = body.get('workSchedule')
        initial_location = body.get('initialLocation')
        
        result = user_service.setup_technician_profile(
            user_id, work_schedule, initial_location
        )
        
        return success_response(result)
    
    elif http_method == 'PUT' and path.endswith('/profile/update'):
        # Direct profile update (for non-sensitive changes)
        # Get user email from Cognito claims
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        email = claims.get('email')
        
        if not email:
            raise ValidationError('Email not found in token')
        
        # Get user by email
        user = user_service.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError('User not found', details={'email': email})
        
        user_id = user.get('userId')
        
        # Get current profile for audit log
        current_profile = user_service.get_user_profile(user_id)
        
        # Update profile
        updates = body.get('updates', body)  # Support both formats
        updated_profile = user_service.update_user_profile(user_id, updates)
        
        # Log data modification
        audit_logger.log_data_modification(
            user_id=user_id,
            resource_type='USER',
            resource_id=user_id,
            modification_type='UPDATE',
            previous_values=current_profile,
            new_values=updates,
            request_context=request_context
        )
        
        return success_response({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': updated_profile
        })
    
    elif http_method == 'GET' and '/users/by-email' in path:
        # Get user by email using GSI (Phase 4 optimization)
        query_params = event.get('queryStringParameters', {})
        email = query_params.get('email')
        
        if not email:
            raise ValidationError('Email parameter required')
        
        user = user_service.get_user_by_email(email)
        
        if not user:
            raise ResourceNotFoundError('User not found', details={'email': email})
        
        return success_response(user)
    
    elif http_method == 'GET' and '/users/by-organization' in path:
        # List users by organization using GSI (Phase 4 optimization)
        query_params = event.get('queryStringParameters', {})
        organization_id = query_params.get('organizationId')
        role = query_params.get('role')
        limit = int(query_params.get('limit', 100))
        last_key = query_params.get('lastKey')
        
        if not organization_id:
            raise ValidationError('organizationId parameter required')
        
        # Parse last_key if provided
        if last_key:
            import base64
            last_key = json.loads(base64.b64decode(last_key))
        
        result = user_service.list_users_by_organization(
            organization_id=organization_id,
            role=role,
            limit=limit,
            last_key=last_key
        )
        
        # Encode last_key for response
        if result.get('last_key'):
            import base64
            result['last_key'] = base64.b64encode(
                json.dumps(result['last_key']).encode()
            ).decode()
        
        return success_response(result)
    
    elif http_method == 'POST' and path.endswith('/profile/request-otp'):
        # Request OTP for profile update
        email = body.get('email')
        changes = body.get('changes', {})
        
        if not email:
            raise ValidationError('Email is required')
        
        # Validate that user exists
        user = user_service.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError('User not found', details={'email': email})
        
        # Generate and store OTP
        otp = _generate_otp()
        cache = get_cache_service()
        _store_otp(cache, email, otp, changes)
        
        # In production, send OTP via email using SES
        # For now, log it (in dev, return it in response)
        logger.info(f"OTP generated for {email}: {otp}")
        
        # TODO: Send OTP via SES email
        # ses_client = boto3.client('ses', region_name=region)
        # ses_client.send_email(...)
        
        response_data = {
            'success': True,
            'message': 'OTP sent to your email'
        }
        
        # In development, include OTP in response for testing
        if os.environ.get('ENVIRONMENT', 'dev') == 'dev':
            response_data['devOtp'] = otp
        
        return success_response(response_data)
    
    elif http_method == 'PUT' and path.endswith('/profile/verify-and-update'):
        # Verify OTP and update profile
        otp = body.get('otp')
        updates = body.get('updates', {})
        
        # Get user email from request context or body
        email = body.get('email')
        if not email:
            # Try to get from Cognito claims in the authorizer context
            claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
            email = claims.get('email')
        
        if not email:
            raise ValidationError('Email is required')
        
        if not otp:
            raise ValidationError('OTP is required')
        
        # Verify OTP
        cache = get_cache_service()
        is_valid, stored_changes, error_msg = _verify_otp(cache, email, otp)
        
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Get user
        user = user_service.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError('User not found', details={'email': email})
        
        user_id = user.get('userId')
        
        # Get current profile for audit log
        current_profile = user_service.get_user_profile(user_id)
        
        # Update profile
        updated_profile = user_service.update_user_profile(user_id, updates)
        
        # Log data modification
        audit_logger.log_data_modification(
            user_id=user_id,
            resource_type='USER',
            resource_id=user_id,
            modification_type='UPDATE',
            previous_values=current_profile,
            new_values=updates,
            request_context=request_context
        )
        
        return success_response({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': updated_profile
        })
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')

import os