#!/usr/bin/env python3
"""
Software Bill of Materials (SBOM) Generator
Generate comprehensive SBOM in SPDX format
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import hashlib

# Configuration
PROJECT_NAME = "AquaChain"
PROJECT_VERSION = "1.0.0"
ORGANIZATION = "AquaChain Team"


class SBOMGenerator:
    """Generate Software Bill of Materials"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.sbom = {
            'spdxVersion': 'SPDX-2.3',
            'dataLicense': 'CC0-1.0',
            'SPDXID': 'SPDXRef-DOCUMENT',
            'name': f'{PROJECT_NAME}-SBOM',
            'documentNamespace': f'https://aquachain.io/sbom/{datetime.utcnow().isoformat()}',
            'creationInfo': {
                'created': datetime.utcnow().isoformat() + 'Z',
                'creators': [f'Organization: {ORGANIZATION}', 'Tool: AquaChain-SBOM-Generator'],
                'licenseListVersion': '3.20'
            },
            'packages': [],
            'relationships': []
        }
        
        self.package_id_counter = 1
    
    def collect_npm_dependencies(self) -> List[Dict[str, Any]]:
        """Collect npm dependencies"""
        print("Collecting npm dependencies...")
        
        frontend_dir = self.project_root / 'frontend'
        
        if not (frontend_dir / 'package.json').exists():
            return []
        
        try:
            # Get dependency tree
            result = subprocess.run(
                ['npm', 'list', '--json', '--all'],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            dep_tree = json.loads(result.stdout)
            packages = []
            
            # Parse dependencies
            self._parse_npm_tree(dep_tree.get('dependencies', {}), packages)
            
            return packages
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error collecting npm dependencies: {e}")
            return []
    
    def _parse_npm_tree(self, deps: Dict, packages: List, parent: str = None):
        """Recursively parse npm dependency tree"""
        for name, info in deps.items():
            version = info.get('version', 'unknown')
            
            package = {
                'SPDXID': f'SPDXRef-Package-{self.package_id_counter}',
                'name': name,
                'versionInfo': version,
                'supplier': 'Organization: npm',
                'downloadLocation': f'https://registry.npmjs.org/{name}/-/{name}-{version}.tgz',
                'filesAnalyzed': False,
                'licenseConcluded': info.get('license', 'NOASSERTION'),
                'licenseDeclared': info.get('license', 'NOASSERTION'),
                'copyrightText': 'NOASSERTION'
            }
            
            packages.append(package)
            self.package_id_counter += 1
            
            # Parse nested dependencies
            if 'dependencies' in info:
                self._parse_npm_tree(info['dependencies'], packages, name)
    
    def collect_python_dependencies(self) -> List[Dict[str, Any]]:
        """Collect Python dependencies"""
        print("Collecting Python dependencies...")
        
        try:
            # Get installed packages
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            pip_packages = json.loads(result.stdout)
            packages = []
            
            for pkg in pip_packages:
                name = pkg['name']
                version = pkg['version']
                
                # Get package metadata
                try:
                    show_result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'show', name],
                        capture_output=True,
                        text=True
                    )
                    
                    metadata = {}
                    for line in show_result.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                    
                    license_info = metadata.get('License', 'NOASSERTION')
                    
                except subprocess.CalledProcessError:
                    license_info = 'NOASSERTION'
                
                package = {
                    'SPDXID': f'SPDXRef-Package-{self.package_id_counter}',
                    'name': name,
                    'versionInfo': version,
                    'supplier': 'Organization: PyPI',
                    'downloadLocation': f'https://pypi.org/project/{name}/{version}/',
                    'filesAnalyzed': False,
                    'licenseConcluded': license_info,
                    'licenseDeclared': license_info,
                    'copyrightText': 'NOASSERTION'
                }
                
                packages.append(package)
                self.package_id_counter += 1
            
            return packages
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error collecting Python dependencies: {e}")
            return []
    
    def generate_sbom(self) -> Dict[str, Any]:
        """Generate complete SBOM"""
        print("Generating SBOM...")
        
        # Add root package
        root_package = {
            'SPDXID': 'SPDXRef-Package-Root',
            'name': PROJECT_NAME,
            'versionInfo': PROJECT_VERSION,
            'supplier': f'Organization: {ORGANIZATION}',
            'downloadLocation': 'NOASSERTION',
            'filesAnalyzed': False,
            'licenseConcluded': 'NOASSERTION',
            'licenseDeclared': 'NOASSERTION',
            'copyrightText': f'Copyright {datetime.utcnow().year} {ORGANIZATION}'
        }
        
        self.sbom['packages'].append(root_package)
        
        # Collect dependencies
        npm_packages = self.collect_npm_dependencies()
        python_packages = self.collect_python_dependencies()
        
        # Add all packages
        self.sbom['packages'].extend(npm_packages)
        self.sbom['packages'].extend(python_packages)
        
        # Add relationships
        for package in npm_packages + python_packages:
            self.sbom['relationships'].append({
                'spdxElementId': 'SPDXRef-Package-Root',
                'relationshipType': 'DEPENDS_ON',
                'relatedSpdxElement': package['SPDXID']
            })
        
        return self.sbom
    
    def save_sbom(self, output_file: str = 'SBOM.json'):
        """Save SBOM to file"""
        output_path = self.project_root / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.sbom, f, indent=2)
        
        print(f"SBOM saved to {output_path}")
        
        # Generate checksum
        with open(output_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        checksum_file = output_path.with_suffix('.json.sha256')
        with open(checksum_file, 'w') as f:
            f.write(f"{checksum}  {output_file}\n")
        
        print(f"Checksum saved to {checksum_file}")
    
    def scan_vulnerabilities(self):
        """Scan SBOM for vulnerabilities using Grype"""
        print("\nScanning SBOM for vulnerabilities...")
        
        sbom_file = self.project_root / 'SBOM.json'
        
        try:
            # Check if grype is installed
            subprocess.run(['grype', 'version'], capture_output=True, check=True)
            
            # Run grype scan
            result = subprocess.run(
                ['grype', f'sbom:{sbom_file}', '-o', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                
                # Save vulnerability report
                vuln_file = self.project_root / 'SBOM-vulnerabilities.json'
                with open(vuln_file, 'w') as f:
                    json.dump(vulnerabilities, f, indent=2)
                
                print(f"Vulnerability report saved to {vuln_file}")
                
                # Print summary
                matches = vulnerabilities.get('matches', [])
                if matches:
                    print(f"\nFound {len(matches)} vulnerabilities:")
                    
                    severity_counts = {}
                    for match in matches:
                        severity = match.get('vulnerability', {}).get('severity', 'unknown')
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    for severity, count in sorted(severity_counts.items()):
                        print(f"  {severity}: {count}")
                else:
                    print("No vulnerabilities found!")
            
        except FileNotFoundError:
            print("Grype not installed. Install with: curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin")
        except subprocess.CalledProcessError as e:
            print(f"Error running grype: {e}")
        except json.JSONDecodeError as e:
            print(f"Error parsing grype output: {e}")


def main():
    """Main entry point"""
    generator = SBOMGenerator()
    
    # Generate SBOM
    sbom = generator.generate_sbom()
    
    # Print summary
    print("\n" + "="*60)
    print("SBOM GENERATION SUMMARY")
    print("="*60)
    print(f"Project: {PROJECT_NAME} v{PROJECT_VERSION}")
    print(f"Total Packages: {len(sbom['packages'])}")
    print(f"Total Relationships: {len(sbom['relationships'])}")
    print("="*60)
    
    # Save SBOM
    generator.save_sbom()
    
    # Scan for vulnerabilities
    generator.scan_vulnerabilities()
    
    print("\nSBOM generation complete!")


if __name__ == '__main__':
    main()
