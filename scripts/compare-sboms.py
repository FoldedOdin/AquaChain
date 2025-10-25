#!/usr/bin/env python3
"""
SBOM Comparison Tool
Compare two SBOMs to track changes in dependencies
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime


class SBOMComparator:
    """Compare two SBOMs and generate a change report"""
    
    def __init__(self, old_sbom_path: str, new_sbom_path: str):
        self.old_sbom_path = Path(old_sbom_path)
        self.new_sbom_path = Path(new_sbom_path)
        
    def load_sbom(self, path: Path) -> Dict:
        """Load SBOM from file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {path}: {e}")
            sys.exit(1)
    
    def extract_packages(self, sbom: Dict) -> Dict[str, Dict]:
        """Extract packages from SBOM"""
        packages = {}
        
        for pkg in sbom.get('packages', []):
            name = pkg.get('name', 'unknown')
            if name == 'unknown' or name.startswith('SPDXRef-'):
                continue
            
            packages[name] = {
                'version': pkg.get('versionInfo', 'unknown'),
                'license': pkg.get('licenseDeclared', 'NOASSERTION'),
                'supplier': pkg.get('supplier', 'NOASSERTION'),
                'spdxid': pkg.get('SPDXID', '')
            }
        
        return packages
    
    def compare_packages(self, old_packages: Dict, new_packages: Dict) -> Dict:
        """Compare two sets of packages"""
        old_names = set(old_packages.keys())
        new_names = set(new_packages.keys())
        
        added = new_names - old_names
        removed = old_names - new_names
        common = old_names & new_names
        
        updated = []
        license_changes = []
        
        for name in common:
            old_pkg = old_packages[name]
            new_pkg = new_packages[name]
            
            if old_pkg['version'] != new_pkg['version']:
                updated.append({
                    'name': name,
                    'old_version': old_pkg['version'],
                    'new_version': new_pkg['version']
                })
            
            if old_pkg['license'] != new_pkg['license']:
                license_changes.append({
                    'name': name,
                    'old_license': old_pkg['license'],
                    'new_license': new_pkg['license']
                })
        
        return {
            'added': sorted(list(added)),
            'removed': sorted(list(removed)),
            'updated': sorted(updated, key=lambda x: x['name']),
            'license_changes': sorted(license_changes, key=lambda x: x['name']),
            'unchanged': len(common) - len(updated) - len(license_changes)
        }
    
    def generate_report(self, comparison: Dict, old_packages: Dict, new_packages: Dict) -> Dict:
        """Generate a comprehensive comparison report"""
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'old_sbom': str(self.old_sbom_path),
            'new_sbom': str(self.new_sbom_path),
            'summary': {
                'total_old': len(old_packages),
                'total_new': len(new_packages),
                'added': len(comparison['added']),
                'removed': len(comparison['removed']),
                'updated': len(comparison['updated']),
                'license_changes': len(comparison['license_changes']),
                'unchanged': comparison['unchanged']
            },
            'changes': comparison
        }
        
        # Add package details for added packages
        report['added_details'] = [
            {
                'name': name,
                'version': new_packages[name]['version'],
                'license': new_packages[name]['license']
            }
            for name in comparison['added']
        ]
        
        # Add package details for removed packages
        report['removed_details'] = [
            {
                'name': name,
                'version': old_packages[name]['version'],
                'license': old_packages[name]['license']
            }
            for name in comparison['removed']
        ]
        
        return report
    
    def print_report(self, report: Dict):
        """Print a human-readable report"""
        print("\n" + "="*60)
        print("SBOM COMPARISON REPORT")
        print("="*60)
        print(f"Old SBOM: {report['old_sbom']}")
        print(f"New SBOM: {report['new_sbom']}")
        print(f"Timestamp: {report['timestamp']}")
        print("\n" + "-"*60)
        print("SUMMARY")
        print("-"*60)
        
        summary = report['summary']
        print(f"Total packages (old): {summary['total_old']}")
        print(f"Total packages (new): {summary['total_new']}")
        print(f"Net change: {summary['total_new'] - summary['total_old']:+d}")
        print()
        print(f"Added:           {summary['added']}")
        print(f"Removed:         {summary['removed']}")
        print(f"Updated:         {summary['updated']}")
        print(f"License changes: {summary['license_changes']}")
        print(f"Unchanged:       {summary['unchanged']}")
        
        # Added packages
        if report['added_details']:
            print("\n" + "-"*60)
            print(f"ADDED PACKAGES ({len(report['added_details'])})")
            print("-"*60)
            for pkg in report['added_details'][:20]:  # Limit to 20
                print(f"  + {pkg['name']}@{pkg['version']} ({pkg['license']})")
            if len(report['added_details']) > 20:
                print(f"  ... and {len(report['added_details']) - 20} more")
        
        # Removed packages
        if report['removed_details']:
            print("\n" + "-"*60)
            print(f"REMOVED PACKAGES ({len(report['removed_details'])})")
            print("-"*60)
            for pkg in report['removed_details'][:20]:
                print(f"  - {pkg['name']}@{pkg['version']} ({pkg['license']})")
            if len(report['removed_details']) > 20:
                print(f"  ... and {len(report['removed_details']) - 20} more")
        
        # Updated packages
        if report['changes']['updated']:
            print("\n" + "-"*60)
            print(f"UPDATED PACKAGES ({len(report['changes']['updated'])})")
            print("-"*60)
            for pkg in report['changes']['updated'][:20]:
                print(f"  ↑ {pkg['name']}: {pkg['old_version']} → {pkg['new_version']}")
            if len(report['changes']['updated']) > 20:
                print(f"  ... and {len(report['changes']['updated']) - 20} more")
        
        # License changes
        if report['changes']['license_changes']:
            print("\n" + "-"*60)
            print(f"LICENSE CHANGES ({len(report['changes']['license_changes'])})")
            print("-"*60)
            for pkg in report['changes']['license_changes']:
                print(f"  ⚖ {pkg['name']}: {pkg['old_license']} → {pkg['new_license']}")
        
        print("\n" + "="*60)
    
    def save_report(self, report: Dict, output_path: str = None):
        """Save report to JSON file"""
        if output_path is None:
            output_path = f"sbom-comparison-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {output_file}")
    
    def compare(self, save_report: bool = True) -> Dict:
        """Perform the comparison"""
        print("Loading SBOMs...")
        old_sbom = self.load_sbom(self.old_sbom_path)
        new_sbom = self.load_sbom(self.new_sbom_path)
        
        print("Extracting packages...")
        old_packages = self.extract_packages(old_sbom)
        new_packages = self.extract_packages(new_sbom)
        
        print("Comparing packages...")
        comparison = self.compare_packages(old_packages, new_packages)
        
        print("Generating report...")
        report = self.generate_report(comparison, old_packages, new_packages)
        
        self.print_report(report)
        
        if save_report:
            self.save_report(report)
        
        return report


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python compare-sboms.py <old_sbom.json> <new_sbom.json> [output.json]")
        print("\nExample:")
        print("  python compare-sboms.py sbom-old.json sbom-new.json")
        print("  python compare-sboms.py sbom-old.json sbom-new.json comparison-report.json")
        sys.exit(1)
    
    old_sbom = sys.argv[1]
    new_sbom = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    comparator = SBOMComparator(old_sbom, new_sbom)
    report = comparator.compare(save_report=True)
    
    if output_file:
        comparator.save_report(report, output_file)
    
    # Exit with error code if there are significant changes
    if report['summary']['removed'] > 0:
        print("\n⚠️  Warning: Packages were removed!")
        sys.exit(2)
    
    if report['summary']['license_changes'] > 0:
        print("\n⚠️  Warning: License changes detected!")
        sys.exit(3)


if __name__ == '__main__':
    main()
