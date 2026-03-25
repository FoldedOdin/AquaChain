# AquaChain Account Migration Guide

Migrates the entire AquaChain stack from one AWS account to another by:
1. Exporting all DynamoDB data, Cognito users, S3 objects, and Secrets Manager values
2. Bootstrapping CDK and deploying all 30+ stacks in the correct dependency order
3. Re-importing all data into the new account
4. Validating item counts match

---

## Do I need the target account number?

No — you don't need to hardcode it anywhere. CDK reads the account ID automatically
from the target profile's credentials via `sts:GetCallerIdentity`. Just configure
the AWS CLI profile for the target account and the script handles the rest.

What you actually need:
- The target account's **Access Key ID** and **Secret Access Key** (from IAM)
- Those go into `aws configure --profile aquachain-target`
- That's it — CDK bootstrap will detect the account number automatically

---

## Prerequisites

- AWS CLI configured with **two named profiles** (source and target)
- Python 3.11+ with `boto3` installed (`pip install boto3`)
- CDK CLI: `npm install -g aws-cdk@2.120.0`
- Sufficient IAM permissions on both accounts (AdministratorAccess recommended for migration)

### Configure AWS profiles

```bash
# Source account (existing)
aws configure --profile aquachain-source

# Target account (new)
aws configure --profile aquachain-target
```

---

## Usage

### Full migration (recommended first run as dry-run)

```bash
# Dry run — shows what would happen, no changes made
python scripts/migration/migrate_account.py \
  --source-profile aquachain-source \
  --target-profile aquachain-target \
  --environment dev \
  --dry-run

# Real migration
python scripts/migration/migrate_account.py \
  --source-profile aquachain-source \
  --target-profile aquachain-target \
  --environment dev
```

### Infrastructure only (no data)

```bash
python scripts/migration/migrate_account.py \
  --source-profile aquachain-source \
  --target-profile aquachain-target \
  --environment dev \
  --skip-data
```

### Re-run data import only (if CDK already deployed)

```bash
python scripts/migration/migrate_account.py \
  --source-profile aquachain-source \
  --target-profile aquachain-target \
  --environment dev \
  --skip-deploy
```

---

## What Gets Migrated

| Resource | Migrated | Notes |
|---|---|---|
| DynamoDB tables | ✓ Full scan + batch write | All 11 tables |
| S3 buckets | ✓ aws s3 sync | data, models, audit, deployments, frontend |
| Secrets Manager | ✓ Values copied | Delete `secrets.json` after migration |
| Cognito users | ✓ User list exported | Passwords cannot be migrated — users must reset |
| Lambda functions | ✓ Redeployed via CDK | Fresh deployment from source code |
| API Gateway | ✓ Redeployed via CDK | New endpoint URLs will be generated |
| IoT Core | ✓ Redeployed via CDK | Devices need re-registration |
| CloudWatch | ✓ Redeployed via CDK | Historical metrics not migrated |
| CDK stacks | ✓ All 30 stacks | Deployed in dependency order |

---

## After Migration

1. **Update frontend config** — new API Gateway URL and Cognito pool IDs will be different
2. **Re-register IoT devices** — new IoT Core endpoint in target account
3. **Notify users** — Cognito passwords cannot be migrated; send password reset emails
4. **Delete secrets file** — `scripts/migration/migration_export/secrets.json` contains plaintext secrets
5. **Run smoke tests** — verify all endpoints respond correctly

```bash
# Delete sensitive export file
rm scripts/migration/migration_export/secrets.json
```

---

## Flags Reference

| Flag | Description |
|---|---|
| `--source-profile` | AWS CLI profile for source account (required) |
| `--target-profile` | AWS CLI profile for target account (required) |
| `--environment` | `dev`, `staging`, or `prod` (required) |
| `--dry-run` | Print actions without making changes |
| `--skip-data` | Deploy infrastructure only, skip DynamoDB/S3 |
| `--skip-export` | Skip export phase, use existing `migration_export/` |
| `--skip-deploy` | Skip CDK deployment, run data import only |

---

## Troubleshooting

**CDK bootstrap fails**
- Ensure the target account has no existing CDK bootstrap stack, or use `--force` flag

**DynamoDB table not found during import**
- The CDK stack may not have finished deploying — wait and re-run with `--skip-export --skip-deploy`

**Secrets already exist in target**
- The script will update existing secrets with `put_secret_value` — safe to re-run

**Stack deployment fails**
- Check the migration log file (`migration_YYYYMMDD_HHMMSS.log`) for the specific error
- Fix the issue and re-run with `--skip-export` to avoid re-exporting data
