# IAM Permissions Setup Guide

## Current Issue
The IAM user `Karthik` lacks the necessary permissions for CDK deployment. You need to add CloudFormation and other AWS service permissions.

## Solution Steps

### Option 1: Using AWS Console (Recommended)

1. **Log into AWS Console** with an admin user or root account
2. **Navigate to IAM** → Users → Karthik
3. **Add Permissions** → Attach policies directly
4. **Create a new policy** with the JSON from `setup-iam-permissions.json`
5. **Name the policy**: `AquaChain-CDK-Deployment-Policy`
6. **Attach the policy** to the Karthik user

### Option 2: Using AWS CLI (if you have admin access)

```bash
# Create the policy
aws iam create-policy \
  --policy-name AquaChain-CDK-Deployment-Policy \
  --policy-document file://setup-iam-permissions.json

# Attach to user (replace ACCOUNT-ID with your account ID)
aws iam attach-user-policy \
  --user-name Karthik \
  --policy-arn arn:aws:iam::758346259059:policy/AquaChain-CDK-Deployment-Policy
```

### Option 3: Minimal Permissions (If full permissions are too broad)

If you prefer more restrictive permissions, create a policy with just these essential permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "s3:*",
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

## Verification

After adding permissions, test with:

```bash
# Test CloudFormation access
aws cloudformation describe-stacks --region ap-south-1

# Test CDK bootstrap
cd infrastructure/cdk
cdk bootstrap aws://758346259059/ap-south-1
```

## Security Notes

- These permissions are broad for development/deployment purposes
- In production, consider using more restrictive policies
- Consider using IAM roles instead of user policies for better security
- Regularly review and audit permissions

## Next Steps

Once permissions are added:
1. Test CDK bootstrap
2. Proceed with infrastructure deployment
3. Address Docker requirement for Lambda functions