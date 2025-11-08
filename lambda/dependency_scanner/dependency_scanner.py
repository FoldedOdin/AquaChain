"""
Dependency Security Scanner Lambda Function
Automated vulnerability scanning for npm and Python dependencies
"""

import os
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from pathlib import Path

# AWS clients
sns = boto3.client('sns')
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Configuration from environment variables
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'aquachain-security-scans')
SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET', 'aquachain-source-code')
CRITICAL_THRESHOLD = int(os.environ.get('CRITICAL_THRESHOLD', '0'))
HIGH_THRESHOLD = int(os.environ.get('HIGH_THRESHOLD', '5'))


class DependencyScanner:
    """Scan dependencies for security vulnerabilities"""
    
    def __init__(self):
        self.scan_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'scans': {},
            'summary': {}
        }
    
    def scan_npm_dependencies(self, package_json_path: str) -> Dict[str, Any]:
        """
        Scan npm dependencies using npm audit
        
        Args:
            package_json_path: Path to package.json file
            
        Returns:
            Dictionary containing vulnerability summary and details
        """
        print(f"Scanning npm dependencies from {package_json_path}...")
        
        package_dir = Path(package_json_path).parent
        
        if not Path(package_json_path).exists():
            return {'error': 'package.json not found'}
        
        try:
            # Run npm audit
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=package_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # npm audit returns non-zero exit code when vulnerabilities found
            # So we don't check returncode
            
            if not result.stdout:
                return {
                    'total': 0,
                    'critical': 0,
                    'high': 0,
                    'moderate': 0,
                    'low': 0,
                    'info': 0,
                    'details': []
                }
            
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
                severity = vuln_data.get('severity', 'unknown').lower()
                
                # Count by severity
                if severity in summary:
                    summary[severity] += 1
                
                # Extract fix information
                fix_available = vuln_data.get('fixAvailable', False)
                fix_info = None
                if isinstance(fix_available, dict):
                    fix_info = {
                        'name': fix_available.get('name'),
                        'version': fix_available.get('version'),
                        'isSemVerMajor': fix_available.get('isSemVerMajor', False)
                    }
                
                summary['details'].append({
                    'package': pkg_name,
                    'severity': severity,
                    'via': vuln_data.get('via', []),
                    'fixAvailable': bool(fix_available),
                    'fixInfo': fix_info,
                    'range': vuln_data.get('range', 'unknown')
                })
            
            # Generate recommendations
            summary['recommendations'] = self._generate_npm_recommendations(summary['details'])
            
            return summary
            
        except subprocess.TimeoutExpired:
            return {'error': 'npm audit timed out after 5 minutes'}
        except subprocess.CalledProcessError as e:
            return {'error': f'npm audit failed: {e}'}
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse npm audit output: {e}'}
        except Exception as e:
            return {'error': f'Unexpected error during npm scan: {str(e)}'}
    
    def scan_python_dependencies(self, requirements_path: str) -> Dict[str, Any]:
        """
        Scan Python dependencies using pip-audit
        
        Args:
            requirements_path: Path to requirements.txt file
            
        Returns:
            Dictionary containing vulnerability summary and details
        """
        print(f"Scanning Python dependencies from {requirements_path}...")
        
        if not Path(requirements_path).exists():
            return {'error': 'requirements.txt not found'}
        
        try:
            # Ensure pip-audit is available
            self._ensure_pip_audit_installed()
            
            # Run pip-audit
            result = subprocess.run(
                ['pip-audit', '--requirement', requirements_path, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # pip-audit returns 0 if no vulnerabilities, non-zero if found
            if not result.stdout:
                return {
                    'total': 0,
                    'critical': 0,
                    'high': 0,
                    'moderate': 0,
                    'low': 0,
                    'details': []
                }
            
            audit_data = json.loads(result.stdout)
            
            # Parse vulnerabilities
            dependencies = audit_data.get('dependencies', [])
            
            summary = {
                'total': 0,
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0,
                'details': []
            }
            
            for dep in dependencies:
                vulns = dep.get('vulns', [])
                
                for vuln in vulns:
                    summary['total'] += 1
                    
                    # Categorize by severity (pip-audit provides this in newer versions)
                    severity = self._categorize_python_vulnerability(vuln)
                    summary[severity] += 1
                    
                    summary['details'].append({
                        'package': dep.get('name'),
                        'version': dep.get('version'),
                        'vulnerability_id': vuln.get('id'),
                        'description': vuln.get('description', ''),
                        'fix_versions': vuln.get('fix_versions', []),
                        'severity': severity,
                        'aliases': vuln.get('aliases', [])
                    })
            
            # Generate recommendations
            summary['recommendations'] = self._generate_python_recommendations(summary['details'])
            
            return summary
            
        except subprocess.TimeoutExpired:
            return {'error': 'pip-audit timed out after 5 minutes'}
        except subprocess.CalledProcessError as e:
            return {'error': f'pip-audit failed: {e}'}
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse pip-audit output: {e}'}
        except Exception as e:
            return {'error': f'Unexpected error during Python scan: {str(e)}'}
    
    def _ensure_pip_audit_installed(self):
        """Ensure pip-audit is installed"""
        try:
            subprocess.run(
                ['pip-audit', '--version'],
                capture_output=True,
                check=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing pip-audit...")
            subprocess.run(
                ['pip', 'install', 'pip-audit'],
                capture_output=True,
                check=True,
                timeout=60
            )
    
    def _categorize_python_vulnerability(self, vuln: Dict[str, Any]) -> str:
        """
        Categorize Python vulnerability by severity
        
        Uses CVE ID patterns and keywords to estimate severity
        """
        description = vuln.get('description', '').lower()
        vuln_id = vuln.get('id', '').lower()
        
        # Check for critical keywords
        critical_keywords = ['remote code execution', 'rce', 'arbitrary code', 'sql injection']
        if any(keyword in description for keyword in critical_keywords):
            return 'critical'
        
        # Check for high severity keywords
        high_keywords = ['denial of service', 'dos', 'authentication bypass', 'privilege escalation']
        if any(keyword in description for keyword in high_keywords):
            return 'high'
        
        # Check for moderate keywords
        moderate_keywords = ['information disclosure', 'xss', 'csrf']
        if any(keyword in description for keyword in moderate_keywords):
            return 'moderate'
        
        # Default to high for safety
        return 'high'
    
    def _generate_npm_recommendations(self, details: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations for npm vulnerabilities"""
        recommendations = []
        
        # Group by fix availability
        fixable = [d for d in details if d.get('fixAvailable')]
        not_fixable = [d for d in details if not d.get('fixAvailable')]
        
        if fixable:
            recommendations.append(
                f"Run 'npm audit fix' to automatically fix {len(fixable)} vulnerabilities"
            )
            
            # Check for breaking changes
            breaking = [d for d in fixable if d.get('fixInfo', {}).get('isSemVerMajor')]
            if breaking:
                recommendations.append(
                    f"{len(breaking)} fixes require major version updates. "
                    "Review breaking changes before running 'npm audit fix --force'"
                )
        
        if not_fixable:
            recommendations.append(
                f"{len(not_fixable)} vulnerabilities have no automatic fix. "
                "Consider alternative packages or manual updates"
            )
        
        return recommendations
    
    def _generate_python_recommendations(self, details: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations for Python vulnerabilities"""
        recommendations = []
        
        # Group by package
        packages = {}
        for detail in details:
            pkg = detail['package']
            if pkg not in packages:
                packages[pkg] = []
            packages[pkg].append(detail)
        
        for pkg, vulns in packages.items():
            fix_versions = set()
            for vuln in vulns:
                fix_versions.update(vuln.get('fix_versions', []))
            
            if fix_versions:
                recommendations.append(
                    f"Update {pkg} to version {', '.join(sorted(fix_versions))} "
                    f"to fix {len(vulns)} vulnerability(ies)"
                )
            else:
                recommendations.append(
                    f"No fix available for {pkg}. Consider alternative packages"
                )
        
        return recommendations
    
    def generate_report(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive vulnerability report
        
        Args:
            scan_results: Results from all scans
            
        Returns:
            Formatted report with summary and recommendations
        """
        report = {
            'timestamp': scan_results['timestamp'],
            'summary': scan_results['summary'],
            'scans': {},
            'overall_recommendations': [],
            'action_required': False
        }
        
        # Process each scan type
        for scan_type, results in scan_results['scans'].items():
            if 'error' in results:
                report['scans'][scan_type] = {
                    'status': 'error',
                    'error': results['error']
                }
            else:
                report['scans'][scan_type] = {
                    'status': 'success',
                    'total': results.get('total', 0),
                    'by_severity': {
                        'critical': results.get('critical', 0),
                        'high': results.get('high', 0),
                        'moderate': results.get('moderate', 0),
                        'low': results.get('low', 0)
                    },
                    'recommendations': results.get('recommendations', []),
                    'details': results.get('details', [])
                }
        
        # Determine if action is required
        summary = scan_results['summary']
        if summary.get('critical', 0) > CRITICAL_THRESHOLD or summary.get('high', 0) > HIGH_THRESHOLD:
            report['action_required'] = True
            report['overall_recommendations'].append(
                'IMMEDIATE ACTION REQUIRED: Critical or high severity vulnerabilities detected'
            )
        
        # Add overall recommendations
        if summary.get('total_vulnerabilities', 0) > 0:
            report['overall_recommendations'].append(
                f"Total of {summary['total_vulnerabilities']} vulnerabilities found across all dependencies"
            )
            report['overall_recommendations'].append(
                'Review detailed recommendations for each scan type and update dependencies'
            )
        else:
            report['overall_recommendations'].append(
                'No vulnerabilities detected. All dependencies are up to date'
            )
        
        return report
    
    def send_alerts(self, report: Dict[str, Any]) -> None:
        """
        Send SNS alerts for critical vulnerabilities
        
        Args:
            report: Generated vulnerability report
        """
        if not report.get('action_required'):
            print("No critical vulnerabilities found. Skipping alert.")
            return
        
        if not ALERT_TOPIC_ARN:
            print("WARNING: No alert topic configured. Cannot send alerts.")
            return
        
        try:
            summary = report['summary']
            
            # Create alert message
            message = {
                'timestamp': report['timestamp'],
                'severity': 'CRITICAL' if summary.get('critical', 0) > 0 else 'HIGH',
                'summary': {
                    'total_vulnerabilities': summary.get('total_vulnerabilities', 0),
                    'critical': summary.get('critical', 0),
                    'high': summary.get('high', 0),
                    'moderate': summary.get('moderate', 0),
                    'low': summary.get('low', 0)
                },
                'recommendations': report['overall_recommendations'],
                'action_required': 'Review and update dependencies immediately',
                'report_location': f"s3://{RESULTS_BUCKET}/dependency-scans/"
            }
            
            # Send SNS notification
            response = sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject=f"🚨 Dependency Security Alert - AquaChain [{message['severity']}]",
                Message=json.dumps(message, indent=2)
            )
            
            print(f"Alert sent successfully. MessageId: {response['MessageId']}")
            
            # Publish CloudWatch metric
            self._publish_metrics(summary)
            
        except Exception as e:
            print(f"ERROR: Failed to send alert: {e}")
            raise
    
    def _publish_metrics(self, summary: Dict[str, Any]) -> None:
        """Publish vulnerability metrics to CloudWatch"""
        try:
            metrics = []
            
            for severity in ['critical', 'high', 'moderate', 'low']:
                metrics.append({
                    'MetricName': f'Vulnerabilities_{severity.capitalize()}',
                    'Value': summary.get(severity, 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                })
            
            metrics.append({
                'MetricName': 'Vulnerabilities_Total',
                'Value': summary.get('total_vulnerabilities', 0),
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            })
            
            cloudwatch.put_metric_data(
                Namespace='AquaChain/Security',
                MetricData=metrics
            )
            
            print("Metrics published to CloudWatch")
            
        except Exception as e:
            print(f"WARNING: Failed to publish metrics: {e}")


def lambda_handler(event, context):
    """
    Lambda handler for dependency scanning
    
    Event format:
    {
        "scan_type": "all|npm|python",
        "source_paths": {
            "npm": "s3://bucket/path/to/package.json",
            "python": "s3://bucket/path/to/requirements.txt"
        }
    }
    """
    print(f"Starting dependency scan. Event: {json.dumps(event)}")
    
    scanner = DependencyScanner()
    
    try:
        scan_type = event.get('scan_type', 'all')
        source_paths = event.get('source_paths', {})
        
        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Scan npm dependencies
            if scan_type in ['all', 'npm']:
                npm_path = source_paths.get('npm')
                if npm_path:
                    # Download package.json from S3
                    local_package_json = temp_path / 'package.json'
                    _download_from_s3(npm_path, str(local_package_json))
                    
                    # Also need package-lock.json for npm audit
                    lock_path = npm_path.replace('package.json', 'package-lock.json')
                    local_lock = temp_path / 'package-lock.json'
                    try:
                        _download_from_s3(lock_path, str(local_lock))
                    except:
                        print("WARNING: package-lock.json not found, audit may be limited")
                    
                    npm_results = scanner.scan_npm_dependencies(str(local_package_json))
                    scanner.scan_results['scans']['npm'] = npm_results
            
            # Scan Python dependencies
            if scan_type in ['all', 'python']:
                python_paths = source_paths.get('python', [])
                if isinstance(python_paths, str):
                    python_paths = [python_paths]
                
                all_python_results = {
                    'total': 0,
                    'critical': 0,
                    'high': 0,
                    'moderate': 0,
                    'low': 0,
                    'details': [],
                    'recommendations': []
                }
                
                for idx, python_path in enumerate(python_paths):
                    local_requirements = temp_path / f'requirements_{idx}.txt'
                    _download_from_s3(python_path, str(local_requirements))
                    
                    results = scanner.scan_python_dependencies(str(local_requirements))
                    
                    # Aggregate results
                    if 'error' not in results:
                        for key in ['total', 'critical', 'high', 'moderate', 'low']:
                            all_python_results[key] += results.get(key, 0)
                        all_python_results['details'].extend(results.get('details', []))
                        all_python_results['recommendations'].extend(results.get('recommendations', []))
                
                scanner.scan_results['scans']['python'] = all_python_results
        
        # Calculate summary
        scanner.scan_results['summary'] = _calculate_summary(scanner.scan_results['scans'])
        
        # Generate report
        report = scanner.generate_report(scanner.scan_results)
        
        # Save report to S3
        _save_report_to_s3(report)
        
        # Send alerts if needed
        scanner.send_alerts(report)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Dependency scan completed successfully',
                'summary': report['summary'],
                'action_required': report['action_required']
            })
        }
        
    except Exception as e:
        print(f"ERROR: Dependency scan failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Dependency scan failed',
                'error': str(e)
            })
        }


def _download_from_s3(s3_path: str, local_path: str) -> None:
    """Download file from S3"""
    # Parse S3 path
    if s3_path.startswith('s3://'):
        s3_path = s3_path[5:]
    
    parts = s3_path.split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ''
    
    s3.download_file(bucket, key, local_path)
    print(f"Downloaded {s3_path} to {local_path}")


def _save_report_to_s3(report: Dict[str, Any]) -> None:
    """Save report to S3 with versioning"""
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        key = f'dependency-scans/report-{timestamp}.json'
        
        s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json',
            Metadata={
                'scan-timestamp': report['timestamp'],
                'action-required': str(report['action_required'])
            }
        )
        
        # Also save as latest
        s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key='dependency-scans/latest.json',
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        
        print(f"Report saved to s3://{RESULTS_BUCKET}/{key}")
        
    except Exception as e:
        print(f"ERROR: Failed to save report to S3: {e}")
        raise


def _calculate_summary(scans: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall summary from all scans"""
    summary = {
        'total_vulnerabilities': 0,
        'critical': 0,
        'high': 0,
        'moderate': 0,
        'low': 0
    }
    
    for scan_type, results in scans.items():
        if 'error' not in results:
            summary['total_vulnerabilities'] += results.get('total', 0)
            summary['critical'] += results.get('critical', 0)
            summary['high'] += results.get('high', 0)
            summary['moderate'] += results.get('moderate', 0)
            summary['low'] += results.get('low', 0)
    
    return summary
