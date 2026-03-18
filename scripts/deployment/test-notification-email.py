"""
End-to-end test: invoke notification Lambda with a real critical alert.
Sends an actual email via SES to verify the full pipeline works.
"""
import boto3
import json

REGION = "ap-south-1"
FUNCTION_NAME = "aquachain-function-notification-dev"

client = boto3.client("lambda", region_name=REGION)

payload = {
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

print(f"Invoking {FUNCTION_NAME}...")
response = client.invoke(
    FunctionName=FUNCTION_NAME,
    InvocationType="RequestResponse",
    Payload=json.dumps(payload).encode()
)

result = json.loads(response["Payload"].read())
print(f"HTTP status: {response['StatusCode']}")
print(f"Response:\n{json.dumps(result, indent=2)}")
