#!/usr/bin/env python3
"""
Software Bill of Materials (SBOM) Generator
Generate comprehensive SBOM in SPDX format using Syft
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import shutil

# Configuration
PROJECT_NAME = "AquaChain"
PROJECT_VERSION = "1.0.0"
ORGANIZATION = "AquaChain Team"


class SBOMGenerator:
    """Generate Software Bill of Materials using Syft"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.sbom_dir = self.project_root / 'sbom-artifacts'
        self.sbom_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        
    def check_syft_installed(self) -> bool:
        """Check if Syft is installed"""
        return shutil.which('syft') is not None
    
    def install_syft_instructions(self):
        """Print Syft installation instructions"""
        print("\n" + "="*60)
        print("Syft is not installed!")
        print("="*60)
        print("\nInstallation instructions:")
        print("\nLinux/macOS:")
        print("  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin")
        print("\nWindows (PowerShell):")
        print("  iwr -useb https://raw.githubusercontent.com/anchore/syft/main/install.sh | iex")
        print("\nOr using package managers:")
        print("  brew install syft")
        print("  choco install syft")
        print("\nFor more options, visit: https://github.com/anchore/syft#installation")
        print("="*60 + "\n")
    
    def generate_sbom_with_syft(self, component: str, path: Path) -> Optional[Path]:
        """Generate SBOM for a component using Syft"""
        print(f"\nGenerating SBOM for {component}...")
        
        output_file = self.sbom_dir / f'sbom-{component}-{self.timestamp}.json'
        
        try:
            # Run Syft to generate SBOM in SPDX JSON format
            result = subprocess.run(
                [
                    'syft',
                    f'dir:{path}',
                    '-o', 'spdx-json',
                    '--file', str(output_file)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✓ SBOM generated: {output_file}")
            
            # Generate checksum
            with open(output_file, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            checksum_file = output_file.with_suffix('.json.sha256')
            with open(checksum_file, 'w') as f:
                f.write(f"{checksum}  {output_file.name}\n")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Error generating SBOM for {component}: {e}")
            if e.stderr:
                print(f"  Error details: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"✗ Syft not found. Please install Syft first.")
            return None
    
    def generate_all_sboms(self) -> Dict[str, Optional[Path]]:
        """Generate SBOMs for all components"""
        print("\n" + "="*60)
        print("GENERATING SBOMs WITH SYFT")
        print("="*60)
        
        sboms = {}
        
        # Frontend SBOM
        frontend_dir = self.project_root / 'frontend'
        if frontend_dir.exists():
            sboms['frontend'] = self.generate_sbom_with_syft('frontend', frontend_dir)
        
        # Backend/Lambda SBOM
        lambda_dir = self.project_root / 'lambda'
        if lambda_dir.exists():
            sboms['backend'] = self.generate_sbom_with_syft('backend', lambda_dir)
        
        # Infrastructure SBOM
        infra_dir = self.project_root / 'infrastructure'
        if infra_dir.exists():
            sboms['infrastructure'] = self.generate_sbom_with_syft('infrastructure', infra_dir)
        
        # IoT Firmware SBOM
        iot_dir = self.project_root / 'iot-simulator'
        if iot_dir.exists():
            sboms['iot-firmware'] = self.generate_sbom_with_syft('iot-firmware', iot_dir)
        
        return sboms
    
    def merge_sboms(self, sbom_files: Dict[str, Optional[Path]]) -> Path:
        """Merge multiple SBOMs into a single comprehensive SBOM"""
        print("\nMerging SBOMs...")
        
        merged_sbom = {
            'spdxVersion': 'SPDX-2.3',
            'dataLicense': 'CC0-1.0',
            'SPDXID': 'SPDXRef-DOCUMENT',
            'name': f'{PROJECT_NAME}-Complete-SBOM',
            'documentNamespace': f'https://aquachain.io/sbom/{self.timestamp}',
            'creationInfo': {
                'created': datetime.utcnow().isoformat() + 'Z',
                'creators': [
                    f'Organization: {ORGANIZATION}',
                    'Tool: Syft',
                    'Tool: AquaChain-SBOM-Generator'
                ],
                'licenseListVersion': '3.20'
            },
            'packages': [],
            'relationships': [],
            'files': []
        }
        
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
        merged_sbom['packages'].append(root_package)
        
        # Merge all component SBOMs
        for component, sbom_file in sbom_files.items():
            if sbom_file and sbom_file.exists():
                try:
                    with open(sbom_file, 'r') as f:
                        component_sbom = json.load(f)
                    
                    # Add packages from component SBOM
                    if 'packages' in component_sbom:
                        for package in component_sbom['packages']:
                            # Prefix SPDXID to avoid conflicts
                            package['SPDXID'] = f"SPDXRef-{component}-{package['SPDXID'].replace('SPDXRef-', '')}"
                            merged_sbom['packages'].append(package)
                            
                            # Add relationship to root
                            merged_sbom['relationships'].append({
                                'spdxElementId': 'SPDXRef-Package-Root',
                                'relationshipType': 'CONTAINS',
                                'relatedSpdxElement': package['SPDXID']
                            })
                    
                    # Add relationships from component SBOM
                    if 'relationships' in component_sbom:
                        for rel in component_sbom['relationships']:
                            # Prefix SPDXIDs in relationships
                            rel['spdxElementId'] = f"SPDXRef-{component}-{rel['spdxElementId'].replace('SPDXRef-', '')}"
                            rel['relatedSpdxElement'] = f"SPDXRef-{component}-{rel['relatedSpdxElement'].replace('SPDXRef-', '')}"
                            merged_sbom['relationships'].append(rel)
                    
                    print(f"✓ Merged {component} SBOM")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"✗ Error merging {component} SBOM: {e}")
        
        # Save merged SBOM
        merged_file = self.sbom_dir / f'sbom-complete-{self.timestamp}.json'
        with open(merged_file, 'w') as f:
            json.dump(merged_sbom, f, indent=2)
        
        print(f"✓ Complete SBOM saved: {merged_file}")
        
        # Generate checksum
        with open(merged_file, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        checksum_file = merged_file.with_suffix('.json.sha256')
        with open(checksum_file, 'w') as f:
            f.write(f"{checksum}  {merged_file.name}\n")
        
        return merged_file
    
    def check_grype_installed(self) -> bool:
        """Check if Grype is installed"""
        return shutil.which('grype') is not None
    
    def install_grype_instructions(self):
        """Print Grype installation instructions"""
        print("\n" + "="*60)
        print("Grype is not installed!")
        print("="*60)
        print("\nInstallation instructions:")
        print("\nLinux/macOS:")
        print("  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin")
        print("\nWindows (PowerShell):")
        print("  iwr -useb https://raw.githubusercontent.com/anchore/grype/main/install.sh | iex")
        print("\nOr using package managers:")
        print("  brew install grype")
        print("  choco install grype")
        print("\nFor more options, visit: https://github.com/anchore/grype#installation")
        print("="*60 + "\n")
    
    def scan_vulnerabilities(self, sbom_file: Path) -> Optional[Path]:
        """Scan SBOM for vulnerabilities using Grype"""
        print(f"\nScanning {sbom_file.name} for vulnerabilities...")
        
        vuln_file = sbom_file.with_suffix('.vulnerabilities.json')
        
        try:
            # Run grype scan
            result = subprocess.run(
                ['grype', f'sbom:{sbom_file}', '-o', 'json', '--file', str(vuln_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Load and analyze results
            with open(vuln_file, 'r') as f:
                vulnerabilities = json.load(f)
            
            # Print summary
            matches = vulnerabilities.get('matches', [])
            if matches:
                print(f"✓ Found {len(matches)} vulnerabilities")
                
                severity_counts = {}
                for match in matches:
                    severity = match.get('vulnerability', {}).get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity in ['Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown']:
                    count = severity_counts.get(severity, 0)
                    if count > 0:
                        print(f"  {severity}: {count}")
            else:
                print("✓ No vulnerabilities found!")
            
            return vuln_file
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Error running grype: {e}")
            if e.stderr:
                print(f"  Error details: {e.stderr}")
            return None
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"✗ Error processing vulnerability results: {e}")
            return None
    
    def generate_summary_report(self, sbom_files: Dict[str, Optional[Path]], 
                               vuln_files: Dict[str, Optional[Path]]) -> Path:
        """Generate a summary report of all SBOMs and vulnerabilities"""
        print("\nGenerating summary report...")
        
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'project': PROJECT_NAME,
            'version': PROJECT_VERSION,
            'components': {},
            'total_packages': 0,
            'total_vulnerabilities': 0,
            'vulnerability_summary': {
                'Critical': 0,
                'High': 0,
                'Medium': 0,
                'Low': 0,
                'Negligible': 0,
                'Unknown': 0
            }
        }
        
        # Analyze each component
        for component, sbom_file in sbom_files.items():
            if not sbom_file or not sbom_file.exists():
                continue
            
            component_data = {
                'sbom_file': str(sbom_file),
                'package_count': 0,
                'vulnerabilities': {
                    'Critical': 0,
                    'High': 0,
                    'Medium': 0,
                    'Low': 0,
                    'Negligible': 0,
                    'Unknown': 0
                }
            }
            
            # Count packages
            try:
                with open(sbom_file, 'r') as f:
                    sbom_data = json.load(f)
                    component_data['package_count'] = len(sbom_data.get('packages', []))
                    report['total_packages'] += component_data['package_count']
            except (json.JSONDecodeError, KeyError):
                pass
            
            # Count vulnerabilities
            vuln_file = vuln_files.get(component)
            if vuln_file and vuln_file.exists():
                try:
                    with open(vuln_file, 'r') as f:
                        vuln_data = json.load(f)
                        matches = vuln_data.get('matches', [])
                        
                        for match in matches:
                            severity = match.get('vulnerability', {}).get('severity', 'Unknown')
                            component_data['vulnerabilities'][severity] = \
                                component_data['vulnerabilities'].get(severity, 0) + 1
                            report['vulnerability_summary'][severity] = \
                                report['vulnerability_summary'].get(severity, 0) + 1
                            report['total_vulnerabilities'] += 1
                        
                        component_data['vulnerability_file'] = str(vuln_file)
                except (json.JSONDecodeError, KeyError):
                    pass
            
            report['components'][component] = component_data
        
        # Save report
        report_file = self.sbom_dir / f'sbom-report-{self.timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Summary report saved: {report_file}")
        
        return report_file
    
    def print_summary(self, report_file: Path):
        """Print a human-readable summary"""
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        print("\n" + "="*60)
        print("SBOM GENERATION SUMMARY")
        print("="*60)
        print(f"Project: {report['project']} v{report['version']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Packages: {report['total_packages']}")
        print(f"Total Vulnerabilities: {report['total_vulnerabilities']}")
        print("\nVulnerability Breakdown:")
        for severity in ['Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown']:
            count = report['vulnerability_summary'].get(severity, 0)
            if count > 0:
                print(f"  {severity}: {count}")
        
        print("\nComponents:")
        for component, data in report['components'].items():
            print(f"\n  {component}:")
            print(f"    Packages: {data['package_count']}")
            vuln_count = sum(data['vulnerabilities'].values())
            print(f"    Vulnerabilities: {vuln_count}")
            if vuln_count > 0:
                for severity in ['Critical', 'High', 'Medium', 'Low']:
                    count = data['vulnerabilities'].get(severity, 0)
                    if count > 0:
                        print(f"      {severity}: {count}")
        
        print("="*60)


def main():
    """Main entry point"""
    generator = SBOMGenerator()
    
    # Check if Syft is installed
    if not generator.check_syft_installed():
        generator.install_syft_instructions()
        print("Please install Syft and run this script again.")
        sys.exit(1)
    
    # Generate SBOMs for all components
    sbom_files = generator.generate_all_sboms()
    
    # Merge SBOMs
    if any(sbom_files.values()):
        merged_sbom = generator.merge_sboms(sbom_files)
    else:
        print("\n✗ No SBOMs were generated successfully.")
        sys.exit(1)
    
    # Check if Grype is installed
    if not generator.check_grype_installed():
        generator.install_grype_instructions()
        print("\nSkipping vulnerability scanning. Install Grype to enable scanning.")
        vuln_files = {}
    else:
        # Scan each SBOM for vulnerabilities
        print("\n" + "="*60)
        print("SCANNING FOR VULNERABILITIES")
        print("="*60)
        
        vuln_files = {}
        for component, sbom_file in sbom_files.items():
            if sbom_file:
                vuln_files[component] = generator.scan_vulnerabilities(sbom_file)
        
        # Scan merged SBOM
        vuln_files['complete'] = generator.scan_vulnerabilities(merged_sbom)
    
    # Generate summary report
    report_file = generator.generate_summary_report(sbom_files, vuln_files)
    
    # Print summary
    generator.print_summary(report_file)
    
    print("\n✓ SBOM generation complete!")
    print(f"\nAll artifacts saved to: {generator.sbom_dir}")


if __name__ == '__main__':
    main()
