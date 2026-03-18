"""
Check which device IDs are linked to users in DynamoDB.
Helps confirm the real ESP32 device ID matches what the notification Lambda will look up.
"""
import boto3
import json

REGION = "ap-south-1"
USERS_TABLE = "AquaChain-Users"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(USERS_TABLE)

print(f"Scanning {USERS_TABLE} for users with deviceIds...\n")

response = table.scan(
    ProjectionExpression="userId, email, #role, deviceIds",
    ExpressionAttributeNames={"#role": "role"}
)

items = response.get("Items", [])

if not items:
    print("No users found in table.")
else:
    for user in items:
        user_id = user.get("userId", "N/A")
        email = user.get("email", "N/A")
        role = user.get("role", "N/A")
        device_ids = user.get("deviceIds", [])
        print(f"User:      {user_id}")
        print(f"Email:     {email}")
        print(f"Role:      {role}")
        print(f"DeviceIDs: {device_ids if device_ids else '(none linked)'}")
        print("-" * 50)

print(f"\nTotal users: {len(items)}")
print(f"Users with devices: {sum(1 for u in items if u.get('deviceIds'))}")
