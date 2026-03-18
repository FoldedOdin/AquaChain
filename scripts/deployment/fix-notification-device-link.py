"""
Fix two issues blocking notification delivery:
  1. Link ESP32-001 to its owner in AquaChain-Users (deviceIds array was empty)
  2. Update notification Lambda env var USERS_TABLE to correct table name (AquaChain-Users)
"""
import boto3
import json

REGION = "ap-south-1"
USERS_TABLE = "AquaChain-Users"
LAMBDA_FUNCTION_NAME = "aquachain-function-notification-dev"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

# ── Fix 1: Link ESP32-001 to its owner ────────────────────────────────────────
DEVICE_ID = "ESP32-001"
OWNER_USER_ID = "51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0"

print("=" * 60)
print("Fix 1: Linking ESP32-001 to owner in AquaChain-Users")
print("=" * 60)

table = dynamodb.Table(USERS_TABLE)

# Check current state
current = table.get_item(Key={"userId": OWNER_USER_ID}).get("Item", {})
current_devices = current.get("deviceIds", [])
print(f"User:            {OWNER_USER_ID}")
print(f"Email:           {current.get('email', 'N/A')}")
print(f"Current devices: {current_devices}")

if DEVICE_ID in current_devices:
    print(f"Already linked: {DEVICE_ID}")
else:
    table.update_item(
        Key={"userId": OWNER_USER_ID},
        UpdateExpression="SET deviceIds = list_append(if_not_exists(deviceIds, :empty), :device)",
        ExpressionAttributeValues={
            ":device": [DEVICE_ID],
            ":empty": []
        }
    )
    print(f"Linked {DEVICE_ID} to user {OWNER_USER_ID}")

# Verify
updated = table.get_item(Key={"userId": OWNER_USER_ID}).get("Item", {})
print(f"Verified devices: {updated.get('deviceIds', [])}")

# ── Fix 2: Update Lambda env var USERS_TABLE ──────────────────────────────────
print()
print("=" * 60)
print("Fix 2: Updating notification Lambda USERS_TABLE env var")
print("=" * 60)

fn = lambda_client.get_function_configuration(FunctionName=LAMBDA_FUNCTION_NAME)
current_env = fn["Environment"]["Variables"]

print(f"Current USERS_TABLE: {current_env.get('USERS_TABLE', '(not set)')}")

current_env["USERS_TABLE"] = USERS_TABLE

lambda_client.update_function_configuration(
    FunctionName=LAMBDA_FUNCTION_NAME,
    Environment={"Variables": current_env}
)

# Wait for update
waiter = lambda_client.get_waiter("function_updated")
waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)
print(f"Updated USERS_TABLE → {USERS_TABLE}")

# ── Smoke test ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("Smoke test: invoking notification Lambda with ESP32-001")
print("=" * 60)

test_payload = {
    "action": "send_alert",
    "alert": {
        "deviceId": "ESP32-001",
        "alertLevel": "critical",
        "wqi": 37.0,
        "timestamp": "2026-03-18T13:10:00Z",
        "alertReasons": [
            "WQI below critical threshold (37 < 50)",
            "pH out of safe range (6.1)"
        ],
        "readings": {
            "pH": 6.1,
            "turbidity": 3.5,
            "tds": 450,
            "temperature": 22.5
        }
    }
}

response = lambda_client.invoke(
    FunctionName=LAMBDA_FUNCTION_NAME,
    InvocationType="RequestResponse",
    Payload=json.dumps(test_payload).encode()
)

result = json.loads(response["Payload"].read())
print(f"HTTP status: {response['StatusCode']}")
print(f"Response:\n{json.dumps(result, indent=2)}")
