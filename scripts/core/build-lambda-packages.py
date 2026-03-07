#!/usr/bin/env python3
"""
Build Lambda deployment packages for the Dashboard Overhaul system
"""

import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path

def create_lambda_package(service_name: str, source_dir: str, output_dir: str) -> str:
    """
    Create a Lambda deployment package for a service
    
    Args:
        service_name: Name of the service
        source_dir: Source directory containing the Lambda code
        output_dir: Output directory for the package
        
    Returns:
        Path to the created package
    """
    
    print(f"Building package for {service_name}...")
    
    # Create temporary build directory
    build_dir = Path(f"build/{service_name}")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy source code
    source_path = Path(source_dir)
    if source_path.exists():
        shutil.copytree(source_path, build_dir / "src", dirs_exist_ok=True)
    else:
        print(f"Warning: Source directory {source_dir} not found")
        return None
    
    # Copy shared utilities
    shared_dir = Path("lambda/shared")
    if shared_dir.exists():
        shutil.copytree(shared_dir, build_dir / "shared", dirs_exist_ok=True)
    
    # Install dependencies if requirements.txt exists
    requirements_file = source_path / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing dependencies for {service_name}...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", str(requirements_file),
            "-t", str(build_dir)
        ], check=True)
    
    # Create ZIP package
    package_path = Path(output_dir) / f"{service_name}.zip"
    package_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    # Clean up build directory
    shutil.rmtree(build_dir)
    
    print(f"Package created: {package_path}")
    return str(package_path)

def main():
    """
    Main function to build all Lambda packages
    """
    
    # Define Lambda services to build
    lambda_services = [
        ("rbac-service", "lambda/rbac_service"),
        ("audit-service", "lambda/audit_service"),
        ("inventory-service", "lambda/inventory_management"),
        ("warehouse-service", "lambda/warehouse_management"),
        ("supplier-service", "lambda/supplier_management"),
        ("procurement-service", "lambda/procurement_service"),
        ("budget-service", "lambda/budget_service"),
        ("workflow-service", "lambda/workflow_service"),
        ("jwt-middleware", "lambda/jwt_middleware"),
        ("monitoring-service", "lambda/monitoring")
    ]
    
    output_dir = "lambda-packages"
    
    # Clean output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Build packages
    built_packages = []
    for service_name, source_dir in lambda_services:
        package_path = create_lambda_package(service_name, source_dir, output_dir)
        if package_path:
            built_packages.append(package_path)
    
    print(f"\nBuilt {len(built_packages)} Lambda packages:")
    for package in built_packages:
        print(f"  - {package}")
    
    # Create deployment manifest
    manifest = {
        "packages": built_packages,
        "build_timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    }
    
    import json
    with open(f"{output_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDeployment manifest created: {output_dir}/manifest.json")

if __name__ == "__main__":
    main()