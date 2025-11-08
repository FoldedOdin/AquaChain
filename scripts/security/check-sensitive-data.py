#!/usr/bin/env python3
"""
Security Scanner - Detect sensitive data in codebase
Scans for AWS account IDs, real email addresses, API keys, etc.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Patterns to detect
PATTERNS = {
    'aws_account_id': r'\b\d{12}\b',
    'real_email': r'[a-zA-Z0-9._%+-]+@(?!example\.com|test\.com|localhost|yourdomain\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'cognito_pool_id': r'[a-z]{2}-[a-z]+-\d_[A-Za-z0-9]{9}',
    'kms_key_id': r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
    'api_key_pattern': r'(api[_-]?key|secret[_-]?key|access[_-]?key)\s*[=:]\s*[\'"][^\'"]{20,}[\'"]',
    'private_key': r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
}

# Files/directories to skip
SKIP_PATTERNS = [
    '.git',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    'cdk.out',
    'dist',
    'build',
    '.pytest_cache',
    '.kiro',
]

# Known safe values (test/example data)
SAFE_VALUES = {
    '123456789012',  # Example AWS account
    '987654321098',  # Example AWS account
    '451282441545',  # AWS SAR application
}

class SensitiveDataScanner:
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
        self.findings: List[Dict] = []
    
    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped"""
        path_str = str(path)
        return any(skip in path_str for skip in SKIP_PATTERNS)
    
    def scan_file(self, file_path: Path):
        """Scan a single file for sensitive data"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern_name, pattern in PATTERNS.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    value = match.group(0)
                    
                    # Skip safe/example values
                    if value in SAFE_VALUES:
                        continue
                    
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    self.findings.append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'type': pattern_name,
                        'value': value,
                    })
        except Exception as e:
            pass  # Skip files that can't be read
    
    def scan(self):
        """Scan entire directory"""
        for root, dirs, files in os.walk(self.root_dir):
            # Remove skip directories from traversal
            dirs[:] = [d for d in dirs if not self.should_skip(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip binary files and specific extensions
                if file_path.suffix in ['.pyc', '.so', '.dll', '.exe', '.zip', '.tar', '.gz']:
                    continue
                
                if not self.should_skip(file_path):
                    self.scan_file(file_path)
    
    def report(self):
        """Generate report of findings"""
        if not self.findings:
            print("✅ No sensitive data detected!")
            return
        
        print(f"⚠️  Found {len(self.findings)} potential sensitive data items:\n")
        
        # Group by type
        by_type = {}
        for finding in self.findings:
            type_name = finding['type']
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(finding)
        
        for type_name, items in by_type.items():
            print(f"\n{'='*60}")
            print(f"{type_name.upper().replace('_', ' ')} ({len(items)} found)")
            print('='*60)
            
            # Group by file
            by_file = {}
            for item in items:
                file = item['file']
                if file not in by_file:
                    by_file[file] = []
                by_file[file].append(item)
            
            for file, file_items in sorted(by_file.items()):
                print(f"\n📄 {file}")
                for item in file_items:
                    print(f"   Line {item['line']}: {item['value']}")
        
        print(f"\n{'='*60}")
        print("\n⚠️  RECOMMENDATIONS:")
        print("1. Review each finding to determine if it's sensitive")
        print("2. Replace real values with placeholders (e.g., 123456789012)")
        print("3. Move sensitive config to .env files (already in .gitignore)")
        print("4. Use AWS Secrets Manager for production secrets")
        print("5. Never commit real credentials, keys, or account IDs")


if __name__ == '__main__':
    print("🔍 Scanning codebase for sensitive data...\n")
    
    scanner = SensitiveDataScanner()
    scanner.scan()
    scanner.report()
