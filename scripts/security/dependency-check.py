#!/usr/bin/env python3
"""
Dependency Check Script

This script provides utilities for checking and managing dependencies across
the AquaChain project, including:
- Checking for outdated dependencies
- Scanning for security vulnerabilities
- Generating dependency reports
- Validating dependency versions across Lambda functions
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class DependencyChecker:
    """Check and manage project dependencies"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.lambda_dir = self.project_root / "lambda"
        self.frontend_dir = self.project_root / "frontend"
        self.infrastructure_dir = self.project_root / "infrastructure"
        
    def check_frontend_dependencies(self) -> Dict:
        """Check frontend npm dependencies for updates and vulnerabilities"""
        print("🔍 Checking frontend dependencies...")
        
        result = {
            'outdated': [],
            'vulnerabilities': {},
            'status': 'success'
        }
        
        try:
            # Check for outdated packages
            outdated_result = subprocess.run(
                ['npm', 'outdated', '--json'],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            
            if outdated_result.stdout:
                outdated_data = json.loads(outdated_result.stdout)
                result['outdated'] = [
                    {
                        'package': pkg,
                        'current': info['current'],
                        'wanted': info['wanted'],
                        'latest': info['latest']
                    }
                    for pkg, info in outdated_data.items()
                ]
            
            # Check for vulnerabilities
            audit_result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            
            if audit_result.stdout:
                audit_data = json.loads(audit_result.stdout)
                result['vulnerabilities'] = audit_data.get('metadata', {}).get('vulnerabilities', {})
            
            print(f"  ✅ Found {len(result['outdated'])} outdated packages")
            print(f"  🔒 Vulnerabilities: {result['vulnerabilities']}")
            
        except Exception as e:
            print(f"  ❌ Error checking frontend dependencies: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def check_lambda_dependencies(self) -> Dict:
        """Check Lambda function Python dependencies"""
        print("🔍 Checking Lambda dependencies...")
        
        results = {}
        
        for lambda_func in self.lambda_dir.iterdir():
            if not lambda_func.is_dir() or lambda_func.name == 'shared':
                continue
            
            requirements_file = lambda_func / 'requirements.txt'
            if not requirements_file.exists():
                continue
            
            print(f"  📦 Checking {lambda_func.name}...")
            
            func_result = {
                'outdated': [],
                'vulnerabilities': [],
                'status': 'success'
            }
            
            try:
                # Check for outdated packages using pip list --outdated
                outdated_result = subprocess.run(
                    ['pip', 'list', '--outdated', '--format=json'],
                    capture_output=True,
                    text=True
                )
                
                if outdated_result.stdout:
                    outdated_data = json.loads(outdated_result.stdout)
                    
                    # Filter to only packages in requirements.txt
                    with open(requirements_file) as f:
                        required_packages = {
                            line.split('==')[0].strip().lower()
                            for line in f
                            if line.strip() and not line.startswith('#')
                        }
                    
                    func_result['outdated'] = [
                        pkg for pkg in outdated_data
                        if pkg['name'].lower() in required_packages
                    ]
                
                # Check for vulnerabilities using safety
                safety_result = subprocess.run(
                    ['safety', 'check', '--json', '--file', str(requirements_file)],
                    capture_output=True,
                    text=True
                )
                
                if safety_result.stdout:
                    try:
                        safety_data = json.loads(safety_result.stdout)
                        func_result['vulnerabilities'] = safety_data
                    except json.JSONDecodeError:
                        pass
                
                print(f"    ✅ {len(func_result['outdated'])} outdated, "
                      f"{len(func_result['vulnerabilities'])} vulnerabilities")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                func_result['status'] = 'error'
                func_result['error'] = str(e)
            
            results[lambda_func.name] = func_result
        
        return results
    
    def check_version_consistency(self) -> Dict:
        """Check for version inconsistencies across Lambda functions"""
        print("🔍 Checking version consistency across Lambda functions...")
        
        package_versions = defaultdict(set)
        
        for lambda_func in self.lambda_dir.iterdir():
            if not lambda_func.is_dir() or lambda_func.name == 'shared':
                continue
            
            requirements_file = lambda_func / 'requirements.txt'
            if not requirements_file.exists():
                continue
            
            with open(requirements_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '==' in line:
                        package, version = line.split('==')
                        package_versions[package.strip()].add((version.strip(), lambda_func.name))
        
        # Find inconsistencies
        inconsistencies = {}
        for package, versions in package_versions.items():
            if len(versions) > 1:
                inconsistencies[package] = list(versions)
        
        if inconsistencies:
            print("  ⚠️  Version inconsistencies found:")
            for package, versions in inconsistencies.items():
                print(f"    {package}:")
                for version, func in sorted(versions):
                    print(f"      - {version} in {func}")
        else:
            print("  ✅ All package versions are consistent")
        
        return inconsistencies
    
    def generate_dependency_report(self, output_file: Path = None) -> Dict:
        """Generate comprehensive dependency report"""
        print("\n" + "="*60)
        print("DEPENDENCY REPORT")
        print("="*60 + "\n")
        
        report = {
            'timestamp': subprocess.run(
                ['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'],
                capture_output=True,
                text=True
            ).stdout.strip(),
            'frontend': self.check_frontend_dependencies(),
            'lambda': self.check_lambda_dependencies(),
            'version_consistency': self.check_version_consistency()
        }
        
        # Calculate summary
        total_outdated = len(report['frontend']['outdated'])
        total_vulnerabilities = sum(report['frontend']['vulnerabilities'].values())
        
        for func_result in report['lambda'].values():
            total_outdated += len(func_result.get('outdated', []))
            total_vulnerabilities += len(func_result.get('vulnerabilities', []))
        
        report['summary'] = {
            'total_outdated_packages': total_outdated,
            'total_vulnerabilities': total_vulnerabilities,
            'version_inconsistencies': len(report['version_consistency'])
        }
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total outdated packages: {total_outdated}")
        print(f"Total vulnerabilities: {total_vulnerabilities}")
        print(f"Version inconsistencies: {len(report['version_consistency'])}")
        print("="*60 + "\n")
        
        # Save report
        if output_file:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to: {output_file}")
        
        return report
    
    def update_all_dependencies(self, dry_run: bool = True):
        """Update all dependencies (with dry-run option)"""
        print("\n" + "="*60)
        print("UPDATE DEPENDENCIES" + (" (DRY RUN)" if dry_run else ""))
        print("="*60 + "\n")
        
        if dry_run:
            print("⚠️  This is a dry run. No changes will be made.")
            print("    Run with --no-dry-run to apply updates.\n")
        
        # Update frontend dependencies
        print("📦 Frontend dependencies:")
        if dry_run:
            print("  Would run: npm update")
        else:
            subprocess.run(['npm', 'update'], cwd=self.frontend_dir)
            print("  ✅ Updated")
        
        # Update Lambda dependencies
        print("\n📦 Lambda dependencies:")
        for lambda_func in self.lambda_dir.iterdir():
            if not lambda_func.is_dir() or lambda_func.name == 'shared':
                continue
            
            requirements_file = lambda_func / 'requirements.txt'
            if not requirements_file.exists():
                continue
            
            print(f"  {lambda_func.name}:")
            if dry_run:
                print(f"    Would update packages in {requirements_file}")
            else:
                # This would require more sophisticated logic to update requirements.txt
                print(f"    ⚠️  Manual update required for {requirements_file}")
        
        print("\n" + "="*60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check and manage AquaChain project dependencies'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for outdated dependencies and vulnerabilities'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive dependency report'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for report (JSON format)'
    )
    parser.add_argument(
        '--consistency',
        action='store_true',
        help='Check version consistency across Lambda functions'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update all dependencies'
    )
    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Actually apply updates (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    if args.check:
        checker.check_frontend_dependencies()
        checker.check_lambda_dependencies()
    elif args.consistency:
        checker.check_version_consistency()
    elif args.update:
        checker.update_all_dependencies(dry_run=not args.no_dry_run)
    elif args.report:
        output_file = args.output or 'dependency-report.json'
        checker.generate_dependency_report(Path(output_file))
    else:
        # Default: generate report
        checker.generate_dependency_report()


if __name__ == '__main__':
    main()
