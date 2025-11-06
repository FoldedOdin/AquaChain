#!/usr/bin/env python3
"""
Script to remove humidity sensor references from AquaChain codebase
Since humidity is NOT a water quality parameter, we're removing it entirely.
"""

import os
import re
import json
from pathlib import Path

def remove_humidity_from_json_config(file_path):
    """Remove humidity from JSON configuration files"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        modified = False
        
        # Remove from sensor profiles
        if 'sensorProfiles' in data:
            for profile_name, profile in data['sensorProfiles'].items():
                if 'humidity' in profile:
                    del profile['humidity']
                    modified = True
                    print(f"  Removed humidity from {profile_name} profile")
        
        if modified:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Updated: {file_path}")
        
        return modified
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def remove_humidity_from_python(file_path):
    """Remove humidity references from Python files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove humidity from feature lists
        content = re.sub(
            r"?\s*",
            "",
            content
        )
        
        # Remove humidity from validation ranges
        content = re.sub(
            r":\s*\{[^}]+\},?\s*",
            "",
            content
        )
        content = re.sub(
            r":\s*\([^)]+\),?\s*",
            "",
            content
        )
        
        # Remove humidity from test data
        content = re.sub(
            r":\s*[\d.]+,?\s*",
            "",
            content
        )
        
        # Remove humidity from comments
        content = re.sub(
            r",\s*humidity\s*",
            "",
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def remove_humidity_from_cpp(file_path):
    """Remove humidity references from C++ files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove DHT sensor initialization
        content = re.sub(
            r"dht\.begin\(\);?\s*",
            "",
            content
        )
        
        # Remove humidity readings
        content = re.sub(
            r"readings\.humidity\s*=\s*dht\.readHumidity\(\);?\s*",
            "",
            content
        )
        
        # Remove humidity validation
        content = re.sub(
            r"if\s*\(isnan\(readings\.temperature\)\s*\|\|\s*isnan\(readings\.humidity\)\)",
            "if (isnan(readings.temperature))",
            content
        )
        
        # Remove humidity from JSON
        content = re.sub(
            r'sensorData\["humidity"\]\s*=\s*readings\.humidity;?\s*',
            "",
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to remove humidity from all files"""
    print("=" * 60)
    print("Removing Humidity Sensor from AquaChain Codebase")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent.parent
    files_updated = 0
    
    # Update JSON config files
    print("📝 Updating JSON configuration files...")
    json_files = [
        project_root / "iot-simulator" / "config" / "devices.json",
    ]
    
    for json_file in json_files:
        if json_file.exists():
            if remove_humidity_from_json_config(json_file):
                files_updated += 1
    
    print()
    
    # Update Python files
    print("🐍 Updating Python files...")
    python_patterns = [
        "lambda/**/*.py",
        "tests/**/*.py",
        "scripts/**/*.py",
        "iot-simulator/**/*.py",
    ]
    
    for pattern in python_patterns:
        for py_file in project_root.glob(pattern):
            if 'node_modules' not in str(py_file) and 'venv' not in str(py_file):
                if remove_humidity_from_python(py_file):
                    files_updated += 1
    
    print()
    
    # Update C++ files
    print("⚙️  Updating ESP32 firmware files...")
    cpp_files = list((project_root / "iot-simulator" / "esp32-firmware").glob("**/*.ino"))
    cpp_files += list((project_root / "iot-simulator" / "esp32-firmware").glob("**/*.h"))
    cpp_files += list((project_root / "iot-simulator" / "esp32-firmware").glob("**/*.cpp"))
    
    for cpp_file in cpp_files:
        if remove_humidity_from_cpp(cpp_file):
            files_updated += 1
    
    print()
    print("=" * 60)
    print(f"✅ Complete! Updated {files_updated} files")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: You should now:")
    print("1. Review the changes")
    print("2. Run tests to ensure nothing broke")
    print("3. Update ML models to use 4 features instead of 5")
    print("4. Retrain ML models without humidity feature")
    print()

if __name__ == "__main__":
    main()
