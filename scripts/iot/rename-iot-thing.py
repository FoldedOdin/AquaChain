#!/usr/bin/env python3
"""
Rename IoT Thing by creating new Thing and moving certificate
AWS IoT doesn't support direct renaming, so we:
1. Create new Thing with new name
2. Detach certificate from old Thing
3. Attach certificate to new Thing
4. Delete old Thing
"""

import boto3
import sys

def rename_thing(old_name, new_name):
    """Rename IoT Thing by recreating with new name"""
    
    iot_client = boto3.client('iot')
    
    print(f"🔄 Renaming Thing: {old_name} → {new_name}")
    print("="*60)
    
    try:
        # Step 1: Check if old Thing exists
        print(f"\n1️⃣  Checking old Thing: {old_name}")
        old_thing = iot_client.describe_thing(thingName=old_name)
        print(f"   ✅ Found: {old_thing['thingArn']}")
        
        # Step 2: Get attached certificates
        print(f"\n2️⃣  Getting attached certificates...")
        principals = iot_client.list_thing_principals(thingName=old_name)
        
        if not principals['principals']:
            print(f"   ❌ No certificates attached to {old_name}")
            return False
        
        certificate_arn = principals['principals'][0]
        print(f"   ✅ Certificate: {certificate_arn.split('/')[-1]}")
        
        # Step 3: Create new Thing
        print(f"\n3️⃣  Creating new Thing: {new_name}")
        try:
            new_thing = iot_client.create_thing(
                thingName=new_name,
                attributePayload={
                    'attributes': old_thing.get('attributes', {}),
                    'merge': False
                }
            )
            print(f"   ✅ Created: {new_thing['thingArn']}")
        except iot_client.exceptions.ResourceAlreadyExistsException:
            print(f"   ⚠️  Thing {new_name} already exists, using existing")
        
        # Step 4: Detach certificate from old Thing
        print(f"\n4️⃣  Detaching certificate from {old_name}...")
        iot_client.detach_thing_principal(
            thingName=old_name,
            principal=certificate_arn
        )
        print(f"   ✅ Detached")
        
        # Step 5: Attach certificate to new Thing
        print(f"\n5️⃣  Attaching certificate to {new_name}...")
        iot_client.attach_thing_principal(
            thingName=new_name,
            principal=certificate_arn
        )
        print(f"   ✅ Attached")
        
        # Step 6: Delete old Thing
        print(f"\n6️⃣  Deleting old Thing: {old_name}...")
        iot_client.delete_thing(thingName=old_name)
        print(f"   ✅ Deleted")
        
        print("\n" + "="*60)
        print(f"✅ Successfully renamed Thing!")
        print("="*60)
        print(f"\nOld Name: {old_name}")
        print(f"New Name: {new_name}")
        print(f"Certificate: {certificate_arn.split('/')[-1]}")
        
        return True
        
    except iot_client.exceptions.ResourceNotFoundException as e:
        print(f"   ❌ Thing not found: {e}")
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python rename-iot-thing.py <old_name> <new_name>")
        print("\nExample:")
        print("  python rename-iot-thing.py ESP32-001 DEV-0001")
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    
    print("="*60)
    print("AWS IoT Thing Rename")
    print("="*60)
    print()
    
    success = rename_thing(old_name, new_name)
    
    if success:
        print("\n💡 Next Steps:")
        print(f"   1. Update config.h: #define DEVICE_ID \"{new_name}\"")
        print("   2. Reflash your ESP32")
        print("   3. Test connection")
        sys.exit(0)
    else:
        print("\n❌ Rename failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
