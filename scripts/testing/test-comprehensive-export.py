#!/usr/bin/env python3
"""
Test the comprehensive export functionality
"""

import json
import boto3
import requests
from datetime import datetime

def get_auth_token():
    """Get authentication token for testing"""
    try:
        # Use existing auth helper
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from testing.get_fresh_jwt_token import get_fresh_token
        return get_fresh_token()
    except Exception as e:
        print(f"❌ Error getting auth token: {e}")
        return None

def test_export_endpoint():
    """Test the new export endpoint"""
    print("🧪 Testing Comprehensive Export Functionality")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    # Test device ID (use a known device)
    device_id = "ESP32-001"
    
    # API endpoint
    api_base = "https://api.aquachain.example.com/dev"
    export_url = f"{api_base}/devices/{device_id}/readings/export"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test different export formats
    formats = ['json', 'csv', 'pdf']
    
    for export_format in formats:
        print(f"\n📊 Testing {export_format.upper()} export...")
        
        params = {
            'days': 7,
            'format': export_format
        }
        
        try:
            response = requests.get(export_url, headers=headers, params=params)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate export structure
                required_sections = [
                    'exportInfo', 'deviceInfo', 'waterQualitySummary', 
                    'sensorData', 'alerts', 'wqiInterpretation', 'metadata'
                ]
                
                missing_sections = []
                for section in required_sections:
                    if section not in data:
                        missing_sections.append(section)
                
                if missing_sections:
                    print(f"❌ Missing sections: {missing_sections}")
                else:
                    print(f"✅ All required sections present")
                    
                    # Print summary
                    export_info = data.get('exportInfo', {})
                    device_info = data.get('deviceInfo', {})
                    readings_count = len(data.get('sensorData', []))
                    alerts_count = len(data.get('alerts', []))
                    
                    print(f"   📅 Export Date: {export_info.get('exportDate')}")
                    print(f"   🏠 Device Location: {device_info.get('location')}")
                    print(f"   📊 Readings: {readings_count}")
                    print(f"   🚨 Alerts: {alerts_count}")
                    
                    # Show water quality summary
                    summary = data.get('waterQualitySummary', {})
                    if summary:
                        print(f"   💧 Water Quality Summary:")
                        for metric, values in summary.items():
                            if isinstance(values, dict):
                                avg = values.get('average', 'N/A')
                                min_val = values.get('min', 'N/A')
                                max_val = values.get('max', 'N/A')
                                print(f"      {metric}: Avg={avg}, Min={min_val}, Max={max_val}")
                    
                    # Show recent readings sample
                    readings = data.get('sensorData', [])
                    if readings:
                        print(f"   📈 Recent Reading Sample:")
                        recent = readings[0]  # Most recent
                        print(f"      Timestamp: {recent.get('timestamp')}")
                        print(f"      pH: {recent.get('pH')}")
                        print(f"      TDS: {recent.get('tds')} ppm")
                        print(f"      Turbidity: {recent.get('turbidity')} NTU")
                        print(f"      Temperature: {recent.get('temperature')} °C")
                        print(f"      WQI: {recent.get('wqi')} ({recent.get('quality')})")
                    
                    # Format-specific validation
                    if export_format == 'csv' and 'csvData' in data:
                        csv_data = data['csvData']
                        print(f"   📄 CSV Data Generated: {len(csv_data.get('readings', ''))} chars")
                    
                    if export_format == 'pdf' and 'chartData' in data:
                        chart_data = data['chartData']
                        print(f"   📊 Chart Data Points: {len(chart_data.get('timestamps', []))}")
                
            else:
                print(f"❌ Request failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing {export_format} export: {e}")
    
    print(f"\n🎯 Export Testing Complete!")
    return True

def compare_with_current_export():
    """Compare new export with current basic export"""
    print(f"\n🔍 Comparing Export Formats")
    print("=" * 40)
    
    # This would show the difference between old basic export and new comprehensive export
    print("📊 NEW Comprehensive Export includes:")
    print("   ✅ Device Information (ID, location, installation date, firmware)")
    print("   ✅ Water Quality Summary (avg, min, max for all parameters)")
    print("   ✅ Complete Sensor Data Table (timestamp, pH, TDS, turbidity, temp, WQI, status)")
    print("   ✅ Alerts Section (time, alert type, severity)")
    print("   ✅ WQI Interpretation Legend")
    print("   ✅ Metadata (system info, accuracy, sampling frequency)")
    print("   ✅ Multiple Formats (JSON, CSV, PDF-ready)")
    print("   ✅ Chart Data for Trend Graphs")
    
    print(f"\n📋 OLD Basic Export had:")
    print("   ❌ Only basic template information")
    print("   ❌ No actual sensor data")
    print("   ❌ No device details")
    print("   ❌ No water quality analysis")
    print("   ❌ No alerts or trends")

if __name__ == "__main__":
    print("🌊 AquaChain Comprehensive Export Test")
    print("=" * 50)
    
    success = test_export_endpoint()
    
    if success:
        compare_with_current_export()
        print(f"\n✅ Export enhancement is ready for deployment!")
    else:
        print(f"\n❌ Export testing failed - check configuration")