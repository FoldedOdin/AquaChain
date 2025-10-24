# Step-by-Step Guide: Adding IAM Permissions

## Method 1: AWS Console (Easiest - Recommended)

### Step 1: Access AWS Console

1. Open your web browser
2. Go to https://aws.amazon.com/console/
3. Sign in with your **root account** or an **admin user** (NOT the Karthik user)

### Step 2: Navigate to IAM

1. In the AWS Console search bar, type "IAM"
2. Click on "IAM" service
3. In the left sidebar, click "Users"
4. Find and click on "Karthik" user

### Step 3: Add Permissions

1. Click the "Permissions" tab
2. Click "Add permissions" button
3. Select "Attach policies directly"
4. Click "Create policy" (opens in new tab)

### Step 4: Create Custom Policy

1. In the new tab, click "JSON" tab
2. Delete the existing content
3. Copy and paste the content from `setup-iam-permissions.json`
4. Click "Next: Tags" (skip tags)
5. Click "Next: Review"
6. Enter policy name: `AquaChain-CDK-Deployment-Policy`
7. Enter description: `Permissions for AquaChain CDK deployment`
8. Click "Create policy"

### Step 5: Attach Policy to User

1. Go back to the Karthik user tab
2. Refresh the policy list
3. Search for "AquaChain-CDK-Deployment-Policy"
4. Check the box next to it
5. Click "Add permissions"

## Method 2: AWS CLI (If you have admin CLI access)

```bash
# Create the policy
aws iam create-policy \
  --policy-name AquaChain-CDK-Deployment-Policy \
  --policy-document file://infrastructure/setup-iam-permissions.json

# Attach to user
aws iam attach-user-policy \
  --user-name Karthik \
  --policy-arn arn:aws:iam::758346259059:policy/AquaChain-CDK-Deployment-Policy
```

## Method 3: Simplified Permissions (If you want minimal access)

If the full permissions seem too broad, use this minimal policy instead:

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
        "iam:GetRole",
        "iam:ListRoles",
        "s3:*",
        "ssm:GetParameter",
        "ssm:PutParameter",
        "sts:AssumeRole",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## Verification Steps

After adding permissions, test them:

```bash
# Test 1: Check if CloudFormation access works
aws cloudformation describe-stacks --region ap-south-1

# Test 2: Try CDK bootstrap
cd infrastructure/cdk
cdk bootstrap aws://758346259059/ap-south-1

# Test 3: Verify permissions
aws sts get-caller-identity
```

## Troubleshooting

### If you get "Access Denied" errors:

1. Make sure you're signed in with root account or admin user in AWS Console
2. Double-check the policy was created and attached correctly
3. Wait 1-2 minutes for permissions to propagate

### If you can't access AWS Console:

1. You need the root account email/password
2. Or contact your AWS administrator
3. Or use AWS CLI with admin credentials

### If policy creation fails:

1. Check the JSON syntax in `setup-iam-permissions.json`
2. Make sure all service names are correct
3. Try the simplified permissions instead

## What These Permissions Allow

The policy grants access to:

- ✅ CloudFormation (for CDK deployment)
- ✅ IAM (for creating roles and policies)
- ✅ S3 (for CDK assets and data storage)
- ✅ DynamoDB (for data tables)
- ✅ Lambda (for serverless functions)
- ✅ IoT Core (for device management)
- ✅ And other AWS services needed by AquaChain

## Security Note

These are development/deployment permissions. In production:

- Use more restrictive policies
- Consider using IAM roles instead of user policies
- Regularly audit permissions

## Next Steps

Once permissions are added successfully:

1. ✅ Test CDK bootstrap
2. 🔄 Address Docker requirement
3. 🚀 Deploy infrastructure
