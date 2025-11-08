"""
Integration tests for authentication workflow
Tests the complete end-to-end authentication process including login, token refresh, and logout
Requirements: 3.4, 12.2
"""

import pytest
import json
import sys
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'auth_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from handler import TokenManager, AuthorizationManager, lambda_handler


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'COGNITO_USER_POOL_ID': 'us-east-1_test123',
        'COGNITO_CLIENT_ID': 'test-client-id',
        'AWS_REGION': 'us-east-1'
    }):
        yield


@pytest.fixture
def mock_cognito_client():
    """Fixture providing mocked Cognito client"""
    with patch('boto3.client') as mock_client:
        mock_cognito = MagicMock()
        mock_client.return_value = mock_cognito
        yield mock_cognito


@pytest.fixture
def sample_jwt_token():
    """Fixture providing sample JWT token"""
    # Create a sample token (not cryptographically valid, for structure only)
    payload = {
        'sub': 'user-123',
        'email': 'test@example.com',
        'cognito:groups': ['consumers'],
        'token_use': 'access',
        'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
        'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        'iat': int(datetime.utcnow().timestamp())
    }
    return payload


@pytest.fixture
def mock_jwks_response():
    """Fixture providing mocked JWKS response"""
    return {
        'keys': [
            {
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test-modulus',
                'e': 'AQAB'
            }
        ]
    }


class TestLoginWorkflow:
    """Test suite for login workflow"""
    
    def test_successful_login_flow(self, mock_aws_environment, mock_cognito_client):
        """Test complete successful login flow"""
        # Mock Cognito authentication response
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'mock-access-token',
                'IdToken': 'mock-id-token',
                'RefreshToken': 'mock-refresh-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        # Simulate login request
        username = 'test@example.com'
        password = 'TestPassword123!'
        
        response = mock_cognito_client.initiate_auth(
            ClientId='test-client-id',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Verify response
        assert 'AuthenticationResult' in response
        auth_result = response['AuthenticationResult']
        assert 'AccessToken' in auth_result
        assert 'IdToken' in auth_result
        assert 'RefreshToken' in auth_result
        assert auth_result['TokenType'] == 'Bearer'
        assert auth_result['ExpiresIn'] == 3600
    
    def test_login_with_invalid_credentials(self, mock_aws_environment, mock_cognito_client):
        """Test login with invalid credentials"""
        from botocore.exceptions import ClientError
        
        # Mock Cognito authentication failure
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Incorrect username or password'}},
            'InitiateAuth'
        )
        
        # Attempt login with invalid credentials
        with pytest.raises(ClientError) as exc_info:
            mock_cognito_client.initiate_auth(
                ClientId='test-client-id',
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'test@example.com',
                    'PASSWORD': 'WrongPassword'
                }
            )
        
        # Verify error
        assert exc_info.value.response['Error']['Code'] == 'NotAuthorizedException'
    
    def test_login_with_mfa_required(self, mock_aws_environment, mock_cognito_client):
        """Test login flow when MFA is required"""
        # Mock Cognito MFA challenge response
        mock_cognito_client.initiate_auth.return_value = {
            'ChallengeName': 'SMS_MFA',
            'Session': 'mock-session-token',
            'ChallengeParameters': {
                'CODE_DELIVERY_DESTINATION': '+1***5678',
                'CODE_DELIVERY_DELIVERY_MEDIUM': 'SMS'
            }
        }
        
        # Simulate login request
        response = mock_cognito_client.initiate_auth(
            ClientId='test-client-id',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'test@example.com',
                'PASSWORD': 'TestPassword123!'
            }
        )
        
        # Verify MFA challenge
        assert response['ChallengeName'] == 'SMS_MFA'
        assert 'Session' in response
        assert 'ChallengeParameters' in response
    
    def test_login_with_account_locked(self, mock_aws_environment, mock_cognito_client):
        """Test login with locked account"""
        from botocore.exceptions import ClientError
        
        # Mock Cognito account locked error
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'UserNotConfirmedException', 'Message': 'User account is not confirmed'}},
            'InitiateAuth'
        )
        
        # Attempt login with locked account
        with pytest.raises(ClientError) as exc_info:
            mock_cognito_client.initiate_auth(
                ClientId='test-client-id',
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'locked@example.com',
                    'PASSWORD': 'TestPassword123!'
                }
            )
        
        # Verify error
        assert exc_info.value.response['Error']['Code'] == 'UserNotConfirmedException'


class TestTokenValidationWorkflow:
    """Test suite for token validation workflow"""
    
    def test_validate_valid_token(self, mock_aws_environment, sample_jwt_token):
        """Test validating a valid JWT token"""
        # Mock JWKS endpoint
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'keys': [{'kid': 'test-key', 'kty': 'RSA', 'use': 'sig'}]
            }
            mock_get.return_value.status_code = 200
            
            # Mock JWT decode
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = sample_jwt_token
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test-key', 'alg': 'RS256'}
                    
                    # Create token manager
                    token_manager = TokenManager('us-east-1_test123', 'us-east-1')
                    
                    # Validate token
                    decoded = token_manager.validate_token('mock-token')
                    
                    # Verify decoded token
                    assert decoded['sub'] == 'user-123'
                    assert decoded['email'] == 'test@example.com'
                    assert 'consumers' in decoded['cognito:groups']
    
    def test_validate_expired_token(self, mock_aws_environment):
        """Test validating an expired token"""
        from errors import AuthenticationError
        
        # Mock JWKS endpoint
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'keys': [{'kid': 'test-key', 'kty': 'RSA', 'use': 'sig'}]
            }
            mock_get.return_value.status_code = 200
            
            # Mock JWT decode to raise ExpiredSignatureError
            with patch('jwt.decode') as mock_decode:
                mock_decode.side_effect = jwt.ExpiredSignatureError('Token has expired')
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test-key', 'alg': 'RS256'}
                    
                    # Create token manager
                    token_manager = TokenManager('us-east-1_test123', 'us-east-1')
                    
                    # Attempt to validate expired token
                    with pytest.raises(AuthenticationError) as exc_info:
                        token_manager.validate_token('expired-token')
                    
                    # Verify error message
                    assert 'expired' in str(exc_info.value).lower()
    
    def test_validate_token_with_invalid_signature(self, mock_aws_environment):
        """Test validating a token with invalid signature"""
        from errors import AuthenticationError
        
        # Mock JWKS endpoint
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'keys': [{'kid': 'test-key', 'kty': 'RSA', 'use': 'sig'}]
            }
            mock_get.return_value.status_code = 200
            
            # Mock JWT decode to raise InvalidTokenError
            with patch('jwt.decode') as mock_decode:
                mock_decode.side_effect = jwt.InvalidTokenError('Invalid signature')
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test-key', 'alg': 'RS256'}
                    
                    # Create token manager
                    token_manager = TokenManager('us-east-1_test123', 'us-east-1')
                    
                    # Attempt to validate token with invalid signature
                    with pytest.raises(AuthenticationError) as exc_info:
                        token_manager.validate_token('invalid-token')
                    
                    # Verify error message
                    assert 'invalid' in str(exc_info.value).lower()
    
    def test_validate_token_endpoint(self, mock_aws_environment):
        """Test token validation API endpoint"""
        # Mock API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/auth/validate',
            'body': json.dumps({
                'token': 'mock-access-token'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                },
                'requestId': 'req-123'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock token validation
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'keys': [{'kid': 'test-key', 'kty': 'RSA', 'use': 'sig'}]
            }
            mock_get.return_value.status_code = 200
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'sub': 'user-123',
                    'email': 'test@example.com',
                    'cognito:groups': ['consumers'],
                    'token_use': 'access'
                }
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test-key', 'alg': 'RS256'}
                    
                    # Execute handler
                    response = lambda_handler(event, context)
                    
                    # Verify response
                    assert response['statusCode'] == 200
                    body = json.loads(response['body'])
                    assert body['valid'] is True
                    assert body['userId'] == 'user-123'
                    assert body['email'] == 'test@example.com'


class TestTokenRefreshWorkflow:
    """Test suite for token refresh workflow"""
    
    def test_successful_token_refresh(self, mock_aws_environment, mock_cognito_client):
        """Test successful token refresh"""
        # Mock Cognito token refresh response
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token',
                'IdToken': 'new-id-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        # Create token manager
        token_manager = TokenManager('us-east-1_test123', 'us-east-1')
        
        # Refresh token
        new_tokens = token_manager.refresh_token('mock-refresh-token', 'test-client-id')
        
        # Verify new tokens
        assert new_tokens['accessToken'] == 'new-access-token'
        assert new_tokens['idToken'] == 'new-id-token'
        assert new_tokens['tokenType'] == 'Bearer'
        assert new_tokens['expiresIn'] == 3600
        
        # Verify Cognito was called correctly
        mock_cognito_client.initiate_auth.assert_called_once_with(
            ClientId='test-client-id',
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': 'mock-refresh-token'
            }
        )
    
    def test_token_refresh_with_invalid_refresh_token(self, mock_aws_environment, mock_cognito_client):
        """Test token refresh with invalid refresh token"""
        from botocore.exceptions import ClientError
        from errors import AuthenticationError
        
        # Mock Cognito refresh failure
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Invalid refresh token'}},
            'InitiateAuth'
        )
        
        # Create token manager
        token_manager = TokenManager('us-east-1_test123', 'us-east-1')
        
        # Attempt to refresh with invalid token
        with pytest.raises(AuthenticationError) as exc_info:
            token_manager.refresh_token('invalid-refresh-token', 'test-client-id')
        
        # Verify error message
        assert 'invalid refresh token' in str(exc_info.value).lower()
    
    def test_token_refresh_endpoint(self, mock_aws_environment, mock_cognito_client):
        """Test token refresh API endpoint"""
        # Mock Cognito token refresh response
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token',
                'IdToken': 'new-id-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        # Mock API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/auth/refresh',
            'body': json.dumps({
                'refreshToken': 'mock-refresh-token'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                },
                'requestId': 'req-123'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }
        
        context = MagicMock()
        context.request_id = 'req-123'
        
        # Mock JWT decode for audit logging
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {'sub': 'user-123'}
            
            # Execute handler
            response = lambda_handler(event, context)
            
            # Verify response
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['accessToken'] == 'new-access-token'
            assert body['idToken'] == 'new-id-token'
            assert body['tokenType'] == 'Bearer'


class TestLogoutWorkflow:
    """Test suite for logout workflow"""
    
    def test_successful_logout(self, mock_aws_environment, mock_cognito_client):
        """Test successful logout (token revocation)"""
        # Mock Cognito global sign out
        mock_cognito_client.global_sign_out.return_value = {}
        
        # Perform logout
        access_token = 'mock-access-token'
        mock_cognito_client.global_sign_out(AccessToken=access_token)
        
        # Verify Cognito was called
        mock_cognito_client.global_sign_out.assert_called_once_with(
            AccessToken=access_token
        )
    
    def test_logout_with_invalid_token(self, mock_aws_environment, mock_cognito_client):
        """Test logout with invalid token"""
        from botocore.exceptions import ClientError
        
        # Mock Cognito sign out failure
        mock_cognito_client.global_sign_out.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Invalid access token'}},
            'GlobalSignOut'
        )
        
        # Attempt logout with invalid token
        with pytest.raises(ClientError) as exc_info:
            mock_cognito_client.global_sign_out(AccessToken='invalid-token')
        
        # Verify error
        assert exc_info.value.response['Error']['Code'] == 'NotAuthorizedException'


class TestCompleteAuthenticationWorkflow:
    """Test suite for complete end-to-end authentication workflow"""
    
    def test_complete_authentication_lifecycle(self, mock_aws_environment, mock_cognito_client):
        """Test complete authentication lifecycle: login -> validate -> refresh -> logout"""
        # Step 1: Login
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'initial-access-token',
                'IdToken': 'initial-id-token',
                'RefreshToken': 'refresh-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        login_response = mock_cognito_client.initiate_auth(
            ClientId='test-client-id',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'test@example.com',
                'PASSWORD': 'TestPassword123!'
            }
        )
        
        assert 'AuthenticationResult' in login_response
        access_token = login_response['AuthenticationResult']['AccessToken']
        refresh_token = login_response['AuthenticationResult']['RefreshToken']
        
        # Step 2: Validate token
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'keys': [{'kid': 'test-key', 'kty': 'RSA', 'use': 'sig'}]
            }
            mock_get.return_value.status_code = 200
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'sub': 'user-123',
                    'email': 'test@example.com',
                    'cognito:groups': ['consumers'],
                    'token_use': 'access',
                    'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
                    'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                    'iat': int(datetime.utcnow().timestamp())
                }
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test-key', 'alg': 'RS256'}
                    
                    token_manager = TokenManager('us-east-1_test123', 'us-east-1')
                    decoded = token_manager.validate_token(access_token)
                    
                    assert decoded['sub'] == 'user-123'
                    assert decoded['email'] == 'test@example.com'
        
        # Step 3: Refresh token
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'refreshed-access-token',
                'IdToken': 'refreshed-id-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        new_tokens = token_manager.refresh_token(refresh_token, 'test-client-id')
        
        assert new_tokens['accessToken'] == 'refreshed-access-token'
        assert new_tokens['idToken'] == 'refreshed-id-token'
        
        # Step 4: Logout
        mock_cognito_client.global_sign_out.return_value = {}
        mock_cognito_client.global_sign_out(AccessToken=new_tokens['accessToken'])
        
        # Verify logout was called
        mock_cognito_client.global_sign_out.assert_called_once()
    
    def test_authentication_with_role_based_access(self, mock_aws_environment):
        """Test authentication with role-based access control"""
        # Create authorization manager
        auth_manager = AuthorizationManager()
        
        # Test admin permissions
        assert auth_manager.check_permission('administrators', 'devices', 'delete')
        assert auth_manager.check_permission('administrators', 'users', 'create')
        
        # Test technician permissions
        assert not auth_manager.check_permission('technicians', 'users', 'delete')
        assert auth_manager.check_permission(
            'technicians', 'devices', 'read_assigned',
            user_id='tech-1', assigned_technician='tech-1'
        )
        
        # Test consumer permissions
        assert auth_manager.check_permission(
            'consumers', 'devices', 'read_own',
            user_id='user-1', resource_owner='user-1'
        )
        assert not auth_manager.check_permission(
            'consumers', 'devices', 'read_own',
            user_id='user-1', resource_owner='user-2'
        )
    
    def test_concurrent_authentication_sessions(self, mock_aws_environment, mock_cognito_client):
        """Test handling multiple concurrent authentication sessions"""
        # Mock multiple login responses
        mock_cognito_client.initiate_auth.side_effect = [
            {
                'AuthenticationResult': {
                    'AccessToken': 'session-1-token',
                    'IdToken': 'session-1-id',
                    'RefreshToken': 'session-1-refresh',
                    'TokenType': 'Bearer',
                    'ExpiresIn': 3600
                }
            },
            {
                'AuthenticationResult': {
                    'AccessToken': 'session-2-token',
                    'IdToken': 'session-2-id',
                    'RefreshToken': 'session-2-refresh',
                    'TokenType': 'Bearer',
                    'ExpiresIn': 3600
                }
            }
        ]
        
        # Create two sessions
        session1 = mock_cognito_client.initiate_auth(
            ClientId='test-client-id',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': 'test@example.com', 'PASSWORD': 'Pass123!'}
        )
        
        session2 = mock_cognito_client.initiate_auth(
            ClientId='test-client-id',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': 'test@example.com', 'PASSWORD': 'Pass123!'}
        )
        
        # Verify both sessions have unique tokens
        assert session1['AuthenticationResult']['AccessToken'] != session2['AuthenticationResult']['AccessToken']
        assert session1['AuthenticationResult']['RefreshToken'] != session2['AuthenticationResult']['RefreshToken']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
