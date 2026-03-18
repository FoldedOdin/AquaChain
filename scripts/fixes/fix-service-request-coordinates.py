"""
Fix service requests that have coordinates stored under location.coordinates
instead of the flat location.latitude / location.longitude structure.

Also corrects the hardcoded 9.9312, 76.2673 placeholder coordinates by
pulling the actual coordinates from the order's delivery address when available.

Run: python scripts/fixes/fix-service-request-coordinates.py
"""

import boto3
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
service_requests_table = dynamodb.Table('aquachain-service-requests')
orders_table = dynamodb.Table('aquachain-orders')

# Hardcoded placeholder coordinates that were incorrectly used
PLACEHOLDER_COORDS = {
    (Decimal('9.9312'), Decimal('76.2673')),
    (9.9312, 76.2673),
}


def scan_all_service_requests():
    items = []
    response = service_requests_table.scan()
    items.extend(response['Items'])
    while 'LastEvaluatedKey' in response:
        response = service_requests_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items


def get_order_address_and_coordinates(order_id: str):
    """
    Try to get real address + coordinates from the linked order's delivery address.
    Returns (address_str, lat, lng) — any of which may be None.
    """
    if not order_id:
        return None, None, None
    try:
        response = orders_table.get_item(Key={'orderId': order_id})
        order = response.get('Item', {})
        addr = order.get('deliveryAddress') or order.get('shippingAddress') or {}
        if isinstance(addr, str):
            try:
                addr = json.loads(addr)
            except Exception:
                addr = {}

        # Build a human-readable address string from the order
        parts = [
            addr.get('street') or addr.get('address') or addr.get('fullAddress'),
            addr.get('landmark'),
            addr.get('city'),
            addr.get('state'),
            addr.get('pincode'),
        ]
        address_str = ', '.join(p for p in parts if p) or None

        lat = addr.get('latitude') or addr.get('lat')
        lng = addr.get('longitude') or addr.get('lng') or addr.get('lon')
        # Also check nested coordinates
        coords = addr.get('coordinates', {})
        if not lat:
            lat = coords.get('latitude') or coords.get('lat')
        if not lng:
            lng = coords.get('longitude') or coords.get('lng') or coords.get('lon')

        lat = Decimal(str(lat)) if lat else None
        lng = Decimal(str(lng)) if lng else None
        return address_str, lat, lng
    except Exception as e:
        print(f"  ⚠️  Could not fetch order {order_id}: {e}")
    return None, None, None


def geocode_with_aws_location(address: str):
    """
    Geocode an address using AWS Location Service.
    Returns (lat, lng) or (None, None) if unavailable.
    """
    try:
        location_client = boto3.client('location', region_name='ap-south-1')
        response = location_client.search_place_index_for_text(
            IndexName='aquachain-places',
            Text=address,
            MaxResults=1,
        )
        results = response.get('Results', [])
        if results:
            point = results[0]['Place']['Geometry']['Point']
            # AWS Location returns [longitude, latitude]
            return Decimal(str(point[1])), Decimal(str(point[0]))
    except Exception as e:
        print(f"  ⚠️  AWS Location geocoding failed for '{address}': {e}")
    return None, None


def needs_fix(location: dict) -> tuple:
    """
    Returns (needs_fix, flat_lat, flat_lng, reason).
    Checks for nested coordinates structure or placeholder values.
    """
    if not location:
        return False, None, None, None

    nested = location.get('coordinates', {})
    flat_lat = location.get('latitude')
    flat_lng = location.get('longitude')

    # Case 1: coordinates are nested under location.coordinates
    if nested and (not flat_lat or not flat_lng):
        return True, nested.get('latitude'), nested.get('longitude'), 'nested coordinates'

    # Case 2: flat coordinates exist but are the hardcoded placeholder
    if flat_lat is not None and flat_lng is not None:
        if (Decimal(str(flat_lat)), Decimal(str(flat_lng))) in PLACEHOLDER_COORDS:
            return True, flat_lat, flat_lng, 'placeholder coordinates'

    return False, None, None, None


def fix_service_requests():
    print("🔍 Scanning service requests...")
    items = scan_all_service_requests()
    print(f"   Found {len(items)} service requests\n")

    fixed = 0
    skipped = 0

    for sr in items:
        request_id = sr.get('requestId', '?')
        location = sr.get('location', {})
        should_fix, lat, lng, reason = needs_fix(location)

        if not should_fix:
            skipped += 1
            continue

        print(f"🔧 Fixing {request_id} ({reason})")

        # Try to get real address + coordinates from the linked order
        order_id = sr.get('orderId')
        order_address, order_lat, order_lng = get_order_address_and_coordinates(order_id)

        if order_lat and order_lng:
            new_lat, new_lng = order_lat, order_lng
            new_address = order_address or location.get('address', '')
            print(f"   ✅ Using order coordinates: {new_lat}, {new_lng}")
        elif order_address:
            # We have an address but no coordinates — geocode it
            print(f"   🌍 Geocoding: {order_address}")
            new_lat, new_lng = geocode_with_aws_location(order_address)
            new_address = order_address
            if new_lat and new_lng:
                print(f"   ✅ Geocoded to: {new_lat}, {new_lng}")
            else:
                # Fall back to whatever coordinates we already have (just flatten)
                new_lat = Decimal(str(lat)) if lat else Decimal('0')
                new_lng = Decimal(str(lng)) if lng else Decimal('0')
                print(f"   ⚠️  Geocoding failed, keeping existing: {new_lat}, {new_lng}")
        else:
            # No order data at all — just flatten the existing nested structure
            new_lat = Decimal(str(lat)) if lat else Decimal('0')
            new_lng = Decimal(str(lng)) if lng else Decimal('0')
            new_address = location.get('address', '')
            print(f"   ⚠️  No order found, keeping existing: {new_lat}, {new_lng}")

        # Build corrected location (flat structure matching TechnicianTask type)
        corrected_location = {
            'address': new_address,
            'latitude': new_lat,
            'longitude': new_lng,
        }

        service_requests_table.update_item(
            Key={'requestId': request_id},
            UpdateExpression='SET #loc = :loc',
            ExpressionAttributeNames={'#loc': 'location'},
            ExpressionAttributeValues={':loc': corrected_location}
        )
        print(f"   ✅ Updated location for {request_id}\n")
        fixed += 1

    print(f"\n✅ Done. Fixed: {fixed}, Skipped (already correct): {skipped}")


if __name__ == '__main__':
    fix_service_requests()
