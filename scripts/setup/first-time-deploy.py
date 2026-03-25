#!/usr/bin/env python3
"""
AquaChain First-Time Deployment Script
For contributors setting up their own AWS account from scratch.

This script will:
  1. Check all required tools are installed
  2. Guide through AWS account + credentials setup
  3. Bootstrap CDK in the new account
  4. Deploy all AquaChain stacks
  5. Print the live API endpoint and next steps

Usage:
    python scripts/setup/first-time-deploy.py [--environment dev|staging|prod] [--region ap-south-1]

Requirements:
    - Python 3.11+
    - An AWS account (free tier works for dev)
    - Internet connection
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
CDK_DIR = ROOT / "infrastructure" / "cdk"
FRONTEND_DIR = ROOT / "frontend"

# ─── Colours (disabled on Windows CMD) ───────────────────────────────────────

IS_WIN = platform.system() == "Windows"

def c(text: str, code: str) -> str:
    if IS_WIN:
        return text
    return f"\033[{code}m{text}\033[0m"

def ok(msg):   print(c(f"  ✓  {msg}", "32"))
def warn(msg): print(c(f"  ⚠  {msg}", "33"))
def err(msg):  print(c(f"  ✗  {msg}", "31"))
def info(msg): print(c(f"  →  {msg}", "36"))
def hdr(msg):  print(c(f"\n{'─'*60}\n  {msg}\n{'─'*60}", "34"))

# ─── Shell helpers ────────────────────────────────────────────────────────────

def run(cmd: str, cwd: Path = ROOT, capture: bool = False, check: bool = True):
    """Run a shell command. Returns CompletedProcess."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture,
        text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr or ''}")
    return result

def run_out(cmd: str, cwd: Path = ROOT) -> str:
    """Run a command and return stripped stdout."""
    return run(cmd, cwd=cwd, capture=True).stdout.strip()

def which(tool: str) -> bool:
    """Check if a CLI tool is available."""
    try:
        run(f"{'where' if IS_WIN else 'which'} {tool}", capture=True)
        return True
    except RuntimeError:
        return False

def pause(prompt: str = "Press Enter to continue..."):
    input(c(f"\n  {prompt}", "33"))

# ─── Step 1: Tool checks ──────────────────────────────────────────────────────

REQUIRED_TOOLS = {
    "python": {
        "check": "python --version",
        "install": "https://www.python.org/downloads/",
        "min_version": "3.11",
    },
    "node": {
        "check": "node --version",
        "install": "https://nodejs.org/en/download/ (LTS version)",
        "min_version": "18",
    },
    "npm": {
        "check": "npm --version",
        "install": "Comes with Node.js",
    },
    "aws": {
        "check": "aws --version",
        "install": "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html",
    },
    "git": {
        "check": "git --version",
        "install": "https://git-scm.com/downloads",
    },
}

def check_tools() -> bool:
    hdr("Step 1 of 5 — Checking required tools")
    all_ok = True

    for tool, meta in REQUIRED_TOOLS.items():
        if which(tool):
            try:
                version = run_out(meta["check"])
                ok(f"{tool}: {version}")
            except Exception:
                ok(f"{tool}: found")
        else:
            err(f"{tool} not found")
            info(f"Install from: {meta['install']}")
            all_ok = False

    # CDK is optional — we'll install it if missing
    if which("cdk"):
        version = run_out("cdk --version")
        ok(f"cdk: {version}")
    else:
        warn("AWS CDK CLI not found — will install automatically")

    if not all_ok:
        print()
        err("Please install the missing tools above, then re-run this script.")
        sys.exit(1)

    return True

# ─── Step 2: AWS credentials ──────────────────────────────────────────────────

def check_aws_credentials(profile: str) -> str:
    """Verify AWS credentials work and return the account ID."""
    hdr("Step 2 of 5 — AWS account setup")

    profile_flag = f"--profile {profile}" if profile else ""

    # Try existing credentials first
    try:
        identity = json.loads(run_out(f"aws sts get-caller-identity {profile_flag} --output json"))
        account_id = identity["Account"]
        user_arn = identity["Arn"]
        ok(f"AWS credentials valid")
        ok(f"Account ID : {account_id}")
        ok(f"Identity   : {user_arn}")
        return account_id
    except Exception:
        pass

    # Credentials not configured — guide the user
    print()
    warn("AWS credentials not configured for this profile.")
    print("""
  To set up your AWS account:

  1. Create a free AWS account at https://aws.amazon.com/free/
     (credit card required but dev usage stays within free tier)

  2. In the AWS Console:
     → IAM → Users → Create user
     → Attach policy: AdministratorAccess  (for initial setup)
     → Security credentials → Create access key → CLI

  3. Run this command and paste your keys:
""")
    info(f"aws configure{' --profile ' + profile if profile else ''}")
    print("""
     AWS Access Key ID:     [paste here]
     AWS Secret Access Key: [paste here]
     Default region:        ap-south-1
     Default output format: json
""")
    pause("Once configured, press Enter to continue...")

    # Retry
    try:
        identity = json.loads(run_out(f"aws sts get-caller-identity {profile_flag} --output json"))
        account_id = identity["Account"]
        ok(f"AWS credentials valid — account {account_id}")
        return account_id
    except Exception:
        err("Still can't authenticate. Check your credentials and try again.")
        sys.exit(1)

# ─── Step 3: Install CDK + Python deps ───────────────────────────────────────

def install_dependencies(profile: str) -> None:
    hdr("Step 3 of 5 — Installing dependencies")

    # CDK CLI
    if not which("cdk"):
        info("Installing AWS CDK CLI...")
        run("npm install -g aws-cdk@2.120.0")
        ok("CDK CLI installed")
    else:
        ok("CDK CLI already installed")

    # CDK Python deps
    info("Installing CDK Python dependencies...")
    run("pip install -r requirements.txt", cwd=CDK_DIR)
    ok("CDK Python dependencies installed")

    # Frontend deps
    info("Installing frontend npm dependencies...")
    run("npm install --legacy-peer-deps", cwd=FRONTEND_DIR)
    ok("Frontend dependencies installed")

# ─── Step 4: Bootstrap + Deploy ──────────────────────────────────────────────

CDK_STACKS = [
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

def deploy_infrastructure(account_id: str, env: str, region: str, profile: str) -> dict:
    hdr("Step 4 of 5 — Deploying infrastructure")

    profile_flag = f"--profile {profile}" if profile else ""
    outputs_dir = ROOT / "scripts" / "setup" / "deploy_outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Bootstrap CDK
    info(f"Bootstrapping CDK in account {account_id} / {region}...")
    run(
        f"cdk bootstrap aws://{account_id}/{region} "
        f"{profile_flag} --context environment={env}",
        cwd=CDK_DIR
    )
    ok("CDK bootstrapped")

    # Deploy stacks
    stacks = [s.format(env=env) for s in CDK_STACKS]
    failed = []

    for i, stack in enumerate(stacks, 1):
        info(f"[{i}/{len(stacks)}] Deploying {stack}...")
        outputs_file = outputs_dir / f"{stack}.json"
        result = subprocess.run(
            f"cdk deploy {stack} "
            f"--require-approval never "
            f"--context environment={env} "
            f"--outputs-file {outputs_file} "
            f"{profile_flag}",
            shell=True, cwd=CDK_DIR
        )
        if result.returncode == 0:
            ok(f"{stack}")
        else:
            warn(f"{stack} failed — continuing with remaining stacks")
            failed.append(stack)

    if failed:
        print()
        warn(f"{len(failed)} stack(s) failed to deploy:")
        for s in failed:
            print(f"     - {s}")
        warn("You can re-run with --skip-install to retry just the failed stacks")

    # Collect all outputs
    all_outputs = {}
    for f in outputs_dir.glob("*.json"):
        try:
            with open(f) as fh:
                all_outputs.update(json.load(fh))
        except Exception:
            pass

    return all_outputs

# ─── Step 5: Post-deploy summary ─────────────────────────────────────────────

def print_summary(outputs: dict, env: str, region: str) -> None:
    hdr("Step 5 of 5 — Deployment complete")

    # Try to extract useful values from CDK outputs
    api_url = None
    cognito_pool_id = None
    cognito_client_id = None
    cloudfront_url = None

    for stack_outputs in outputs.values():
        if isinstance(stack_outputs, dict):
            for key, val in stack_outputs.items():
                k = key.lower()
                if "apiurl" in k or "apiendpoint" in k:
                    api_url = val
                if "userpoolid" in k:
                    cognito_pool_id = val
                if "userpoolclientid" in k or "clientid" in k:
                    cognito_client_id = val
                if "cloudfronturl" in k or "distributionurl" in k:
                    cloudfront_url = val

    print()
    ok("AquaChain deployed successfully to your AWS account!")
    print()

    if api_url:
        print(c(f"  API Endpoint   : {api_url}", "32"))
    if cognito_pool_id:
        print(c(f"  Cognito Pool   : {cognito_pool_id}", "32"))
    if cognito_client_id:
        print(c(f"  Cognito Client : {cognito_client_id}", "32"))
    if cloudfront_url:
        print(c(f"  Frontend URL   : {cloudfront_url}", "32"))

    print()
    print(c("  Next steps:", "33"))
    print("""
  1. Create your frontend environment file:

       cp frontend/.env.example frontend/.env.local

     Then fill in the values printed above (API endpoint, Cognito IDs).

  2. Start the frontend dev server:

       cd frontend && npm start

  3. Create your first admin user in AWS Console:
       → Cognito → User Pools → [your pool] → Create user

  4. Register an IoT device (or use the simulator):

       python iot-simulator/simulator.py --mode aws --devices 1

  5. Check CloudWatch logs if anything looks wrong:
       → CloudWatch → Log groups → /aws/lambda/...
""")
    print(c("  Full docs: docker/README.md and DOCS/development/LOCAL_DEVELOPMENT_GUIDE.md", "36"))
    print()

# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="First-time AquaChain deployment to a new AWS account"
    )
    parser.add_argument(
        "--environment", "-e",
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Environment to deploy (default: dev)"
    )
    parser.add_argument(
        "--region", "-r",
        default="ap-south-1",
        help="AWS region (default: ap-south-1)"
    )
    parser.add_argument(
        "--profile", "-p",
        default="",
        help="AWS CLI profile name (leave blank for default profile)"
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation (if already done)"
    )
    args = parser.parse_args()

    print()
    print(c("  AquaChain — First-Time Deployment", "1;36"))
    print(c(f"  Environment: {args.environment}  |  Region: {args.region}", "36"))
    print()

    # Step 1
    check_tools()

    # Step 2
    account_id = check_aws_credentials(args.profile)

    # Step 3
    if not args.skip_install:
        install_dependencies(args.profile)
    else:
        info("Skipping dependency installation (--skip-install)")

    # Confirm before spending money
    print()
    print(c(f"  Ready to deploy AquaChain to AWS account {account_id}.", "33"))
    print(c(f"  This will create real AWS resources. Dev environment stays within free tier.", "33"))
    print()
    answer = input(c("  Type 'yes' to continue: ", "33")).strip().lower()
    if answer != "yes":
        print("  Aborted.")
        sys.exit(0)

    # Step 4
    outputs = deploy_infrastructure(account_id, args.environment, args.region, args.profile)

    # Step 5
    print_summary(outputs, args.environment, args.region)

if __name__ == "__main__":
    main()
