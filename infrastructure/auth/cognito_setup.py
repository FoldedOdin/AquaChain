"""
AWS Cognito User Pool setup for AquaChain authentication system.
Implements requirements 8.1 and 8.4 for secure user authentication with role-based access.
"""

import boto3
import json
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class CognitoSetup:
    def __init__(self, region='us-east-1'):
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.region = region
        
    def create_user_pool(self):
        """
        Create Cognito User Pool with email/password authentication and MFA support.
        Implements requirement 8.1 for secure authentication.
        """
        try:
            # Password policy configuration
            password_policy = {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True,
                'TemporaryPasswordValidityDays': 7
            }
            
            # MFA configuration
            mfa_configuration = 'OPTIONAL'  # Users can enable MFA
            
            # Account recovery settings
            account_recovery_setting = {
                'RecoveryMechanisms': [
                    {
                        'Priority': 1,
                        'Name': 'verified_email'
                    },
                    {
                        'Priority': 2,
                        'Name': 'verified_phone_number'
                    }
                ]
            }
            
            # User pool configuration
            user_pool_config = {
                'PoolName': 'aquachain-users',
                'Policies': {
                    'PasswordPolicy': password_policy
                },
                'LambdaConfig': {},
                'AutoVerifiedAttributes': ['email'],
                'AliasAttributes': ['email'],
                'UsernameAttributes': ['email'],
                'SmsVerificationMessage': 'Your AquaChain verification code is {####}',
                'EmailVerificationMessage': 'Welcome to AquaChain! Your verification code is {####}. Please enter this code to verify your email address and complete your registration.',
                'EmailVerificationSubject': 'Verify Your AquaChain Account',
                'VerificationMessageTemplate': {
                    'SmsMessage': 'Your AquaChain verification code is {####}',
                    'EmailMessage': 'Welcome to AquaChain!\n\nThank you for signing up. To complete your registration and start monitoring your water quality, please verify your email address.\n\nYour verification code is: {####}\n\nThis code will expire in 24 hours.\n\nIf you did not create an AquaChain account, please ignore this email.\n\nBest regards,\nThe AquaChain Team',
                    'EmailSubject': 'Verify Your AquaChain Account',
                    'DefaultEmailOption': 'CONFIRM_WITH_CODE'
                },
                'MfaConfiguration': mfa_configuration,
                'DeviceConfiguration': {
                    'ChallengeRequiredOnNewDevice': True,
                    'DeviceOnlyRememberedOnUserPrompt': False
                },
                'EmailConfiguration': {
                    'EmailSendingAccount': 'COGNITO_DEFAULT',
                    'ReplyToEmailAddress': 'noreply@aquachain.io'
                },
                'AdminCreateUserConfig': {
                    'AllowAdminCreateUserOnly': False,
                    'UnusedAccountValidityDays': 7,
                    'InviteMessageTemplate': {
                        'SMSMessage': 'Welcome to AquaChain! Your username is {username} and temporary password is {####}',
                        'EmailMessage': 'Welcome to AquaChain! Your username is {username} and temporary password is {####}',
                        'EmailSubject': 'Welcome to AquaChain'
                    }
                },
                'UserPoolTags': {
                    'Project': 'AquaChain',
                    'Environment': 'production',
                    'Component': 'authentication'
                },
                'AccountRecoverySetting': account_recovery_setting,
                'UsernameConfiguration': {
                    'CaseSensitive': False
                }
            }
            
            response = self.cognito_client.create_user_pool(**user_pool_config)
            user_pool_id = response['UserPool']['Id']
            
            logger.info(f"Created User Pool: {user_pool_id}")
            return user_pool_id
            
        except ClientError as e:
            logger.error(f"Error creating user pool: {e}")
            raise
    
    def create_user_pool_client(self, user_pool_id):
        """
        Create User Pool Client for web and mobile applications.
        """
        try:
            client_config = {
                'UserPoolId': user_pool_id,
                'ClientName': 'aquachain-web-client',
                'GenerateSecret': False,  # Public client for web/mobile
                'RefreshTokenValidity': 30,  # 30 days
                'AccessTokenValidity': 60,   # 60 minutes
                'IdTokenValidity': 60,       # 60 minutes
                'TokenValidityUnits': {
                    'AccessToken': 'minutes',
                    'IdToken': 'minutes',
                    'RefreshToken': 'days'
                },
                'ReadAttributes': [
                    'email',
                    'email_verified',
                    'given_name',
                    'family_name',
                    'phone_number',
                    'phone_number_verified',
                    'custom:role',
                    'custom:deviceIds'
                ],
                'WriteAttributes': [
                    'email',
                    'given_name',
                    'family_name',
                    'phone_number',
                    'custom:role',
                    'custom:deviceIds'
                ],
                'ExplicitAuthFlows': [
                    'ALLOW_USER_SRP_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH',
                    'ALLOW_USER_PASSWORD_AUTH'
                ],
                'SupportedIdentityProviders': [
                    'COGNITO',
                    'Google'
                ],
                'CallbackURLs': [
                    'https://aquachain.io/auth/callback',
                    'http://localhost:3000/auth/callback'  # For development
                ],
                'LogoutURLs': [
                    'https://aquachain.io/auth/logout',
                    'http://localhost:3000/auth/logout'
                ],
                'AllowedOAuthFlows': ['code'],
                'AllowedOAuthScopes': [
                    'openid',
                    'email',
                    'profile',
                    'aws.cognito.signin.user.admin'
                ],
                'AllowedOAuthFlowsUserPoolClient': True,
                'PreventUserExistenceErrors': 'ENABLED'
            }
            
            response = self.cognito_client.create_user_pool_client(**client_config)
            client_id = response['UserPoolClient']['ClientId']
            
            logger.info(f"Created User Pool Client: {client_id}")
            return client_id
            
        except ClientError as e:
            logger.error(f"Error creating user pool client: {e}")
            raise
    
    def create_user_groups(self, user_pool_id):
        """
        Create user groups for Consumer/Technician/Administrator roles.
        Implements requirement 8.1 for role-based access control.
        """
        groups = [
            {
                'GroupName': 'consumers',
                'Description': 'Consumer users who monitor water quality for personal use',
                'Precedence': 3
            },
            {
                'GroupName': 'technicians',
                'Description': 'Field service professionals who maintain and repair IoT devices',
                'Precedence': 2
            },
            {
                'GroupName': 'administrators',
                'Description': 'System operators who manage users, devices, and system-wide operations',
                'Precedence': 1
            }
        ]
        
        created_groups = []
        
        for group in groups:
            try:
                response = self.cognito_client.create_group(
                    UserPoolId=user_pool_id,
                    **group
                )
                created_groups.append(response['Group']['GroupName'])
                logger.info(f"Created group: {group['GroupName']}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'GroupExistsException':
                    logger.info(f"Group {group['GroupName']} already exists")
                    created_groups.append(group['GroupName'])
                else:
                    logger.error(f"Error creating group {group['GroupName']}: {e}")
                    raise
        
        return created_groups
    
    def configure_google_oauth(self, user_pool_id, google_client_id, google_client_secret):
        """
        Configure Google OAuth 2.0 federation.
        Implements requirement 8.1 for social login integration.
        """
        try:
            # Create Google identity provider
            provider_config = {
                'UserPoolId': user_pool_id,
                'ProviderName': 'Google',
                'ProviderType': 'Google',
                'ProviderDetails': {
                    'client_id': google_client_id,
                    'client_secret': google_client_secret,
                    'authorize_scopes': 'openid email profile'
                },
                'AttributeMapping': {
                    'email': 'email',
                    'given_name': 'given_name',
                    'family_name': 'family_name',
                    'email_verified': 'email_verified'
                }
            }
            
            response = self.cognito_client.create_identity_provider(**provider_config)
            
            logger.info("Configured Google OAuth provider")
            return response['IdentityProvider']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'DuplicateProviderException':
                logger.info("Google OAuth provider already exists")
                return None
            else:
                logger.error(f"Error configuring Google OAuth: {e}")
                raise
    
    def create_user_pool_domain(self, user_pool_id, domain_prefix):
        """
        Create a domain for the Cognito hosted UI.
        """
        try:
            response = self.cognito_client.create_user_pool_domain(
                UserPoolId=user_pool_id,
                Domain=domain_prefix
            )
            
            logger.info(f"Created user pool domain: {domain_prefix}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidParameterException':
                logger.info(f"Domain {domain_prefix} already exists or is invalid")
                return None
            else:
                logger.error(f"Error creating user pool domain: {e}")
                raise
    
    def setup_complete_cognito_infrastructure(self, google_client_id=None, google_client_secret=None):
        """
        Set up complete Cognito infrastructure for AquaChain.
        """
        try:
            # Create User Pool
            user_pool_id = self.create_user_pool()
            
            # Create User Pool Client
            client_id = self.create_user_pool_client(user_pool_id)
            
            # Create User Groups
            groups = self.create_user_groups(user_pool_id)
            
            # Configure Google OAuth if credentials provided
            google_provider = None
            if google_client_id and google_client_secret:
                google_provider = self.configure_google_oauth(
                    user_pool_id, google_client_id, google_client_secret
                )
            
            # Create domain for hosted UI
            domain_prefix = f"aquachain-auth-{user_pool_id.lower()}"
            domain = self.create_user_pool_domain(user_pool_id, domain_prefix)
            
            # Return configuration details
            config = {
                'userPoolId': user_pool_id,
                'clientId': client_id,
                'groups': groups,
                'region': self.region,
                'domain': domain_prefix if domain else None,
                'googleProvider': google_provider is not None
            }
            
            logger.info("Cognito infrastructure setup completed successfully")
            return config
            
        except Exception as e:
            logger.error(f"Error setting up Cognito infrastructure: {e}")
            raise

def main():
    """
    Main function to set up Cognito infrastructure.
    """
    logging.basicConfig(level=logging.INFO)
    
    cognito_setup = CognitoSetup()
    
    # Set up the complete infrastructure
    # Note: Google OAuth credentials should be provided via environment variables or AWS Secrets Manager
    config = cognito_setup.setup_complete_cognito_infrastructure()
    
    print("Cognito Configuration:")
    print(json.dumps(config, indent=2))
    
    return config

if __name__ == "__main__":
    main()