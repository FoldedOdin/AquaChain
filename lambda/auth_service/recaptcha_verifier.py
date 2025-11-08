"""
reCAPTCHA Verification Service for AquaChain
Verifies reCAPTCHA v3 tokens on the backend
"""

import json
import requests
import logging
import boto3
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RecaptchaVerifier:
    """
    Verify reCAPTCHA v3 tokens with Google's API
    """
    
    VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
    MIN_SCORE = 0.5  # Minimum score for v3 (0.0 to 1.0)
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self._secret_key = None
    
    def _get_secret_key(self) -> str:
        """Get reCAPTCHA secret key from AWS Secrets Manager"""
        if self._secret_key:
            return self._secret_key
        
        try:
            response = self.secrets_client.get_secret_value(
                SecretId='aquachain/recaptcha/secret-key'
            )
            secret_data = json.loads(response['SecretString'])
            self._secret_key = secret_data['secret_key']
            return self._secret_key
        except Exception as e:
            logger.error(f"Failed to get reCAPTCHA secret: {e}")
            raise
    
    def verify_token(self, token: str, expected_action: str, 
                    remote_ip: str = None) -> Dict[str, Any]:
        """
        Verify reCAPTCHA token
        
        Args:
            token: reCAPTCHA response token
            expected_action: Expected action name
            remote_ip: User's IP address (optional)
            
        Returns:
            Verification result dictionary
        """
        try:
            secret_key = self._get_secret_key()
            
            # Prepare verification request
            data = {
                'secret': secret_key,
                'response': token
            }
            
            if remote_ip:
                data['remoteip'] = remote_ip
            
            # Call Google's verification API
            response = requests.post(
                self.VERIFY_URL,
                data=data,
                timeout=10
            )
            
            result = response.json()
            
            # Validate response
            success = result.get('success', False)
            score = result.get('score', 0.0)
            action = result.get('action', '')
            
            # Check if verification passed
            if not success:
                error_codes = result.get('error-codes', [])
                logger.warning(f"reCAPTCHA verification failed: {error_codes}")
                return {
                    'success': False,
                    'score': 0.0,
                    'error': 'Verification failed',
                    'error_codes': error_codes
                }
            
            # Check action matches
            if action != expected_action:
                logger.warning(f"Action mismatch: expected {expected_action}, got {action}")
                return {
                    'success': False,
                    'score': score,
                    'error': 'Action mismatch'
                }
            
            # Check score threshold
            if score < self.MIN_SCORE:
                logger.warning(f"Score too low: {score} < {self.MIN_SCORE}")
                return {
                    'success': False,
                    'score': score,
                    'error': 'Score below threshold'
                }
            
            # Verification passed
            logger.info(f"reCAPTCHA verified: action={action}, score={score}")
            return {
                'success': True,
                'score': score,
                'action': action,
                'challenge_ts': result.get('challenge_ts'),
                'hostname': result.get('hostname')
            }
            
        except requests.RequestException as e:
            logger.error(f"reCAPTCHA API error: {e}")
            return {
                'success': False,
                'score': 0.0,
                'error': f'API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {e}")
            return {
                'success': False,
                'score': 0.0,
                'error': f'Verification error: {str(e)}'
            }


def lambda_handler(event, context):
    """
    Lambda handler for reCAPTCHA verification
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        token = body.get('token')
        action = body.get('action', 'submit')
        
        # Get client IP
        headers = event.get('headers', {})
        remote_ip = headers.get('X-Forwarded-For', '').split(',')[0].strip()
        
        # Validate input
        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Token is required'
                })
            }
        
        # Verify token
        verifier = RecaptchaVerifier()
        result = verifier.verify_token(token, action, remote_ip)
        
        # Return result
        status_code = 200 if result['success'] else 400
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }
