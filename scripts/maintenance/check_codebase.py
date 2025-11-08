#!/usr/bin/env python3
"""
Comprehensive codebase error checker
"""
import os
import sys
import py_compile
from pathlib import Path

def check_python_files():
    """Check all Python files for syntax errors"""
    errors = []
    checked = 0
    
    # Directories to check
    dirs_to_check = ['scripts', 'lambda', 'tests', 'iot-simulator', 'infrastructure']
    
    # Directories to exclude
    exclude_dirs = {'node_modules', 'venv', '.venv', 'build', 'dist', 'cdk.out', '__pycache__', '.git'}
    
    for directory in dirs_to_check:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    checked += 1
                    
                    try:
                        py_compile.compile(filepath, doraise=True)
                    except py_compile.PyCompileError as e:
                        errors.append({
                            'file': filepath,
                            'error': str(e)
                        })
    
    return checked, errors

def check_json_files():
    """Check JSON files for syntax errors"""
    import json
    errors = []
    checked = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip node_modules and other build directories
        dirs[:] = [d for d in dirs if d not in {'node_modules', 'venv', '.venv', 'build', 'dist', 'cdk.out', '.git'}]
        
        for file in files:
            if file.endswith('.json') and not file.startswith('.'):
                filepath = os.path.join(root, file)
                checked += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json.load(f)
                except Exception as e:
                    errors.append({
                        'file': filepath,
                        'error': str(e)
                    })
    
    return checked, errors

def main():
    print("=" * 70)
    print("AquaChain Codebase Error Check")
    print("=" * 70)
    print()
    
    # Check Python files
    print("🐍 Checking Python files...")
    py_checked, py_errors = check_python_files()
    print(f"   Checked: {py_checked} files")
    
    if py_errors:
        print(f"   ❌ Found {len(py_errors)} errors:")
        for error in py_errors:
            print(f"      • {error['file']}")
            print(f"        {error['error'][:200]}")
    else:
        print("   ✅ No Python syntax errors found")
    
    print()
    
    # Check JSON files
    print("📄 Checking JSON files...")
    json_checked, json_errors = check_json_files()
    print(f"   Checked: {json_checked} files")
    
    if json_errors:
        print(f"   ❌ Found {len(json_errors)} errors:")
        for error in json_errors:
            print(f"      • {error['file']}")
            print(f"        {error['error'][:200]}")
    else:
        print("   ✅ No JSON syntax errors found")
    
    print()
    print("=" * 70)
    
    total_errors = len(py_errors) + len(json_errors)
    if total_errors == 0:
        print("✅ All checks passed! No errors found.")
        return 0
    else:
        print(f"❌ Found {total_errors} total errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
