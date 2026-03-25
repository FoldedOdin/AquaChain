#!/usr/bin/env python3
"""
AquaChain AWS Account Migration Script
Migrates all AquaChain infrastructure and data from one AWS account to another
by exporting data, deploying fresh CDK stacks, and re-importing data.

Usage:
    python migrate_account.py --source-profile <profile> --target-profile <profile> \
                               --environment <dev|staging|prod> [--skip-data] [--dry-run]

Prerequisites:
    - AWS CLI configured with both source and target profiles
    - Python 3.11+ with boto3 installed
    - CDK CLI installed (npm install -g aws-cdk@2.120.0)
    - Sufficient IAM permissions on both accounts

WARNING: This script will create real AWS resources in the target account.
         Estimated cost depends on environment (dev ~$5/month, prod ~$200+/month).
"""

import argparse
import boto3
import json
import os
import subprocess
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
log = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

REGION = "ap-south-1"
CDK_DIR = Path(__file__).resolve().parents[2] / "infrastructure" / "cdk"
EXPORT_DIR = Path(__file__).resolve().parent / "migration_export"

# All DynamoDB tables managed by AquaChain (from data_stack.py)
DYNAMODB_TABLES = [
    "AquaChain-Readings",
    "AquaChain-Ledger",
    "AquaChain-Sequence",
    "AquaChain-Users",
    "AquaChain-ServiceRequests",
    "AquaChain-Devices",
    "AquaChain-PluggableDevices",
    "aquachain-notifications",
    "AquaChain-AuditLogs",
    "AquaChain-SystemConfig",
    "AquaChain-Alerts",
]

# S3 buckets to migrate (data lake, ML models, audit trail)
S3_BUCKET_PREFIXES = [
    "aquachain-data",
    "aquachain-models",
    "aquachain-audit",
    "aquachain-deployments",
    "aquachain-frontend",
]

# Secrets to migrate (names only — values fetched at runtime)
SECRET_PREFIXES = [
    "aquachain/",
]

# CDK stack deployment order (respects dependency graph from app.py)
CDK_STACK_ORDER = [
    "AquaChain-Security-{env}",
    "AquaChain-Core-{env}",
    "AquaChain-Data-{env}",
    "AquaChain-LambdaLayers-{env}",
    "AquaChain-Compute-{env}",
    "AquaChain-API-{env}",
    "AquaChain-WebSocket-{env}",
    "AquaChain-IoTCore-{env}",
    "AquaChain-IoTSecurity-{env}",
    "AquaChain-Monitoring-{env}",
    "AquaChain-DataClassification-{env}",
    "AquaChain-AuditLogging-{env}",
    "AquaChain-GDPRCompliance-{env}",
    "AquaChain-SageMaker-{env}",
    "AquaChain-LambdaPerformance-{env}",
    "AquaChain-Backup-{env}",
    "AquaChain-DR-{env}",
    "AquaChain-CloudFront-{env}",
    "AquaChain-APIThrottling-{env}",
    "AquaChain-Phase3-{env}",
    "AquaChain-DashboardOverhaul-{env}",
    "AquaChain-ProductionMonitoring-{env}",
    "AquaChain-EnhancedOrdering-{env}",
    "AquaChain-AutoTechnicianAssignment-{env}",
    "AquaChain-SecurityAudit-{env}",
    "AquaChain-LedgerSecurity-{env}",
    "AquaChain-ContactService-{env}",
    "AquaChain-PerformanceDashboard-{env}",
    "AquaChain-LandingPage-{env}",
    "AquaChain-VPC-{env}",
]

# ─── AWS Session Helpers ───────────────────────────────────────────────────────

def get_session(profile: str) -> boto3.Session:
    return boto3.Session(profile_name=profile, region_name=REGION)

def get_account_id(session: boto3.Session) -> str:
    return session.client("sts").get_caller_identity()["Account"]

# ─── Phase 1: Export from Source Account ──────────────────────────────────────

def export_dynamodb_table(session: boto3.Session, table_name: str, out_dir: Path) -> int:
    """Scan and export all items from a DynamoDB table to a JSON file."""
    client = session.client("dynamodb")
    out_file = out_dir / f"{table_name}.json"
    items = []

    try:
        paginator = client.get_paginator("scan")
        for page in paginator.paginate(TableName=table_name):
            items.extend(page.get("Items", []))
        with open(out_file, "w") as f:
            json.dump(items, f)
        log.info(f"  Exported {len(items):,} items from {table_name}")
        return len(items)
    except client.exceptions.ResourceNotFoundException:
        log.warning(f"  Table {table_name} not found in source account — skipping")
        return 0
    except Exception as e:
        log.error(f"  Failed to export {table_name}: {e}")
        return 0

def export_cognito_users(session: boto3.Session, out_dir: Path) -> None:
    """Export Cognito user pool IDs and user list (passwords cannot be exported)."""
    client = session.client("cognito-idp")
    pools = client.list_user_pools(MaxResults=60).get("UserPools", [])
    aquachain_pools = [p for p in pools if "aquachain" in p["Name"].lower()]

    for pool in aquachain_pools:
        pool_id = pool["Id"]
        users = []
        paginator = client.get_paginator("list_users")
        for page in paginator.paginate(UserPoolId=pool_id):
            users.extend(page.get("Users", []))

        out_file = out_dir / f"cognito_{pool_id}.json"
        with open(out_file, "w") as f:
            # Convert datetime objects to strings for JSON serialisation
            json.dump(users, f, default=str)
        log.info(f"  Exported {len(users)} users from Cognito pool {pool['Name']} ({pool_id})")
        log.warning(
            f"  NOTE: Cognito passwords cannot be exported. Users will need to reset "
            f"passwords or be re-invited in the target account."
        )

def export_secrets(session: boto3.Session, out_dir: Path) -> None:
    """Export secret names and values from Secrets Manager."""
    client = session.client("secretsmanager")
    secrets_out = []

    paginator = client.get_paginator("list_secrets")
    for page in paginator.paginate():
        for secret in page.get("SecretList", []):
            name = secret["Name"]
            if any(name.startswith(p) for p in SECRET_PREFIXES):
                try:
                    value = client.get_secret_value(SecretId=name)
                    secrets_out.append({
                        "Name": name,
                        "SecretString": value.get("SecretString"),
                        "Description": secret.get("Description", ""),
                    })
                    log.info(f"  Exported secret: {name}")
                except Exception as e:
                    log.warning(f"  Could not read secret {name}: {e}")

    out_file = out_dir / "secrets.json"
    with open(out_file, "w") as f:
        json.dump(secrets_out, f)
    log.info(f"  Total secrets exported: {len(secrets_out)}")
    log.warning("  SECURITY: secrets.json contains sensitive values — delete after migration!")

def export_s3_buckets(session: boto3.Session, out_dir: Path, dry_run: bool) -> None:
    """List S3 buckets and sync their contents to a local directory."""
    s3_client = session.client("s3")
    all_buckets = [b["Name"] for b in s3_client.list_buckets().get("Buckets", [])]
    aquachain_buckets = [
        b for b in all_buckets
        if any(b.startswith(p) for p in S3_BUCKET_PREFIXES)
    ]

    s3_export_dir = out_dir / "s3"
    s3_export_dir.mkdir(exist_ok=True)

    for bucket in aquachain_buckets:
        log.info(f"  Syncing s3://{bucket} → {s3_export_dir / bucket}")
        if not dry_run:
            _run(
                f"aws s3 sync s3://{bucket} {s3_export_dir / bucket} "
                f"--profile {session.profile_name} --region {REGION}",
                check=False
            )
        else:
            log.info(f"  [DRY RUN] Would sync s3://{bucket}")

def run_export(source_session: boto3.Session, env: str, dry_run: bool) -> None:
    """Run all export steps against the source account."""
    log.info("=" * 60)
    log.info("PHASE 1: Exporting data from source account")
    log.info("=" * 60)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    dynamo_dir = EXPORT_DIR / "dynamodb"
    dynamo_dir.mkdir(exist_ok=True)

    total_items = 0
    for table in DYNAMODB_TABLES:
        total_items += export_dynamodb_table(source_session, table, dynamo_dir)

    log.info(f"DynamoDB export complete — {total_items:,} total items")

    log.info("Exporting Cognito users...")
    export_cognito_users(source_session, EXPORT_DIR)

    log.info("Exporting Secrets Manager secrets...")
    if not dry_run:
        export_secrets(source_session, EXPORT_DIR)
    else:
        log.info("  [DRY RUN] Skipping secrets export")

    log.info("Exporting S3 buckets...")
    export_s3_buckets(source_session, EXPORT_DIR, dry_run)

# ─── Phase 2: Bootstrap & Deploy CDK in Target Account ────────────────────────

def bootstrap_cdk(target_profile: str, target_account: str, dry_run: bool) -> None:
    """Bootstrap CDK in the target account."""
    log.info("=" * 60)
    log.info("PHASE 2: Bootstrapping CDK in target account")
    log.info("=" * 60)

    cmd = (
        f"cdk bootstrap aws://{target_account}/{REGION} "
        f"--profile {target_profile}"
    )
    if dry_run:
        log.info(f"  [DRY RUN] Would run: {cmd}")
    else:
        _run(cmd, cwd=CDK_DIR)

def deploy_stacks(target_profile: str, env: str, dry_run: bool) -> None:
    """Deploy all CDK stacks in dependency order."""
    log.info("=" * 60)
    log.info("PHASE 3: Deploying CDK stacks to target account")
    log.info("=" * 60)

    stacks = [s.format(env=env) for s in CDK_STACK_ORDER]

    for stack in stacks:
        log.info(f"  Deploying {stack}...")
        cmd = (
            f"cdk deploy {stack} "
            f"--profile {target_profile} "
            f"--context environment={env} "
            f"--require-approval never "
            f"--outputs-file {EXPORT_DIR / f'{stack}-outputs.json'}"
        )
        if dry_run:
            log.info(f"  [DRY RUN] Would run: {cmd}")
        else:
            result = _run(cmd, cwd=CDK_DIR, check=False)
            if result.returncode != 0:
                log.error(f"  Stack {stack} failed — check output above")
                log.error("  Continuing with remaining stacks...")

# ─── Phase 3: Import Data into Target Account ─────────────────────────────────

def import_dynamodb_table(session: boto3.Session, table_name: str, data_dir: Path) -> int:
    """Batch-write exported items back into a DynamoDB table."""
    data_file = data_dir / f"{table_name}.json"
    if not data_file.exists():
        log.warning(f"  No export file for {table_name} — skipping import")
        return 0

    with open(data_file) as f:
        items = json.load(f)

    if not items:
        log.info(f"  {table_name}: no items to import")
        return 0

    client = session.client("dynamodb")
    batch_size = 25  # DynamoDB batch_write_item limit
    imported = 0
    errors = 0

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        request_items = {
            table_name: [{"PutRequest": {"Item": item}} for item in batch]
        }
        try:
            response = client.batch_write_item(RequestItems=request_items)
            unprocessed = response.get("UnprocessedItems", {})
            if unprocessed:
                log.warning(f"  {len(unprocessed.get(table_name, []))} unprocessed items in batch")
                errors += len(unprocessed.get(table_name, []))
            imported += len(batch) - len(unprocessed.get(table_name, []))
        except Exception as e:
            log.error(f"  Batch write failed for {table_name}: {e}")
            errors += len(batch)

        # Avoid throttling
        time.sleep(0.1)

    log.info(f"  Imported {imported:,} items into {table_name} ({errors} errors)")
    return imported

def import_secrets(session: boto3.Session) -> None:
    """Re-create secrets in the target account."""
    secrets_file = EXPORT_DIR / "secrets.json"
    if not secrets_file.exists():
        log.warning("  No secrets export file found — skipping")
        return

    with open(secrets_file) as f:
        secrets = json.load(f)

    client = session.client("secretsmanager")
    for secret in secrets:
        name = secret["Name"]
        try:
            client.create_secret(
                Name=name,
                Description=secret.get("Description", "Migrated from source account"),
                SecretString=secret["SecretString"],
            )
            log.info(f"  Created secret: {name}")
        except client.exceptions.ResourceExistsException:
            client.put_secret_value(SecretId=name, SecretString=secret["SecretString"])
            log.info(f"  Updated existing secret: {name}")
        except Exception as e:
            log.error(f"  Failed to create secret {name}: {e}")

def import_s3_buckets(target_session: boto3.Session, dry_run: bool) -> None:
    """Sync locally exported S3 data into target account buckets."""
    s3_export_dir = EXPORT_DIR / "s3"
    if not s3_export_dir.exists():
        log.warning("  No S3 export directory found — skipping")
        return

    target_profile = target_session.profile_name
    for bucket_dir in s3_export_dir.iterdir():
        if bucket_dir.is_dir():
            bucket_name = bucket_dir.name
            log.info(f"  Syncing {bucket_dir} → s3://{bucket_name}")
            cmd = (
                f"aws s3 sync {bucket_dir} s3://{bucket_name} "
                f"--profile {target_profile} --region {REGION}"
            )
            if dry_run:
                log.info(f"  [DRY RUN] Would run: {cmd}")
            else:
                _run(cmd, check=False)

def run_import(target_session: boto3.Session, dry_run: bool) -> None:
    """Run all import steps against the target account."""
    log.info("=" * 60)
    log.info("PHASE 4: Importing data into target account")
    log.info("=" * 60)

    dynamo_dir = EXPORT_DIR / "dynamodb"
    total = 0
    for table in DYNAMODB_TABLES:
        if not dry_run:
            total += import_dynamodb_table(target_session, table, dynamo_dir)
        else:
            log.info(f"  [DRY RUN] Would import {table}")

    log.info(f"DynamoDB import complete — {total:,} total items")

    log.info("Importing secrets...")
    if not dry_run:
        import_secrets(target_session)
    else:
        log.info("  [DRY RUN] Skipping secrets import")

    log.info("Importing S3 data...")
    import_s3_buckets(target_session, dry_run)

# ─── Phase 4: Validation ──────────────────────────────────────────────────────

def validate_migration(source_session: boto3.Session, target_session: boto3.Session) -> bool:
    """Compare item counts between source and target to validate migration."""
    log.info("=" * 60)
    log.info("PHASE 5: Validating migration")
    log.info("=" * 60)

    src_client = source_session.client("dynamodb")
    tgt_client = target_session.client("dynamodb")
    all_ok = True

    for table in DYNAMODB_TABLES:
        try:
            src_count = src_client.describe_table(TableName=table)["Table"]["ItemCount"]
        except Exception:
            src_count = "N/A (not in source)"

        try:
            tgt_count = tgt_client.describe_table(TableName=table)["Table"]["ItemCount"]
        except Exception:
            tgt_count = "MISSING"
            all_ok = False

        status = "✓" if src_count == tgt_count else "⚠"
        log.info(f"  {status} {table}: source={src_count}, target={tgt_count}")

    if all_ok:
        log.info("Validation PASSED — all tables present in target account")
    else:
        log.warning("Validation WARNING — some tables missing or counts differ")
        log.warning("Note: DynamoDB ItemCount is approximate and may lag by ~6 hours")

    return all_ok

# ─── Utilities ────────────────────────────────────────────────────────────────

def _run(cmd: str, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command, streaming output to the log."""
    log.debug(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=sys.stdout, stderr=sys.stderr
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}): {cmd}")
    return result

def confirm(prompt: str) -> bool:
    """Ask for explicit user confirmation."""
    answer = input(f"\n{prompt} [yes/no]: ").strip().lower()
    return answer == "yes"

# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate AquaChain from one AWS account to another"
    )
    parser.add_argument("--source-profile", required=True, help="AWS CLI profile for source account")
    parser.add_argument("--target-profile", required=True, help="AWS CLI profile for target account")
    parser.add_argument(
        "--environment", required=True, choices=["dev", "staging", "prod"],
        help="Environment to migrate"
    )
    parser.add_argument(
        "--skip-data", action="store_true",
        help="Skip DynamoDB/S3 data migration (infrastructure only)"
    )
    parser.add_argument(
        "--skip-export", action="store_true",
        help="Skip export phase (use existing export in migration_export/)"
    )
    parser.add_argument(
        "--skip-deploy", action="store_true",
        help="Skip CDK deployment (data import only)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making any changes"
    )
    args = parser.parse_args()

    source_session = get_session(args.source_profile)
    target_session = get_session(args.target_profile)

    source_account = get_account_id(source_session)
    target_account = get_account_id(target_session)

    log.info("=" * 60)
    log.info("AquaChain Account Migration")
    log.info("=" * 60)
    log.info(f"  Source account : {source_account} (profile: {args.source_profile})")
    log.info(f"  Target account : {target_account} (profile: {args.target_profile})")
    log.info(f"  Environment    : {args.environment}")
    log.info(f"  Region         : {REGION}")
    log.info(f"  Dry run        : {args.dry_run}")
    log.info(f"  Skip data      : {args.skip_data}")

    if source_account == target_account:
        log.error("Source and target accounts are the same — aborting")
        sys.exit(1)

    if not args.dry_run:
        if not confirm(
            f"This will deploy AquaChain to account {target_account} and may incur AWS costs. Continue?"
        ):
            log.info("Aborted by user")
            sys.exit(0)

    # Phase 1: Export
    if not args.skip_export and not args.skip_data:
        run_export(source_session, args.environment, args.dry_run)
    else:
        log.info("Skipping export phase")

    # Phase 2: Bootstrap CDK
    if not args.skip_deploy:
        bootstrap_cdk(args.target_profile, target_account, args.dry_run)

    # Phase 3: Deploy stacks
    if not args.skip_deploy:
        deploy_stacks(args.target_profile, args.environment, args.dry_run)

    # Phase 4: Import data
    if not args.skip_data:
        run_import(target_session, args.dry_run)
    else:
        log.info("Skipping data import phase")

    # Phase 5: Validate
    if not args.dry_run and not args.skip_data:
        validate_migration(source_session, target_session)

    log.info("=" * 60)
    log.info("Migration complete")
    log.info("=" * 60)
    log.info("Next steps:")
    log.info("  1. Update frontend .env with new API endpoint and Cognito pool IDs")
    log.info("  2. Re-register IoT devices against the new IoT Core endpoint")
    log.info("  3. Notify Cognito users to reset their passwords")
    log.info("  4. Delete migration_export/secrets.json (contains sensitive values)")
    log.info("  5. Run smoke tests against the new environment")

if __name__ == "__main__":
    main()
