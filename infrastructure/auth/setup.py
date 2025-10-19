"""
Complete authentication system setup script for AquaChain.
Integrates Cognito, Lambda functions, and DynamoDB for full auth system.
"""

import boto3
import json
import os
from cognito_setup import CognitoSetup
from config import auth_config

def setup_authentication_system():
    """
    Set up the complete authentication system infrastructure.
    """
    print("Setting up AquaChain Authentication System...")
    
    # 1. Set up Cognito User Pool
    print("1. Creating Cognito User Pool...")
    cognito_setup = CognitoSetup()
    
    # Get Google OAuth credentials from environment or prompt
    google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    
    if not google_client_id or not google_client_secret:
        print("Warning: Google OAuth credentials not found. Social login will be disabled.")
        google_client_id = None
        google_client_secret = None
    
    cognito_config = cognito_setup.setup_complete_cognito_infrastructure(
        google_client_id, google_client_secret
    )
    
    print(f"✓ User Pool created: {cognito_config['userPoolId']}")
    print(f"✓ Client created: {cognito_config['clientId']}")
    print(f"✓ Groups created: {', '.join(cognito_config['groups'])}")
    
    # 2. Store configuration in AWS Systems Manager Parameter Store
    print("2. Storing configuration in Parameter Store...")
    ssm_client = boto3.client('ssm')
    
    environment = os.getenv('ENVIRONMENT', 'development')
    
    parameters = [
        {
            'Name': f'/aquachain/{environment}/auth/user-pool-id',
            'Value': cognito_config['userPoolId'],
            'Type': 'String',
            'Description': 'AquaChain Cognito User Pool ID'
        },
        {
            'Name': f'/aquachain/{environment}/auth/client-id',
            'Value': cognito_config['clientId'],
            'Type': 'String',
            'Description': 'AquaChain Cognito Client ID'
        },
        {
            'Name': f'/aquachain/{environment}/auth/region',
            'Value': cognito_config['region'],
            'Type': 'String',
            'Description': 'AquaChain AWS Region'
        }
    ]
    
    for param in parameters:
        try:
            ssm_client.put_parameter(**param, Overwrite=True)
            print(f"✓ Stored parameter: {param['Name']}")
        except Exception as e:
            print(f"✗ Error storing parameter {param['Name']}: {e}")
    
    # 3. Create DynamoDB table for user profiles
    print("3. Creating DynamoDB users table...")
    dynamodb = boto3.resource('dynamodb')
    
    try:
        table = dynamodb.create_table(
            TableName='aquachain-users',
            KeySchema=[
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'role',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'role-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'role',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Component',
                    'Value': 'Authentication'
                }
            ]
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print("✓ DynamoDB users table created")
        
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("✓ DynamoDB users table already exists")
        else:
            print(f"✗ Error creating DynamoDB table: {e}")
    
    # 4. Output configuration for Lambda functions
    print("4. Generating Lambda environment configuration...")
    
    lambda_env_config = {
        'COGNITO_USER_POOL_ID': cognito_config['userPoolId'],
        'COGNITO_CLIENT_ID': cognito_config['clientId'],
        'AWS_REGION': cognito_config['region'],
        'USERS_TABLE_NAME': 'aquachain-users'
    }
    
    # Save to file for deployment scripts
    with open('lambda_env_config.json', 'w') as f:
        json.dump(lambda_env_config, f, indent=2)
    
    print("✓ Lambda environment configuration saved to lambda_env_config.json")
    
    # 5. Create IAM roles for Lambda functions
    print("5. Creating IAM roles...")
    iam_client = boto3.client('iam')
    
    # Auth service role
    auth_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    auth_permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminUpdateUserAttributes"
                ],
                "Resource": f"arn:aws:cognito-idp:{cognito_config['region']}:*:userpool/{cognito_config['userPoolId']}"
            }
        ]
    }
    
    try:
        # Create role
        iam_client.create_role(
            RoleName='AquaChainAuthServiceRole',
            AssumeRolePolicyDocument=json.dumps(auth_role_policy),
            Description='Role for AquaChain authentication service Lambda'
        )
        
        # Attach policy
        iam_client.put_role_policy(
            RoleName='AquaChainAuthServiceRole',
            PolicyName='AquaChainAuthServicePolicy',
            PolicyDocument=json.dumps(auth_permissions_policy)
        )
        
        print("✓ Auth service IAM role created")
        
    except Exception as e:
        if 'EntityAlreadyExists' in str(e):
            print("✓ Auth service IAM role already exists")
        else:
            print(f"✗ Error creating IAM role: {e}")
    
    # User management service role
    user_mgmt_permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminInitiateAuth"
                ],
                "Resource": f"arn:aws:cognito-idp:{cognito_config['region']}:*:userpool/{cognito_config['userPoolId']}"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": "arn:aws:dynamodb:*:*:table/aquachain-users*"
            }
        ]
    }
    
    try:
        # Create role
        iam_client.create_role(
            RoleName='AquaChainUserMgmtRole',
            AssumeRolePolicyDocument=json.dumps(auth_role_policy),
            Description='Role for AquaChain user management service Lambda'
        )
        
        # Attach policy
        iam_client.put_role_policy(
            RoleName='AquaChainUserMgmtRole',
            PolicyName='AquaChainUserMgmtPolicy',
            PolicyDocument=json.dumps(user_mgmt_permissions_policy)
        )
        
        print("✓ User management service IAM role created")
        
    except Exception as e:
        if 'EntityAlreadyExists' in str(e):
            print("✓ User management service IAM role already exists")
        else:
            print(f"✗ Error creating user management IAM role: {e}")
    
    print("\n🎉 Authentication system setup completed!")
    print("\nNext steps:")
    print("1. Deploy Lambda functions using the generated configuration")
    print("2. Set up API Gateway endpoints")
    print("3. Configure frontend applications with Cognito settings")
    print(f"4. Test authentication with User Pool: {cognito_config['userPoolId']}")
    
    return cognito_config

if __name__ == "__main__":
    setup_authentication_system()