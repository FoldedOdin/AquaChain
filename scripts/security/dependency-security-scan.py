#!/usr/bin/env python3
"""
Dependency Security Scanner
Automated vulnerability scanning for npm and Python dependencies
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any
import boto3
from pathlib import Path

sns = boto3.client('sns')
s3 = boto3.client('s3')

# Configuration
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'aquachain-security-scans')
CRITICAL_THRESHOLD = 0  # Alert on any critical vulnerabilities
HIGH_THRESHOLD = 5  # Alert if more than 5 high vulnerabilities


class DependencyScanner:
    """Scan dependencies for security vulnerabilities"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.scan_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'scans': {}
        }
    
    def scan_npm_dependencies(self) -> Dict[str, Any]:
        """Scan npm dependencies using npm audit"""
        print("Scanning npm dependencies...")
        
        frontend_dir = self.project_root / 'frontend'
        
        if not (frontend_dir / 'package.json').exists():
            return {'error': 'package.json not found'}
        
        try:
            # Run npm audit
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            audit_data = json.loads(result.stdout)
            
            # Parse vulnerabilities
            vulnerabilities = audit_data.get('vulnerabilities', {})
            
            summary = {
                'total': len(vulnerabilities),
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0,
                'info': 0,
                'details': []
            }
            
            for pkg_name, vuln_data in vulnerabilities.items():
                severity = vuln_data.get('severity', 'unknown')
                summary[severity] = summary.get(severity, 0) + 1
                
                summary['details'].append({
                    'package': pkg_name,
                    'severity': severity,
                    'via': vuln_data.get('via', []),
                    'fixAvailable': vuln_data.get('fixAvailable', False)
                })
            
            return summary
            
        except subprocess.CalledProcessError as e:
            return {'error': f'npm audit failed: {e}'}
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse npm audit output: {e}'}
    
    def scan_python_dependencies(self) -> Dict[str, Any]:
        """Scan Python dependencies using pip-audit"""
        print("Scanning Python dependencies...")
        
        try:
            # Check if pip-audit is installed
            subprocess.run(
                ['pip-audit', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing pip-audit...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pip-audit'])
        
        try:
            # Run pip-audit
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                audit_data = json.loads(result.stdout)
            else:
                audit_data = {'dependencies': []}
            
            # Parse vulnerabilities
            vulnerabilities = audit_data.get('dependencies', [])
            
            summary = {
                'total': len(vulnerabilities),
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0,
                'details': []
            }
            
            for vuln in vulnerabilities:
                # pip-audit doesn't provide severity, so we estimate based on CVSS
                vulns = vuln.get('vulns', [])
                for v in vulns:
                    # Estimate severity from description or default to high
                    severity = 'high'
                    summary[severity] = summary.get(severity, 0) + 1
                    
                    summary['details'].append({
                        'package': vuln.get('name'),
                        'version': vuln.get('version'),
                        'vulnerability_id': v.get('id'),
                        'description': v.get('description'),
                        'fix_versions': v.get('fix_versions', [])
                    })
            
            return summary
            
        except subprocess.CalledProcessError as e:
            return {'error': f'pip-audit failed: {e}'}
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse pip-audit output: {e}'}
    
    def run_all_scans(self) -> Dict[str, Any]:
        """Run all dependency scans"""
        print("Starting dependency security scans...")
        
        # Scan npm dependencies
        npm_results = self.scan_npm_dependencies()
        self.scan_results['scans']['npm'] = npm_results
        
        # Scan Python dependencies
        python_results = self.scan_python_dependencies()
        self.scan_results['scans']['python'] = python_results
        
        # Calculate totals
        self.scan_results['summary'] = self._calculate_summary()
        
        # Save results
        self._save_results()
        
        # Check thresholds and alert if needed
        self._check_thresholds()
        
        return self.scan_results
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate overall summary"""
        summary = {
            'total_vulnerabilities': 0,
            'critical': 0,
            'high': 0,
            'moderate': 0,
            'low': 0
        }
        
        for scan_type, results in self.scan_results['scans'].items():
            if 'error' not in results:
                summary['total_vulnerabilities'] += results.get('total', 0)
                summary['critical'] += results.get('critical', 0)
                summary['high'] += results.get('high', 0)
                summary['moderate'] += results.get('moderate', 0)
                summary['low'] += results.get('low', 0)
        
        return summary
    
    def _save_results(self):
        """Save scan results to S3"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
            key = f'dependency-scans/{timestamp}.json'
            
            s3.put_object(
                Bucket=RESULTS_BUCKET,
                Key=key,
                Body=json.dumps(self.scan_results, indent=2),
                ContentType='application/json'
            )
            
            print(f"Results saved to s3://{RESULTS_BUCKET}/{key}")
            
        except Exception as e:
            print(f"Error saving results to S3: {e}")
    
    def _check_thresholds(self):
        """Check if vulnerabilities exceed thresholds"""
        summary = self.scan_results['summary']
        
        critical_count = summary.get('critical', 0)
        high_count = summary.get('high', 0)
        
        if critical_count > CRITICAL_THRESHOLD or high_count > HIGH_THRESHOLD:
            self._send_alert(summary)
    
    def _send_alert(self, summary: Dict[str, Any]):
        """Send SNS alert for vulnerabilities"""
        if not ALERT_TOPIC_ARN:
            print("No alert topic configured")
            return
        
        try:
            message = {
                'timestamp': self.scan_results['timestamp'],
                'severity': 'CRITICAL' if summary['critical'] > 0 else 'HIGH',
                'summary': summary,
                'action_required': 'Review and update dependencies immediately'
            }
            
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject='Dependency Security Alert - AquaChain',
                Message=json.dumps(message, indent=2)
            )
            
            print("Alert sent successfully")
            
        except Exception as e:
            print(f"Error sending alert: {e}")


def main():
    """Main entry point"""
    scanner = DependencyScanner()
    results = scanner.run_all_scans()
    
    # Print summary
    print("\n" + "="*60)
    print("DEPENDENCY SECURITY SCAN RESULTS")
    print("="*60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"\nTotal Vulnerabilities: {results['summary']['total_vulnerabilities']}")
    print(f"  Critical: {results['summary']['critical']}")
    print(f"  High: {results['summary']['high']}")
    print(f"  Moderate: {results['summary']['moderate']}")
    print(f"  Low: {results['summary']['low']}")
    print("="*60)
    
    # Exit with error code if critical or high vulnerabilities found
    if results['summary']['critical'] > 0 or results['summary']['high'] > HIGH_THRESHOLD:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
