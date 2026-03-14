#!/usr/bin/env python3
"""
Try to reproduce the exact frontend login issue
"""

import requests
import json
import time

def test_with_browser_headers():
    """Test with headers that match what a browser would send"""
    print("🌐 Testing with browser-like headers...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    # Headers that match what a browser would send
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'http://localhost:3000',
        'Referer': 'http://localhost:3000/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    payload = {
        'email': 'leninat259@gmail.com',
        'password': 'AquaChain123!'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS with browser headers")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_with_form_data():
    """Test with form data instead of JSON"""
    print("\n📝 Testing with form data...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://localhost:3000'
    }
    
    payload = {
        'email': 'leninat259@gmail.com',
        'password': 'AquaChain123!'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS with form data")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_timing_issue():
    """Test if there's a timing issue with rapid requests"""
    print("\n⏱️ Testing timing issues...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    payload = {
        'email': 'leninat259@gmail.com',
        'password': 'AquaChain123!'
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Try multiple rapid requests
    for i in range(3):
        print(f"   Request {i+1}:")
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"      Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"      ❌ FAILED: {response.text}")
            else:
                print(f"      ✅ SUCCESS")
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
        
        # Small delay between requests
        time.sleep(0.5)

def test_different_email_formats():
    """Test different email formats that might cause issues"""
    print("\n📧 Testing different email formats...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    email_formats = [
        'leninat259@gmail.com',           # Normal
        'LENINAT259@GMAIL.COM',           # Uppercase
        'Leninat259@Gmail.Com',           # Mixed case
        ' leninat259@gmail.com ',         # With spaces
        'leninat259@gmail.com\n',         # With newline
        'leninat259@gmail.com\r',         # With carriage return
    ]
    
    for email in email_formats:
        print(f"   Testing: '{email}'")
        
        payload = {
            'email': email,
            'password': 'AquaChain123!'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ SUCCESS")
            else:
                print(f"      ❌ FAILED")
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")

def main():
    """Main function"""
    print("🚀 Reproducing Frontend Login Issue")
    print("=" * 60)
    
    # Test different scenarios
    test_with_browser_headers()
    test_with_form_data()
    test_timing_issue()
    test_different_email_formats()
    
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS:")
    print("If any of the above tests failed, that might indicate the issue")
    print("Most likely causes:")
    print("1. Email case sensitivity")
    print("2. Extra whitespace in email/password")
    print("3. Different Content-Type header")
    print("4. Browser auto-fill changing the values")

if __name__ == "__main__":
    main()