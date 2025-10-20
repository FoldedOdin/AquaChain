#!/usr/bin/env python3
"""
CDK code validation script that doesn't require AWS CDK libraries
"""

import os
import sys
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

class CDKCodeValidator:
    """
    Validates CDK Python code structure and best practices
    """
    
    def __init__(self, cdk_root: str):
        self.cdk_root = Path(cdk_root)
        self.validation_results = {
            "overall_success": True,
            "validations": {}
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks
        """
        print("Validating AquaChain CDK Code Structure")
        print("=" * 50)
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Python Syntax", self.validate_python_syntax),
            ("Import Structure", self.validate_imports),
            ("Configuration Files", self.validate_config_files),
            ("Environment Configs", self.validate_environment_configs),
            ("Naming Conventions", self.validate_naming_conventions)
        ]
        
        for validation_name, validation_func in validations:
            print(f"\n{validation_name}:")
            print("-" * 30)
            
            try:
                success, details = validation_func()
                self.validation_results["validations"][validation_name.lower().replace(" ", "_")] = {
                    "success": success,
                    "details": details
                }
                
                if success:
                    print(f"✓ {validation_name} validation passed")
                else:
                    print(f"✗ {validation_name} validation failed")
                    self.validation_results["overall_success"] = False
                    
            except Exception as e:
                print(f"✗ {validation_name} validation error: {e}")
                self.validation_results["validations"][validation_name.lower().replace(" ", "_")] = {
                    "success": False,
                    "error": str(e)
                }
                self.validation_results["overall_success"] = False
        
        print("\n" + "=" * 50)
        if self.validation_results["overall_success"]:
            print("✓ All CDK code validations passed")
        else:
            print("✗ Some CDK code validations failed")
        
        return self.validation_results
    
    def validate_file_structure(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate expected file structure exists
        """
        expected_files = [
            "app.py",
            "cdk.json",
            "requirements.txt",
            "config/environment_config.py",
            "stacks/security_stack.py",
            "stacks/core_stack.py",
            "stacks/data_stack.py",
            "stacks/compute_stack.py",
            "stacks/api_stack.py",
            "stacks/monitoring_stack.py",
            "deployment/deploy.py",
            "validation/validate_infrastructure.py",
            "tests/test_stacks.py"
        ]
        
        expected_dirs = [
            "stacks",
            "config",
            "deployment",
            "validation",
            "tests",
            "scripts"
        ]
        
        missing_files = []
        missing_dirs = []
        
        # Check files
        for file_path in expected_files:
            full_path = self.cdk_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                print(f"  ✓ Found {file_path}")
        
        # Check directories
        for dir_path in expected_dirs:
            full_path = self.cdk_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            else:
                print(f"  ✓ Found directory {dir_path}/")
        
        success = len(missing_files) == 0 and len(missing_dirs) == 0
        
        if missing_files:
            print(f"  ✗ Missing files: {missing_files}")
        if missing_dirs:
            print(f"  ✗ Missing directories: {missing_dirs}")
        
        return success, {
            "missing_files": missing_files,
            "missing_dirs": missing_dirs,
            "expected_files": expected_files,
            "expected_dirs": expected_dirs
        }
    
    def validate_python_syntax(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate Python syntax in all .py files
        """
        python_files = list(self.cdk_root.rglob("*.py"))
        syntax_errors = []
        valid_files = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the AST to check syntax
                ast.parse(content)
                valid_files.append(str(py_file.relative_to(self.cdk_root)))
                print(f"  ✓ {py_file.relative_to(self.cdk_root)}")
                
            except SyntaxError as e:
                error_info = {
                    "file": str(py_file.relative_to(self.cdk_root)),
                    "line": e.lineno,
                    "error": str(e)
                }
                syntax_errors.append(error_info)
                print(f"  ✗ {py_file.relative_to(self.cdk_root)}: {e}")
            except Exception as e:
                error_info = {
                    "file": str(py_file.relative_to(self.cdk_root)),
                    "error": str(e)
                }
                syntax_errors.append(error_info)
                print(f"  ✗ {py_file.relative_to(self.cdk_root)}: {e}")
        
        success = len(syntax_errors) == 0
        
        return success, {
            "total_files": len(python_files),
            "valid_files": len(valid_files),
            "syntax_errors": syntax_errors
        }
    
    def validate_imports(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate import structure in stack files
        """
        stack_files = [
            "stacks/security_stack.py",
            "stacks/core_stack.py", 
            "stacks/data_stack.py",
            "stacks/compute_stack.py",
            "stacks/api_stack.py",
            "stacks/monitoring_stack.py"
        ]
        
        expected_imports = {
            "aws_cdk": ["Stack"],
            "constructs": ["Construct"],
            "typing": ["Dict", "Any"]
        }
        
        import_issues = []
        valid_imports = []
        
        for stack_file in stack_files:
            file_path = self.cdk_root / stack_file
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check for expected imports
                imports_found = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports_found.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports_found.append(node.module)
                
                # Validate expected imports are present
                file_valid = True
                for expected_module in expected_imports:
                    if not any(expected_module in imp for imp in imports_found):
                        import_issues.append({
                            "file": stack_file,
                            "missing_import": expected_module
                        })
                        file_valid = False
                
                if file_valid:
                    valid_imports.append(stack_file)
                    print(f"  ✓ {stack_file} imports are valid")
                else:
                    print(f"  ✗ {stack_file} has import issues")
                    
            except Exception as e:
                import_issues.append({
                    "file": stack_file,
                    "error": str(e)
                })
                print(f"  ✗ {stack_file}: {e}")
        
        success = len(import_issues) == 0
        
        return success, {
            "valid_files": len(valid_imports),
            "import_issues": import_issues
        }
    
    def validate_config_files(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate configuration files are properly formatted
        """
        config_files = [
            ("cdk.json", "json"),
            ("requirements.txt", "text")
        ]
        
        config_issues = []
        valid_configs = []
        
        for config_file, file_type in config_files:
            file_path = self.cdk_root / config_file
            
            if not file_path.exists():
                config_issues.append({
                    "file": config_file,
                    "error": "File not found"
                })
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if file_type == "json":
                    json.loads(content)  # Validate JSON syntax
                    print(f"  ✓ {config_file} is valid JSON")
                elif file_type == "text":
                    # Basic validation for requirements.txt
                    lines = content.strip().split('\n')
                    if len(lines) > 0 and any('aws-cdk' in line for line in lines):
                        print(f"  ✓ {config_file} contains CDK dependencies")
                    else:
                        config_issues.append({
                            "file": config_file,
                            "error": "Missing CDK dependencies"
                        })
                        continue
                
                valid_configs.append(config_file)
                
            except json.JSONDecodeError as e:
                config_issues.append({
                    "file": config_file,
                    "error": f"Invalid JSON: {e}"
                })
                print(f"  ✗ {config_file}: Invalid JSON - {e}")
            except Exception as e:
                config_issues.append({
                    "file": config_file,
                    "error": str(e)
                })
                print(f"  ✗ {config_file}: {e}")
        
        success = len(config_issues) == 0
        
        return success, {
            "valid_configs": len(valid_configs),
            "config_issues": config_issues
        }
    
    def validate_environment_configs(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate environment configuration structure
        """
        config_file = self.cdk_root / "config" / "environment_config.py"
        
        if not config_file.exists():
            return False, {"error": "environment_config.py not found"}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required functions
            required_functions = [
                "get_environment_config",
                "get_resource_name"
            ]
            
            functions_found = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions_found.append(node.name)
            
            missing_functions = set(required_functions) - set(functions_found)
            
            if missing_functions:
                print(f"  ✗ Missing functions: {missing_functions}")
                return False, {
                    "missing_functions": list(missing_functions),
                    "found_functions": functions_found
                }
            else:
                print(f"  ✓ All required functions found: {functions_found}")
                return True, {
                    "found_functions": functions_found
                }
                
        except Exception as e:
            print(f"  ✗ Error validating environment config: {e}")
            return False, {"error": str(e)}
    
    def validate_naming_conventions(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate naming conventions in stack files
        """
        stack_files = list((self.cdk_root / "stacks").glob("*.py"))
        naming_issues = []
        valid_files = []
        
        for stack_file in stack_files:
            if stack_file.name == "__init__.py":
                continue
                
            try:
                with open(stack_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check class naming conventions
                classes_found = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes_found.append(node.name)
                        
                        # Check if class name follows convention
                        if not (node.name.startswith("AquaChain") and node.name.endswith("Stack")):
                            naming_issues.append({
                                "file": stack_file.name,
                                "class": node.name,
                                "issue": "Class name should start with 'AquaChain' and end with 'Stack'"
                            })
                
                if len([issue for issue in naming_issues if issue["file"] == stack_file.name]) == 0:
                    valid_files.append(stack_file.name)
                    print(f"  ✓ {stack_file.name} follows naming conventions")
                else:
                    print(f"  ✗ {stack_file.name} has naming issues")
                    
            except Exception as e:
                naming_issues.append({
                    "file": stack_file.name,
                    "error": str(e)
                })
                print(f"  ✗ {stack_file.name}: {e}")
        
        success = len(naming_issues) == 0
        
        return success, {
            "valid_files": len(valid_files),
            "naming_issues": naming_issues
        }

def main():
    """
    Main validation script
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate AquaChain CDK code")
    parser.add_argument("--cdk-root", default=".", help="CDK root directory")
    parser.add_argument("--output", "-o", help="Output file for validation results (JSON)")
    
    args = parser.parse_args()
    
    # Run validation
    validator = CDKCodeValidator(args.cdk_root)
    results = validator.validate_all()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nValidation results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()