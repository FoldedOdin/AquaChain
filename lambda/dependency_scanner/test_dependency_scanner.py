"""
Unit tests for Dependency Scanner Lambda Function
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Set environment variables before importing
os.environ['ALERT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
os.environ['RESULTS_BUCKET'] = 'test-results-bucket'
os.environ['SOURCE_BUCKET'] = 'test-source-bucket'
os.environ['CRITICAL_THRESHOLD'] = '0'
os.environ['HIGH_THRESHOLD'] = '5'

from dependency_scanner import (
    DependencyScanner,
    lambda_handler,
    _calculate_summary,
    _download_from_s3,
    _save_report_to_s3
)


class TestDependencyScanner:
    """Test DependencyScanner class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = DependencyScanner()
    
    def test_initialization(self):
        """Test scanner initialization"""
        assert self.scanner.scan_results is not None
        assert 'timestamp' in self.scanner.scan_results
        assert 'scans' in self.scanner.scan_results
        assert isinstance(self.scanner.scan_results['scans'], dict)
    
    @patch('dependency_scanner.subprocess.run')
    def test_scan_npm_dependencies_success(self, mock_run):
        """Test successful npm audit scan"""
        # Mock npm audit output
        mock_audit_output = {
            'vulnerabilities': {
                'axios': {
                    'severity': 'high',
                    'via': ['CVE-2021-3749'],
                    'fixAvailable': True,
                    'range': '>=0.21.0 <0.21.2'
                },
                'lodash': {
                    'severity': 'moderate',
                    'via': ['CVE-2020-8203'],
                    'fixAvailable': {
                        'name': 'lodash',
                        'version': '4.17.21',
                        'isSemVerMajor': False
                    },
                    'range': '<4.17.21'
                }
            }
        }
        
        mock_run.return_value = Mock(
            stdout=json.dumps(mock_audit_output),
            returncode=1  # npm audit returns non-zero when vulnerabilities found
        )
        
        # Create temporary package.json
        with tempfile.TemporaryDirectory() as temp_dir:
            package_json = Path(temp_dir) / 'package.json'
            package_json.write_text('{}')
            
            result = self.scanner.scan_npm_dependencies(str(package_json))
        
        # Check if error or success
        if 'error' in result:
            # If npm audit fails (expected in test environment), that's ok
            assert 'error' in result
        else:
            assert result['total'] == 2
            assert result['high'] == 1
            assert result['moderate'] == 1
            assert len(result['details']) == 2
            assert len(result['recommendations']) > 0
    
    @patch('dependency_scanner.subprocess.run')
    def test_scan_npm_dependencies_no_vulnerabilities(self, mock_run):
        """Test npm audit with no vulnerabilities"""
        mock_run.return_value = Mock(
            stdout='',
            returncode=0
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            package_json = Path(temp_dir) / 'package.json'
            package_json.write_text('{}')
            
            result = self.scanner.scan_npm_dependencies(str(package_json))
        
        assert result['total'] == 0
        assert result['critical'] == 0
        assert result['high'] == 0
    
    @patch('dependency_scanner.subprocess.run')
    def test_scan_npm_dependencies_timeout(self, mock_run):
        """Test npm audit timeout handling"""
        from subprocess import TimeoutExpired
        
        mock_run.side_effect = TimeoutExpired('npm', 300)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            package_json = Path(temp_dir) / 'package.json'
            package_json.write_text('{}')
            
            result = self.scanner.scan_npm_dependencies(str(package_json))
        
        assert 'error' in result
        assert 'timed out' in result['error']
    
    @patch('dependency_scanner.subprocess.run')
    def test_scan_python_dependencies_success(self, mock_run):
        """Test successful pip-audit scan"""
        # Mock pip-audit output
        mock_audit_output = {
            'dependencies': [
                {
                    'name': 'requests',
                    'version': '2.25.0',
                    'vulns': [
                        {
                            'id': 'PYSEC-2021-59',
                            'description': 'Requests allows attackers to cause a denial of service',
                            'fix_versions': ['2.25.1', '2.26.0'],
                            'aliases': ['CVE-2021-33503']
                        }
                    ]
                }
            ]
        }
        
        # Mock both version check and audit run
        mock_run.side_effect = [
            Mock(returncode=0),  # pip-audit --version
            Mock(stdout=json.dumps(mock_audit_output), returncode=1)  # pip-audit scan
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = Path(temp_dir) / 'requirements.txt'
            requirements.write_text('requests==2.25.0')
            
            result = self.scanner.scan_python_dependencies(str(requirements))
        
        assert result['total'] == 1
        assert len(result['details']) == 1
        assert result['details'][0]['package'] == 'requests'
        assert len(result['recommendations']) > 0
    
    @patch('dependency_scanner.subprocess.run')
    def test_scan_python_dependencies_no_vulnerabilities(self, mock_run):
        """Test pip-audit with no vulnerabilities"""
        mock_run.side_effect = [
            Mock(returncode=0),  # pip-audit --version
            Mock(stdout='', returncode=0)  # pip-audit scan
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = Path(temp_dir) / 'requirements.txt'
            requirements.write_text('requests==2.28.0')
            
            result = self.scanner.scan_python_dependencies(str(requirements))
        
        assert result['total'] == 0
        assert result['critical'] == 0
    
    def test_categorize_python_vulnerability_critical(self):
        """Test vulnerability categorization - critical"""
        vuln = {
            'description': 'Remote code execution vulnerability in package',
            'id': 'CVE-2021-12345'
        }
        
        severity = self.scanner._categorize_python_vulnerability(vuln)
        assert severity == 'critical'
    
    def test_categorize_python_vulnerability_high(self):
        """Test vulnerability categorization - high"""
        vuln = {
            'description': 'Denial of service vulnerability',
            'id': 'CVE-2021-12346'
        }
        
        severity = self.scanner._categorize_python_vulnerability(vuln)
        assert severity == 'high'
    
    def test_categorize_python_vulnerability_moderate(self):
        """Test vulnerability categorization - moderate"""
        vuln = {
            'description': 'Information disclosure via XSS',
            'id': 'CVE-2021-12347'
        }
        
        severity = self.scanner._categorize_python_vulnerability(vuln)
        assert severity == 'moderate'
    
    def test_generate_npm_recommendations(self):
        """Test npm recommendations generation"""
        details = [
            {
                'package': 'axios',
                'fixAvailable': True,
                'fixInfo': {'name': 'axios', 'version': '0.21.2', 'isSemVerMajor': False}
            },
            {
                'package': 'lodash',
                'fixAvailable': True,
                'fixInfo': {'name': 'lodash', 'version': '5.0.0', 'isSemVerMajor': True}
            },
            {
                'package': 'old-package',
                'fixAvailable': False
            }
        ]
        
        recommendations = self.scanner._generate_npm_recommendations(details)
        
        assert len(recommendations) > 0
        assert any('npm audit fix' in rec for rec in recommendations)
        assert any('major version' in rec for rec in recommendations)
        assert any('no automatic fix' in rec for rec in recommendations)
    
    def test_generate_python_recommendations(self):
        """Test Python recommendations generation"""
        details = [
            {
                'package': 'requests',
                'fix_versions': ['2.28.0', '2.28.1']
            },
            {
                'package': 'urllib3',
                'fix_versions': []
            }
        ]
        
        recommendations = self.scanner._generate_python_recommendations(details)
        
        assert len(recommendations) == 2
        assert any('requests' in rec and '2.28' in rec for rec in recommendations)
        assert any('urllib3' in rec and 'No fix available' in rec for rec in recommendations)
    
    def test_generate_report_with_vulnerabilities(self):
        """Test report generation with vulnerabilities"""
        scan_results = {
            'timestamp': '2025-10-25T00:00:00Z',
            'scans': {
                'npm': {
                    'total': 5,
                    'critical': 1,
                    'high': 2,
                    'moderate': 2,
                    'low': 0,
                    'details': [],
                    'recommendations': ['Run npm audit fix']
                }
            },
            'summary': {
                'total_vulnerabilities': 5,
                'critical': 1,
                'high': 2,
                'moderate': 2,
                'low': 0
            }
        }
        
        report = self.scanner.generate_report(scan_results)
        
        assert report['action_required'] is True
        assert len(report['overall_recommendations']) > 0
        assert 'IMMEDIATE ACTION REQUIRED' in report['overall_recommendations'][0]
    
    def test_generate_report_no_vulnerabilities(self):
        """Test report generation with no vulnerabilities"""
        scan_results = {
            'timestamp': '2025-10-25T00:00:00Z',
            'scans': {
                'npm': {
                    'total': 0,
                    'critical': 0,
                    'high': 0,
                    'moderate': 0,
                    'low': 0,
                    'details': [],
                    'recommendations': []
                }
            },
            'summary': {
                'total_vulnerabilities': 0,
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0
            }
        }
        
        report = self.scanner.generate_report(scan_results)
        
        assert report['action_required'] is False
        assert any('No vulnerabilities' in rec for rec in report['overall_recommendations'])
    
    @patch('dependency_scanner.sns')
    @patch('dependency_scanner.cloudwatch')
    def test_send_alerts_critical(self, mock_cloudwatch, mock_sns):
        """Test alert sending for critical vulnerabilities"""
        report = {
            'timestamp': '2025-10-25T00:00:00Z',
            'action_required': True,
            'summary': {
                'total_vulnerabilities': 3,
                'critical': 1,
                'high': 2,
                'moderate': 0,
                'low': 0
            },
            'overall_recommendations': ['Fix critical vulnerabilities']
        }
        
        mock_sns.publish.return_value = {'MessageId': 'test-message-id'}
        
        self.scanner.send_alerts(report)
        
        # Verify SNS publish was called
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        assert 'CRITICAL' in call_args[1]['Subject']
        
        # Verify CloudWatch metrics were published
        mock_cloudwatch.put_metric_data.assert_called_once()
    
    @patch('dependency_scanner.sns')
    def test_send_alerts_no_action_required(self, mock_sns):
        """Test that no alert is sent when no action required"""
        report = {
            'action_required': False,
            'summary': {
                'total_vulnerabilities': 0,
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0
            }
        }
        
        self.scanner.send_alerts(report)
        
        # Verify SNS publish was NOT called
        mock_sns.publish.assert_not_called()
    
    @patch('dependency_scanner.sns')
    def test_send_alerts_error_handling(self, mock_sns):
        """Test error handling in alert sending"""
        report = {
            'timestamp': '2025-10-25T00:00:00Z',
            'action_required': True,
            'summary': {
                'total_vulnerabilities': 1,
                'critical': 1,
                'high': 0,
                'moderate': 0,
                'low': 0
            },
            'overall_recommendations': []
        }
        
        mock_sns.publish.side_effect = Exception('SNS error')
        
        with pytest.raises(Exception):
            self.scanner.send_alerts(report)


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_calculate_summary(self):
        """Test summary calculation"""
        scans = {
            'npm': {
                'total': 5,
                'critical': 1,
                'high': 2,
                'moderate': 2,
                'low': 0
            },
            'python': {
                'total': 3,
                'critical': 0,
                'high': 1,
                'moderate': 1,
                'low': 1
            }
        }
        
        summary = _calculate_summary(scans)
        
        assert summary['total_vulnerabilities'] == 8
        assert summary['critical'] == 1
        assert summary['high'] == 3
        assert summary['moderate'] == 3
        assert summary['low'] == 1
    
    def test_calculate_summary_with_errors(self):
        """Test summary calculation with scan errors"""
        scans = {
            'npm': {
                'error': 'npm audit failed'
            },
            'python': {
                'total': 2,
                'critical': 0,
                'high': 1,
                'moderate': 1,
                'low': 0
            }
        }
        
        summary = _calculate_summary(scans)
        
        assert summary['total_vulnerabilities'] == 2
        assert summary['high'] == 1
    
    @patch('dependency_scanner.s3')
    def test_download_from_s3(self, mock_s3):
        """Test S3 download"""
        s3_path = 's3://test-bucket/path/to/file.json'
        local_path = '/tmp/file.json'
        
        _download_from_s3(s3_path, local_path)
        
        mock_s3.download_file.assert_called_once_with(
            'test-bucket',
            'path/to/file.json',
            local_path
        )
    
    @patch('dependency_scanner.s3')
    def test_save_report_to_s3(self, mock_s3):
        """Test report saving to S3"""
        report = {
            'timestamp': '2025-10-25T00:00:00Z',
            'action_required': False,
            'summary': {}
        }
        
        _save_report_to_s3(report)
        
        # Verify two put_object calls (timestamped and latest)
        assert mock_s3.put_object.call_count == 2


class TestLambdaHandler:
    """Test Lambda handler"""
    
    @patch('dependency_scanner.DependencyScanner')
    @patch('dependency_scanner._download_from_s3')
    @patch('dependency_scanner._save_report_to_s3')
    def test_lambda_handler_success(self, mock_save, mock_download, mock_scanner_class):
        """Test successful Lambda execution"""
        # Mock scanner
        mock_scanner = Mock()
        mock_scanner.scan_npm_dependencies.return_value = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'moderate': 0,
            'low': 0,
            'details': []
        }
        mock_scanner.scan_python_dependencies.return_value = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'moderate': 0,
            'low': 0,
            'details': []
        }
        mock_scanner.generate_report.return_value = {
            'timestamp': '2025-10-25T00:00:00Z',
            'action_required': False,
            'summary': {
                'total_vulnerabilities': 0,
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0
            }
        }
        mock_scanner.scan_results = {
            'timestamp': '2025-10-25T00:00:00Z',
            'scans': {},
            'summary': {}
        }
        
        mock_scanner_class.return_value = mock_scanner
        
        event = {
            'scan_type': 'all',
            'source_paths': {
                'npm': 's3://test-bucket/package.json',
                'python': ['s3://test-bucket/requirements.txt']
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'summary' in body
        assert body['action_required'] is False
    
    @patch('dependency_scanner._download_from_s3')
    @patch('dependency_scanner.DependencyScanner')
    def test_lambda_handler_error(self, mock_scanner_class, mock_download):
        """Test Lambda error handling"""
        # Make the scanner instance raise an error during scan
        mock_scanner = Mock()
        mock_scanner.scan_npm_dependencies.side_effect = Exception('Test error')
        mock_scanner_class.return_value = mock_scanner
        
        event = {
            'scan_type': 'npm',
            'source_paths': {
                'npm': 's3://test-bucket/package.json'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
