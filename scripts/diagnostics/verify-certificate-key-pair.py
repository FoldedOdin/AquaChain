#!/usr/bin/env python3
"""
Verify that certificate and private key in config.h are a matching pair
"""

import re
import sys

def extract_certificate_from_config(config_path):
    """Extract AWS_CERT from config.h"""
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find AWS_CERT
        cert_match = re.search(r'const char AWS_CERT\[\] PROGMEM = R"KEY\((.*?)-----END CERTIFICATE-----', content, re.DOTALL)
        if cert_match:
            cert = cert_match.group(1) + "-----END CERTIFICATE-----"
            return cert.strip()
        return None
    except Exception as e:
        print(f"Error reading config.h: {e}")
        return None

def extract_private_key_from_config(config_path):
    """Extract AWS_PRIVATE_KEY from config.h"""
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find AWS_PRIVATE_KEY
        key_match = re.search(r'const char AWS_PRIVATE_KEY\[\] PROGMEM = R"KEY\((.*?)-----END RSA PRIVATE KEY-----', content, re.DOTALL)
        if key_match:
            key = key_match.group(1) + "-----END RSA PRIVATE KEY-----"
            return key.strip()
        return None
    except Exception as e:
        print(f"Error reading config.h: {e}")
        return None

def check_certificate_key_match():
    """Check if certificate and key are from the same pair"""
    print("=" * 60)
    print("Certificate/Key Pair Verification")
    print("=" * 60)
    
    config_path = "iot-firmware/aquachain-esp32/aquachain-esp32-improved/config.h"
    
    print(f"\nReading certificates from: {config_path}")
    
    cert = extract_certificate_from_config(config_path)
    key = extract_private_key_from_config(config_path)
    
    if not cert:
        print("✗ Could not extract AWS_CERT from config.h")
        return False
    
    if not key:
        print("✗ Could not extract AWS_PRIVATE_KEY from config.h")
        return False
    
    print("✓ Found AWS_CERT in config.h")
    print("✓ Found AWS_PRIVATE_KEY in config.h")
    
    # Save to temp files for OpenSSL verification
    import tempfile
    import os
    import subprocess
    
    try:
        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write(cert)
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write(key)
            key_path = key_file.name
        
        print("\n" + "=" * 60)
        print("Verifying Certificate/Key Pair Match")
        print("=" * 60)
        
        # Extract public key from certificate
        cert_pubkey_result = subprocess.run(
            ['openssl', 'x509', '-in', cert_path, '-pubkey', '-noout'],
            capture_output=True,
            text=True
        )
        
        if cert_pubkey_result.returncode != 0:
            print("✗ Could not extract public key from certificate")
            print(f"Error: {cert_pubkey_result.stderr}")
            return False
        
        # Extract public key from private key
        key_pubkey_result = subprocess.run(
            ['openssl', 'rsa', '-in', key_path, '-pubout'],
            capture_output=True,
            text=True
        )
        
        if key_pubkey_result.returncode != 0:
            print("✗ Could not extract public key from private key")
            print(f"Error: {key_pubkey_result.stderr}")
            return False
        
        # Compare public keys
        cert_pubkey = cert_pubkey_result.stdout.strip()
        key_pubkey = key_pubkey_result.stdout.strip()
        
        if cert_pubkey == key_pubkey:
            print("✓ Certificate and private key are a MATCHING PAIR!")
            print("\nYour certificates are correct.")
            return True
        else:
            print("✗ Certificate and private key DO NOT MATCH!")
            print("\nThis is the problem! You need to:")
            print("1. Download a new certificate bundle from AWS IoT")
            print("2. Use the certificate and key from the SAME download")
            print("3. Update config.h with both files")
            return False
        
    except FileNotFoundError:
        print("\n⚠ OpenSSL not found in PATH")
        print("Cannot verify certificate/key pair match without OpenSSL")
        print("\nManual verification:")
        print("1. Ensure AWS_CERT and AWS_PRIVATE_KEY are from the same download")
        print("2. Check the certificate creation date in AWS IoT Console")
        print("3. Verify you downloaded all 3 files together")
        return None
    
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        return False
    
    finally:
        # Clean up temp files
        try:
            if 'cert_path' in locals():
                os.unlink(cert_path)
            if 'key_path' in locals():
                os.unlink(key_path)
        except:
            pass

def main():
    result = check_certificate_key_match()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if result is True:
        print("\n✓ Your certificates are correctly matched!")
        print("\nIf ESP32 still fails to connect, check:")
        print("1. System time is correct (epoch > 1000000000)")
        print("2. Thing name matches: ESP32-001")
        print("3. Certificate is ACTIVE in AWS IoT")
        print("4. Policy allows iot:Connect")
        print("5. Endpoint is correct with -ats suffix")
    
    elif result is False:
        print("\n✗ Certificate and key DO NOT match!")
        print("\nTO FIX:")
        print("1. Go to AWS IoT Console → Security → Certificates")
        print("2. Create new certificate (or use existing)")
        print("3. Download ALL 3 files:")
        print("   - device-certificate.pem.crt")
        print("   - private.pem.key")
        print("   - AmazonRootCA1.pem")
        print("4. Update config.h with content from these files")
        print("5. Ensure certificate is attached to Thing 'ESP32-001'")
        print("6. Ensure policy 'aquachain-device-policy-dev' is attached")
    
    else:
        print("\n⚠ Could not verify certificate/key pair")
        print("\nManual checklist:")
        print("1. AWS_CERT and AWS_PRIVATE_KEY must be from same download")
        print("2. Check certificate creation date in AWS IoT Console")
        print("3. Verify all 3 files were downloaded together")
        print("4. Ensure no copy/paste errors in config.h")
    
    print("\n" + "=" * 60)
    
    return 0 if result else 1

if __name__ == '__main__':
    sys.exit(main())
