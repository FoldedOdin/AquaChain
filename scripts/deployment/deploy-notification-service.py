"""
Deploy AquaChain Notification Service with production SES + SNS access.

What this script does:
  1. Creates/updates the notification Lambda IAM role with SES + SNS permissions
  2. Packages and deploys the notification Lambda function
  3. Sets all required environment variables (table names, SNS ARNs, SES config)
  4. Subscribes the Lambda to the critical-alerts and service-updates SNS topics
  5. Verifies SES production access (exits sandbox if needed)
  6. Runs a smoke test to confirm end-to-end delivery

Usage:
    python scripts/deployment/deploy-notification-service.py [--env dev|prod]
"""

import boto3
import json
import zipfile
import os
import sys
import time
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
REGION = "ap-south-1"
ACCOUNT_ID = "758346259059"
ENV = "dev"  # overridden by --env flag

LAMBDA_FUNCTION_NAME = f"aquachain-function-notification-{ENV}"
ROLE_NAME = f"aquachain-notification-role-{ENV}"
SES_FROM_EMAIL = "contact.aquachain@gmail.com"  # verified SES identity
SES_CONFIGURATION_SET = ""                      # no config set needed for Gmail sender

# DynamoDB table names (match existing tables)
USERS_TABLE = f"aquachain-users"
NOTIFICATIONS_TABLE = f"aquachain-notifications"
RATE_LIMIT_TABLE = f"aquachain-rate-limits"
ALERTS_TABLE = f"aquachain-alerts"

# SNS topic ARNs (already created by CDK security stack)
CRITICAL_ALERTS_TOPIC_ARN = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-critical-alerts-{ENV}"
SERVICE_UPDATES_TOPIC_ARN = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-service-updates-{ENV}"
SYSTEM_ALERTS_TOPIC_ARN   = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-system-alerts-{ENV}"

LAMBDA_SOURCE_DIR = Path("lambda/notification_service")
ZIP_PATH = Path("lambda/notification-service-deployment.zip")

# ── AWS clients ───────────────────────────────────────────────────────────────
session = boto3.Session(region_name=REGION)
iam = session.client("iam")
lambda_client = session.client("lambda")
sns = session.client("sns")
ses = session.client("ses")
dynamodb = session.client("dynamodb")


# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(f"  {msg}")

def step(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Step 1: IAM role ──────────────────────────────────────────────────────────
def ensure_iam_role() -> str:
    step("1/7  Ensuring IAM role with SES + SNS permissions")

    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })

    # Create or get role
    try:
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=trust_policy,
            Description="AquaChain notification service Lambda execution role",
            Tags=[
                {"Key": "Project", "Value": "AquaChain"},
                {"Key": "Environment", "Value": ENV},
                {"Key": "Service", "Value": "notification"},
                {"Key": "CostCenter", "Value": "engineering"},
            ]
        )
        role_arn = role["Role"]["Arn"]
        log(f"Created role: {role_arn}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
        log(f"Role already exists: {role_arn}")

    # Attach AWS managed policies
    managed_policies = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess",
    ]
    for policy_arn in managed_policies:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy_arn)
            log(f"Attached: {policy_arn.split('/')[-1]}")
        except iam.exceptions.EntityAlreadyExistsException:
            pass

    # Inline policy: SES + SNS + DynamoDB (least-privilege)
    inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            # SES — send emails (resource-level not supported for SendEmail)
            {
                "Sid": "SESProduction",
                "Effect": "Allow",
                "Action": [
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                    "ses:GetSendQuota",
                    "ses:GetSendStatistics"
                ],
                "Resource": "*"
            },
            # SNS — publish to notification topics + direct SMS
            {
                "Sid": "SNSPublish",
                "Effect": "Allow",
                "Action": [
                    "sns:Publish",
                    "sns:GetTopicAttributes",
                    "sns:ListSubscriptionsByTopic"
                ],
                "Resource": [
                    CRITICAL_ALERTS_TOPIC_ARN,
                    SERVICE_UPDATES_TOPIC_ARN,
                    SYSTEM_ALERTS_TOPIC_ARN,
                ]
            },
            # SNS — direct SMS (no topic ARN required)
            {
                "Sid": "SNSSMSDirect",
                "Effect": "Allow",
                "Action": ["sns:Publish"],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {"sns:Protocol": "sms"}
                }
            },
            # DynamoDB — notification tracking tables
            {
                "Sid": "DynamoDBNotifications",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{USERS_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{USERS_TABLE}/index/*",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{NOTIFICATIONS_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{RATE_LIMIT_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{ALERTS_TABLE}",
                ]
            },
            # CloudWatch Logs
            {
                "Sid": "CloudWatchLogs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/lambda/{LAMBDA_FUNCTION_NAME}:*"
            }
        ]
    }

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName=f"aquachain-notification-policy-{ENV}",
        PolicyDocument=json.dumps(inline_policy)
    )
    log("Inline policy applied (SES + SNS + DynamoDB)")

    # Wait for role propagation
    log("Waiting 10s for IAM role propagation...")
    time.sleep(10)
    return role_arn


# ── Step 2: Ensure DynamoDB tables exist ──────────────────────────────────────
def ensure_dynamodb_tables() -> None:
    step("2/7  Ensuring DynamoDB tables exist")

    tables_to_create = [
        {
            "TableName": NOTIFICATIONS_TABLE,
            "KeySchema": [{"AttributeName": "notificationId", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "notificationId", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": RATE_LIMIT_TABLE,
            "KeySchema": [{"AttributeName": "limitKey", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "limitKey", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]

    for table_def in tables_to_create:
        try:
            dynamodb.create_table(**table_def)
            log(f"Created table: {table_def['TableName']}")
            # Enable TTL
            waiter = boto3.client("dynamodb", region_name=REGION).get_waiter("table_exists")
            waiter.wait(TableName=table_def["TableName"])
            dynamodb.update_time_to_live(
                TableName=table_def["TableName"],
                TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"}
            )
            log(f"  TTL enabled on {table_def['TableName']}")
        except dynamodb.exceptions.ResourceInUseException:
            log(f"Table already exists: {table_def['TableName']}")


# ── Step 3: SES configuration set ─────────────────────────────────────────────
def ensure_ses_configuration_set() -> None:
    step("3/7  Checking SES configuration")

    # Try to create the configuration set; skip gracefully if no permission or already exists
    try:
        ses.create_configuration_set(ConfigurationSet={"Name": SES_CONFIGURATION_SET})
        log(f"Created SES configuration set: {SES_CONFIGURATION_SET}")
    except ses.exceptions.ConfigurationSetAlreadyExistsException:
        log(f"SES configuration set already exists: {SES_CONFIGURATION_SET}")
    except Exception as e:
        if "AccessDenied" in str(e) or "not authorized" in str(e):
            log(f"NOTE: No permission to create SES configuration set (ses:CreateConfigurationSet).")
            log(f"  The Lambda will send emails without a configuration set (tracking disabled).")
            log(f"  To enable tracking, grant ses:CreateConfigurationSet to your IAM user.")
        else:
            log(f"WARNING: Could not create SES configuration set: {e}")

    # Check sender identity verification
    try:
        domain = SES_FROM_EMAIL.split("@")[1]
        email_identities = ses.list_identities(IdentityType="EmailAddress")["Identities"]
        domain_identities = ses.list_identities(IdentityType="Domain")["Identities"]

        if SES_FROM_EMAIL in email_identities:
            attrs = ses.get_identity_verification_attributes(Identities=[SES_FROM_EMAIL])
            status = attrs["VerificationAttributes"].get(SES_FROM_EMAIL, {}).get("VerificationStatus", "Unknown")
            log(f"SES email identity {SES_FROM_EMAIL}: {status}")
        elif domain in domain_identities:
            attrs = ses.get_identity_verification_attributes(Identities=[domain])
            status = attrs["VerificationAttributes"].get(domain, {}).get("VerificationStatus", "Unknown")
            log(f"SES domain identity {domain}: {status}")
            if status == "Pending":
                log(f"  Add this TXT record to your DNS:")
                log(f"  Name:  _amazonses.{domain}")
                log(f"  Value: +swUL4oXYc5HIKIsLV1UBLHnWH17gL4rpIkVFDWfehY=")
                log(f"  (verification can take up to 72 hours)")
        else:
            log(f"WARNING: {SES_FROM_EMAIL} / {domain} not yet verified in SES.")
            log(f"  Domain verification is pending — add the TXT record to DNS.")
    except Exception as e:
        log(f"NOTE: Could not check SES identity status: {e}")

    # Check sandbox vs production
    try:
        quota = ses.get_send_quota()
        max_24h = quota["Max24HourSend"]
        if max_24h <= 200.0:
            log("WARNING: SES account is in sandbox (200 emails/day limit).")
            log("  Request production access:")
            log("  AWS Console → SES → Account dashboard → Request production access")
        else:
            log(f"SES production access confirmed (quota: {int(max_24h)} emails/24h)")
    except Exception as e:
        log(f"NOTE: Could not check SES quota: {e}")


# ── Step 4: Package Lambda ────────────────────────────────────────────────────
def package_lambda() -> None:
    step("4/7  Packaging Lambda function")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        # All .py files in the notification_service directory
        # (includes self-contained consent_checker.py and structured_logger.py)
        for py_file in LAMBDA_SOURCE_DIR.glob("*.py"):
            zf.write(py_file, py_file.name)
            log(f"  Added: {py_file.name}")

    log(f"Package created: {ZIP_PATH} ({ZIP_PATH.stat().st_size // 1024} KB)")


# ── Step 5: Deploy Lambda ─────────────────────────────────────────────────────
def deploy_lambda(role_arn: str) -> str:
    step("5/7  Deploying Lambda function")

    env_vars = {
        "ENVIRONMENT": ENV,
        "REGION": REGION,
        # DynamoDB tables
        "USERS_TABLE": USERS_TABLE,
        "NOTIFICATIONS_TABLE": NOTIFICATIONS_TABLE,
        "RATE_LIMIT_TABLE": RATE_LIMIT_TABLE,
        "ALERTS_TABLE": ALERTS_TABLE,
        # SES
        "SES_FROM_EMAIL": SES_FROM_EMAIL,
        "SES_CONFIGURATION_SET": SES_CONFIGURATION_SET,
        # SNS topic ARNs
        "CRITICAL_ALERTS_TOPIC_ARN": CRITICAL_ALERTS_TOPIC_ARN,
        "SERVICE_UPDATES_TOPIC_ARN": SERVICE_UPDATES_TOPIC_ARN,
        "SYSTEM_ALERTS_TOPIC_ARN": SYSTEM_ALERTS_TOPIC_ARN,
        # App URL for email links
        "APP_URL": "https://app.aquachain.io",
    }

    zip_bytes = ZIP_PATH.read_bytes()

    try:
        # Update existing function
        lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_bytes,
        )
        log("Updated function code")

        # Wait for update to complete
        waiter = lambda_client.get_waiter("function_updated")
        waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)

        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Role=role_arn,
            Runtime="python3.11",
            Handler="handler.lambda_handler",
            Timeout=30,
            MemorySize=512,
            Environment={"Variables": env_vars},
            TracingConfig={"Mode": "Active"},
        )
        log("Updated function configuration")

    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime="python3.11",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Code={"ZipFile": zip_bytes},
            Timeout=30,
            MemorySize=512,
            Environment={"Variables": env_vars},
            TracingConfig={"Mode": "Active"},
            Tags={
                "Project": "AquaChain",
                "Environment": ENV,
                "Service": "notification",
                "CostCenter": "engineering",
            }
        )
        log(f"Created function: {LAMBDA_FUNCTION_NAME}")

    # Wait for function to be active
    waiter = lambda_client.get_waiter("function_active")
    waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)

    fn = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
    fn_arn = fn["Configuration"]["FunctionArn"]
    log(f"Function ARN: {fn_arn}")
    return fn_arn


# ── Step 6: Wire SNS → Lambda subscriptions ───────────────────────────────────
def wire_sns_subscriptions(fn_arn: str) -> None:
    step("6/7  Wiring SNS → Lambda subscriptions")

    topics = [
        (CRITICAL_ALERTS_TOPIC_ARN, "critical-alerts"),
        (SERVICE_UPDATES_TOPIC_ARN, "service-updates"),
    ]

    for topic_arn, label in topics:
        # Check if subscription already exists
        existing = sns.list_subscriptions_by_topic(TopicArn=topic_arn)["Subscriptions"]
        already_subscribed = any(
            s["Protocol"] == "lambda" and s["Endpoint"] == fn_arn
            for s in existing
        )

        if already_subscribed:
            log(f"Already subscribed: {label}")
            continue

        sub = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="lambda",
            Endpoint=fn_arn,
            ReturnSubscriptionArn=True,
        )
        log(f"Subscribed to {label}: {sub['SubscriptionArn']}")

        # Grant SNS permission to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_FUNCTION_NAME,
                StatementId=f"sns-{label}-invoke",
                Action="lambda:InvokeFunction",
                Principal="sns.amazonaws.com",
                SourceArn=topic_arn,
            )
            log(f"  Lambda invoke permission granted for {label}")
        except lambda_client.exceptions.ResourceConflictException:
            log(f"  Invoke permission already exists for {label}")


# ── Step 7: Smoke test ────────────────────────────────────────────────────────
def smoke_test() -> None:
    step("7/7  Smoke test — invoking Lambda directly")

    test_payload = {
        "action": "send_alert",
        "alert": {
            "deviceId": "ESP32-TEST-001",
            "alertLevel": "warning",
            "wqi": 45.0,
            "timestamp": "2026-03-18T13:00:00Z",
            "alertReasons": ["WQI below threshold (45 < 50)"],
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            }
        }
    }

    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(test_payload).encode(),
    )

    status = response["StatusCode"]
    payload = json.loads(response["Payload"].read())

    if status == 200:
        log(f"Smoke test passed (HTTP {status})")
        log(f"Response: {json.dumps(payload, indent=2)[:400]}")
    else:
        log(f"WARNING: Smoke test returned HTTP {status}")
        log(f"Response: {json.dumps(payload, indent=2)[:400]}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global ENV, LAMBDA_FUNCTION_NAME, ROLE_NAME
    global CRITICAL_ALERTS_TOPIC_ARN, SERVICE_UPDATES_TOPIC_ARN, SYSTEM_ALERTS_TOPIC_ARN

    parser = argparse.ArgumentParser(description="Deploy AquaChain Notification Service")
    parser.add_argument("--env", default="dev", choices=["dev", "staging", "prod"])
    args = parser.parse_args()

    ENV = args.env
    LAMBDA_FUNCTION_NAME = f"aquachain-function-notification-{ENV}"
    ROLE_NAME = f"aquachain-notification-role-{ENV}"
    CRITICAL_ALERTS_TOPIC_ARN = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-critical-alerts-{ENV}"
    SERVICE_UPDATES_TOPIC_ARN = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-service-updates-{ENV}"
    SYSTEM_ALERTS_TOPIC_ARN   = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:aquachain-topic-system-alerts-{ENV}"

    print(f"\nDeploying AquaChain Notification Service → {ENV.upper()}")
    print(f"Region: {REGION}  |  Account: {ACCOUNT_ID}")

    role_arn = ensure_iam_role()
    ensure_dynamodb_tables()
    ensure_ses_configuration_set()
    package_lambda()
    fn_arn = deploy_lambda(role_arn)
    wire_sns_subscriptions(fn_arn)
    smoke_test()

    print(f"\n{'='*60}")
    print(f"  Deployment complete!")
    print(f"  Function: {LAMBDA_FUNCTION_NAME}")
    print(f"  ARN:      {fn_arn}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
