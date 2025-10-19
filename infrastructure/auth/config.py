"""
Configuration management for AquaChain authentication system.
"""

import os
import boto3
from typing import Dict, Optional

class AuthConfig:
    """
    Configuration class for authentication settings.
    """
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
    def get_cognito_config(self) -> Dict[str, str]:
        """
        Get Cognito configuration from environment variables or AWS Systems Manager.
        """
        # Try environment variables first
        config = {
            'userPoolId': os.getenv('COGNITO_USER_POOL_ID'),
            'clientId': os.getenv('COGNITO_CLIENT_ID'),
            'region': self.region
        }
        
        # If not found in env vars, try AWS Systems Manager Parameter Store
        if not config['userPoolId'] or not config['clientId']:
            config = self._get_config_from_ssm()
        
        return config
    
    def _get_config_from_ssm(self) -> Dict[str, str]:
        """
        Retrieve configuration from AWS Systems Manager Parameter Store.
        """
        ssm_client = boto3.client('ssm', region_name=self.region)
        
        try:
            # Get parameters from SSM
            parameters = ssm_client.get_parameters(
                Names=[
                    f'/aquachain/{self.environment}/auth/user-pool-id',
                    f'/aquachain/{self.environment}/auth/client-id'
                ],
                WithDecryption=True
            )
            
            config = {'region': self.region}
            
            for param in parameters['Parameters']:
                if param['Name'].endswith('user-pool-id'):
                    config['userPoolId'] = param['Value']
                elif param['Name'].endswith('client-id'):
                    config['clientId'] = param['Value']
            
            return config
            
        except Exception as e:
            print(f"Error retrieving config from SSM: {e}")
            return {
                'userPoolId': None,
                'clientId': None,
                'region': self.region
            }
    
    def get_google_oauth_config(self) -> Dict[str, Optional[str]]:
        """
        Get Google OAuth configuration.
        """
        return {
            'clientId': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'clientSecret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        }
    
    def get_jwt_config(self) -> Dict[str, any]:
        """
        Get JWT configuration settings.
        """
        return {
            'algorithm': 'RS256',
            'accessTokenExpiry': 3600,  # 1 hour
            'refreshTokenExpiry': 2592000,  # 30 days
            'issuer': f'https://cognito-idp.{self.region}.amazonaws.com'
        }

# Global config instance
auth_config = AuthConfig()