#!/usr/bin/env python3
"""
Simple Backend Services Integration Validation
A lightweight validation script for checkpoint 9 that checks service implementations
without complex imports or dependencies.
"""

import os
import json
import ast
import re
from datetime import datetime
from pathlib import Path


class SimpleBackendValidator:
    """
    Simple validator for backend services integration
    """
    
    def __init__(self):
        self.validation_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.results = {
            'validation_id': self.validation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'checkpoint': 'Backend Services Integration Validation (Simple)',
            'status': 'running',
            'services': {},
            'integration_points': {},
            'summary': {}
        }
    
    def validate_service_implementation(self, service_name, service_path):
        """
        Validate a service implementation by analyzing the code
        """
        print(f"🔍 Validating {service_name}...")
        
        if not os.path.exists(service_path):
            return {
                'exists': False,
                'error': f"Service file not found: {service_path}"
            }
        
        try:
            with open(service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to analyze the code
            tree = ast.parse(content)
            
            # Find classes and methods
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        'name': node.name,
                        'methods': methods,
                        'method_count': len(methods)
                    })
                elif isinstance(node, ast.FunctionDef) and node.name == 'lambda_handler':
                    functions.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module)
            
            # Check for key patterns
            has_error_handling = 'try:' in content and 'except' in content
            has_logging = any('logger' in imp for imp in imports) or 'logger' in content
            has_audit_logging = 'audit_logger' in content or 'audit' in content.lower()
            has_lambda_handler = 'lambda_handler' in content
            has_boto3 = 'boto3' in content
            has_dynamodb = 'dynamodb' in content.lower()
            
            # Check for service-specific patterns
            service_patterns = {
                'rbac_service': ['RBAC', 'permission', 'authorize', 'role'],
                'inventory_management': ['inventory', 'stock', 'reorder', 'forecast'],
                'procurement_service': ['purchase', 'order', 'approval', 'supplier'],
                'workflow_service': ['workflow', 'state', 'transition', 'escalate'],
                'budget_service': ['budget', 'allocation', 'utilization', 'enforce'],
                'audit_service': ['audit', 'log', 'integrity', 'tamper']
            }
            
            pattern_matches = 0
            if service_name in service_patterns:
                for pattern in service_patterns[service_name]:
                    if pattern.lower() in content.lower():
                        pattern_matches += 1
            
            validation_result = {
                'exists': True,
                'file_size': len(content),
                'line_count': len(content.split('\n')),
                'classes': classes,
                'class_count': len(classes),
                'functions': functions,
                'has_lambda_handler': has_lambda_handler,
                'has_error_handling': has_error_handling,
                'has_logging': has_logging,
                'has_audit_logging': has_audit_logging,
                'has_boto3': has_boto3,
                'has_dynamodb': has_dynamodb,
                'pattern_matches': pattern_matches,
                'total_patterns': len(service_patterns.get(service_name, [])),
                'imports': imports[:10],  # First 10 imports
                'quality_score': self._calculate_quality_score(
                    has_error_handling, has_logging, has_audit_logging,
                    has_lambda_handler, pattern_matches, len(service_patterns.get(service_name, []))
                )
            }
            
            print(f"  ✅ {service_name} - Quality Score: {validation_result['quality_score']:.1f}/10")
            return validation_result
            
        except Exception as e:
            print(f"  ❌ {service_name} - Error: {e}")
            return {
                'exists': True,
                'error': str(e),
                'quality_score': 0
            }
    
    def _calculate_quality_score(self, has_error_handling, has_logging, has_audit_logging,
                               has_lambda_handler, pattern_matches, total_patterns):
        """
        Calculate a quality score for the service implementation
        """
        score = 0
        
        # Basic requirements (6 points)
        if has_lambda_handler:
            score += 2
        if has_error_handling:
            score += 2
        if has_logging:
            score += 1
        if has_audit_logging:
            score += 1
        
        # Service-specific patterns (4 points)
        if total_patterns > 0:
            pattern_score = (pattern_matches / total_patterns) * 4
            score += pattern_score
        
        return min(score, 10)  # Cap at 10
    
    def validate_integration_points(self):
        """
        Validate integration points between services
        """
        print("🔗 Validating integration points...")
        
        integration_checks = {
            'rbac_integration': {
                'description': 'RBAC service integration across all services',
                'files_to_check': [
                    'lambda/inventory_management/handler.py',
                    'lambda/procurement_service/handler.py',
                    'lambda/workflow_service/handler.py',
                    'lambda/budget_service/handler.py'
                ],
                'patterns': ['rbac', 'permission', 'authorize', 'validate_user']
            },
            'audit_integration': {
                'description': 'Audit logging integration across all services',
                'files_to_check': [
                    'lambda/inventory_management/handler.py',
                    'lambda/procurement_service/handler.py',
                    'lambda/workflow_service/handler.py',
                    'lambda/budget_service/handler.py'
                ],
                'patterns': ['audit_logger', 'log_user_action', 'log_data', 'audit']
            },
            'workflow_integration': {
                'description': 'Workflow service integration with procurement',
                'files_to_check': [
                    'lambda/procurement_service/handler.py'
                ],
                'patterns': ['workflow', 'state_machine', 'transition', 'approval']
            },
            'budget_integration': {
                'description': 'Budget service integration with procurement',
                'files_to_check': [
                    'lambda/procurement_service/handler.py'
                ],
                'patterns': ['budget', 'validate_budget', 'reserve_budget', 'allocation']
            }
        }
        
        for integration_name, integration_config in integration_checks.items():
            print(f"  🔍 Checking {integration_config['description']}...")
            
            integration_result = {
                'description': integration_config['description'],
                'files_checked': [],
                'pattern_matches': {},
                'total_matches': 0,
                'integration_score': 0
            }
            
            for file_path in integration_config['files_to_check']:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                        
                        file_matches = 0
                        for pattern in integration_config['patterns']:
                            if pattern.lower() in content:
                                file_matches += 1
                        
                        integration_result['files_checked'].append(file_path)
                        integration_result['pattern_matches'][file_path] = file_matches
                        integration_result['total_matches'] += file_matches
                        
                    except Exception as e:
                        integration_result['pattern_matches'][file_path] = f"Error: {e}"
            
            # Calculate integration score
            max_possible_matches = len(integration_config['files_to_check']) * len(integration_config['patterns'])
            if max_possible_matches > 0:
                integration_result['integration_score'] = (integration_result['total_matches'] / max_possible_matches) * 10
            
            self.results['integration_points'][integration_name] = integration_result
            
            if integration_result['integration_score'] >= 5:
                print(f"    ✅ {integration_name} - Score: {integration_result['integration_score']:.1f}/10")
            else:
                print(f"    ⚠️  {integration_name} - Score: {integration_result['integration_score']:.1f}/10")
    
    def validate_property_based_tests(self):
        """
        Check for property-based test implementations
        """
        print("🧪 Checking property-based tests...")
        
        pbt_files = [
            'tests/unit/lambda/test_rbac_authorization_properties.py',
            'tests/unit/lambda/test_inventory_operations_properties.py',
            'tests/unit/lambda/test_procurement_operations_properties.py',
            'tests/unit/lambda/test_workflow_management_properties.py',
            'tests/unit/lambda/test_budget_enforcement_properties.py',
            'tests/unit/lambda/test_audit_trail_completeness_properties.py'
        ]
        
        pbt_results = {
            'total_expected': len(pbt_files),
            'existing_files': [],
            'missing_files': [],
            'test_analysis': {}
        }
        
        for pbt_file in pbt_files:
            if os.path.exists(pbt_file):
                pbt_results['existing_files'].append(pbt_file)
                
                # Analyze the test file
                try:
                    with open(pbt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for property-based testing patterns
                    has_hypothesis = 'hypothesis' in content.lower()
                    has_fast_check = 'fast-check' in content.lower() or 'fastcheck' in content.lower()
                    has_property_decorator = '@given' in content or '@property' in content
                    test_count = content.count('def test_')
                    property_count = content.count('Property') + content.count('property')
                    
                    pbt_results['test_analysis'][pbt_file] = {
                        'has_hypothesis': has_hypothesis,
                        'has_fast_check': has_fast_check,
                        'has_property_decorator': has_property_decorator,
                        'test_count': test_count,
                        'property_count': property_count,
                        'file_size': len(content)
                    }
                    
                    print(f"  ✅ {os.path.basename(pbt_file)} - {test_count} tests, {property_count} properties")
                    
                except Exception as e:
                    pbt_results['test_analysis'][pbt_file] = {'error': str(e)}
                    print(f"  ❌ {os.path.basename(pbt_file)} - Error: {e}")
            else:
                pbt_results['missing_files'].append(pbt_file)
                print(f"  ❌ {os.path.basename(pbt_file)} - Missing")
        
        self.results['property_based_tests'] = pbt_results
        return len(pbt_results['existing_files']) > 0
    
    def generate_summary(self):
        """
        Generate validation summary
        """
        print("📊 Generating summary...")
        
        # Calculate service scores
        service_scores = []
        for service_name, service_result in self.results['services'].items():
            if 'quality_score' in service_result:
                service_scores.append(service_result['quality_score'])
        
        avg_service_score = sum(service_scores) / len(service_scores) if service_scores else 0
        
        # Calculate integration scores
        integration_scores = []
        for integration_name, integration_result in self.results['integration_points'].items():
            if 'integration_score' in integration_result:
                integration_scores.append(integration_result['integration_score'])
        
        avg_integration_score = sum(integration_scores) / len(integration_scores) if integration_scores else 0
        
        # Calculate PBT score
        pbt_results = self.results.get('property_based_tests', {})
        pbt_score = 0
        if pbt_results.get('total_expected', 0) > 0:
            pbt_score = (len(pbt_results.get('existing_files', [])) / pbt_results['total_expected']) * 10
        
        # Overall score
        overall_score = (avg_service_score * 0.5 + avg_integration_score * 0.3 + pbt_score * 0.2)
        
        self.results['summary'] = {
            'avg_service_score': avg_service_score,
            'avg_integration_score': avg_integration_score,
            'pbt_score': pbt_score,
            'overall_score': overall_score,
            'status': 'passed' if overall_score >= 7.0 else 'needs_improvement',
            'total_services': len(self.results['services']),
            'services_with_errors': len([s for s in self.results['services'].values() if 'error' in s]),
            'integration_points_checked': len(self.results['integration_points']),
            'pbt_files_found': len(pbt_results.get('existing_files', [])),
            'pbt_files_missing': len(pbt_results.get('missing_files', []))
        }
        
        self.results['status'] = 'completed'
    
    def print_results(self):
        """
        Print validation results
        """
        summary = self.results['summary']
        
        print("\n" + "=" * 80)
        print("BACKEND SERVICES INTEGRATION VALIDATION RESULTS")
        print("=" * 80)
        
        if summary['status'] == 'passed':
            print("✅ VALIDATION PASSED")
        else:
            print("⚠️  VALIDATION NEEDS IMPROVEMENT")
        
        print(f"\nOverall Score: {summary['overall_score']:.1f}/10")
        print(f"Status: {summary['status'].upper()}")
        
        print(f"\nService Implementation:")
        print(f"  Average Service Score: {summary['avg_service_score']:.1f}/10")
        print(f"  Total Services: {summary['total_services']}")
        print(f"  Services with Errors: {summary['services_with_errors']}")
        
        print(f"\nIntegration Points:")
        print(f"  Average Integration Score: {summary['avg_integration_score']:.1f}/10")
        print(f"  Integration Points Checked: {summary['integration_points_checked']}")
        
        print(f"\nProperty-Based Tests:")
        print(f"  PBT Score: {summary['pbt_score']:.1f}/10")
        print(f"  PBT Files Found: {summary['pbt_files_found']}")
        print(f"  PBT Files Missing: {summary['pbt_files_missing']}")
        
        # Detailed service results
        print(f"\nDetailed Service Results:")
        for service_name, service_result in self.results['services'].items():
            if 'quality_score' in service_result:
                status = "✅" if service_result['quality_score'] >= 7 else "⚠️"
                print(f"  {status} {service_name}: {service_result['quality_score']:.1f}/10")
                if 'error' in service_result:
                    print(f"    Error: {service_result['error']}")
            else:
                print(f"  ❌ {service_name}: Not found or error")
        
        # Integration results
        print(f"\nIntegration Point Results:")
        for integration_name, integration_result in self.results['integration_points'].items():
            score = integration_result.get('integration_score', 0)
            status = "✅" if score >= 5 else "⚠️"
            print(f"  {status} {integration_name}: {score:.1f}/10")
        
        print(f"\nValidation ID: {self.validation_id}")
        print(f"Timestamp: {self.results['timestamp']}")
        print("=" * 80)
    
    def save_report(self):
        """
        Save validation report to file
        """
        report_file = f"backend_validation_report_{self.validation_id}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved to: {report_file}")
        return report_file
    
    def run_validation(self):
        """
        Run complete validation
        """
        print("🚀 Starting Simple Backend Services Integration Validation")
        print("=" * 80)
        
        # Define services to validate
        services = {
            'rbac_service': 'lambda/rbac_service/handler.py',
            'inventory_management': 'lambda/inventory_management/handler.py',
            'procurement_service': 'lambda/procurement_service/handler.py',
            'workflow_service': 'lambda/workflow_service/handler.py',
            'budget_service': 'lambda/budget_service/handler.py',
            'audit_service': 'lambda/audit_service/handler.py'
        }
        
        # Validate each service
        for service_name, service_path in services.items():
            self.results['services'][service_name] = self.validate_service_implementation(
                service_name, service_path
            )
        
        # Validate integration points
        self.validate_integration_points()
        
        # Check property-based tests
        self.validate_property_based_tests()
        
        # Generate summary
        self.generate_summary()
        
        # Print results
        self.print_results()
        
        # Save report
        self.save_report()
        
        return self.results


def main():
    """
    Main function
    """
    validator = SimpleBackendValidator()
    results = validator.run_validation()
    
    # Exit with appropriate code
    if results['summary']['status'] == 'passed':
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)