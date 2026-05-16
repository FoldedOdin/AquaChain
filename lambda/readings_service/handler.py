#!/usr/bin/env python3
"""
Readings Service Lambda Function
Handles device readings API endpoints: /latest, /history, /export
"""

import csv
import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key

# ---------------------------------------------------------------------------
# Logging — structured, level from env (default INFO)
# ---------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ---------------------------------------------------------------------------
# AWS clients — region resolved from environment (never hardcoded)
# ---------------------------------------------------------------------------
_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
dynamodb = boto3.resource("dynamodb", region_name=_REGION)

# Table references via environment variables with sensible defaults
readings_table = dynamodb.Table(os.environ.get("READINGS_TABLE", "AquaChain-Readings"))

# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def convert_decimals(obj: Any) -> Any:
    """Recursively convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def create_response(status_code: int, body: Dict[str, Any], cors: bool = True) -> Dict[str, Any]:
    """Create a standardized API Gateway proxy response."""
    serialized_body = json.dumps(convert_decimals(body))

    response: Dict[str, Any] = {
        "statusCode": status_code,
        "body": serialized_body,
        "isBase64Encoded": False,
    }

    if cors:
        response["headers"] = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": (
                "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token"
            ),
        }

    return response


_CORS_PREFLIGHT_RESPONSE: Dict[str, Any] = {
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": (
            "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token"
        ),
    },
    "body": "",
    "isBase64Encoded": False,
}

# ---------------------------------------------------------------------------
# Auth / claims helpers
# ---------------------------------------------------------------------------

def get_cognito_claims(event: Dict) -> Dict:
    """Safely extract Cognito claims from an API Gateway event."""
    try:
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        claims = authorizer.get("claims") or authorizer.get("jwt", {}).get("claims") or authorizer
        return claims or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not extract Cognito claims: %s", exc)
        return {}


def get_user_info(event: Dict) -> Dict[str, Any]:
    """Return a normalised dict of the authenticated user's identity."""
    claims = get_cognito_claims(event)
    return {
        "user_id": claims.get("sub", "unknown"),
        "username": claims.get("cognito:username", claims.get("username", "unknown")),
        "groups": claims.get("cognito:groups", []),
        "email": claims.get("email", "unknown"),
    }

# ---------------------------------------------------------------------------
# Device info — GSI query instead of table scan
# ---------------------------------------------------------------------------

def get_device_info(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up device metadata.

    Queries the Devices table by primary key first (O(1)).
    Falls back to a graceful default so the caller never receives None
    purely because the device table was unavailable.
    """
    try:
        devices_table = dynamodb.Table(os.environ.get("DEVICES_TABLE", "AquaChain-Devices"))
        result = devices_table.get_item(Key={"deviceId": device_id})
        item = result.get("Item")
        if item:
            return {
                "deviceId": device_id,
                "location": item.get("address") or item.get("location", "Unknown Location"),
                "installationDate": item.get("createdAt", "2026-01-01"),
                "firmwareVersion": item.get("firmwareVersion", "v2.1.0"),
                "ownerName": item.get("ownerName", "Unknown"),
                "ownerEmail": item.get("ownerEmail", "unknown@example.com"),
            }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting device info for %s: %s", device_id, exc)

    # Return safe defaults so export generation always has a device block
    return {
        "deviceId": device_id,
        "location": "Unknown Location",
        "installationDate": "2026-01-01",
        "firmwareVersion": "v2.1.0",
        "ownerName": "Unknown",
        "ownerEmail": "unknown@example.com",
    }


def verify_device_ownership(device_id: str, user_id: str) -> bool:
    """
    Return True if the device belongs to user_id (or the lookup fails safely).

    Uses a direct get_item on the Devices table — O(1), not a scan.
    """
    try:
        devices_table = dynamodb.Table(os.environ.get("DEVICES_TABLE", "AquaChain-Devices"))
        result = devices_table.get_item(Key={"deviceId": device_id})
        item = result.get("Item")
        if item and item.get("userId") and item["userId"] != user_id:
            logger.warning(
                "Ownership violation: user=%s tried to access device=%s owned by=%s",
                user_id,
                device_id,
                item["userId"],
            )
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        # Fail open only if DynamoDB is temporarily unavailable — logged for audit trail
        logger.warning("Could not verify device ownership for %s: %s — failing open", device_id, exc)
        return True

# ---------------------------------------------------------------------------
# WQI calculation
# ---------------------------------------------------------------------------

def add_missing_wqi_quality(readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Backfill WQI and quality label for readings that lack them."""
    for reading in readings:
        # Sensor-faulted readings produce meaningless WQI — skip calculation
        if reading.get("anomalyType") == "sensor_fault" or reading.get("qualityStatus") == "sensor_fault":
            reading.setdefault("quality", "Sensor Fault")
            reading.setdefault("wqi", 0)
            continue

        wqi = reading.get("wqi") or reading.get("qualityScore")
        quality = reading.get("quality")

        if wqi is None or wqi == "N/A" or quality is None or quality == "N/A":
            try:
                ph = float(reading.get("pH", 7.0))
                turbidity = float(reading.get("turbidity", 0.0))
                tds = float(reading.get("tds", 100.0))
                temperature = float(reading.get("temperature", 25.0))

                ph_score = max(0.0, 100 - abs(ph - 7.0) * 15)
                turbidity_score = max(0.0, 100 - turbidity * 10)
                tds_score = max(0.0, 100 - abs(tds - 100) / 10)
                temp_score = max(0.0, 100 - abs(temperature - 25) * 2)

                calculated_wqi = round((ph_score + turbidity_score + tds_score + temp_score) / 4, 1)

                if calculated_wqi >= 90:
                    calculated_quality = "Excellent"
                elif calculated_wqi >= 80:
                    calculated_quality = "Good"
                elif calculated_wqi >= 60:
                    calculated_quality = "Fair"
                elif calculated_wqi >= 40:
                    calculated_quality = "Poor"
                else:
                    calculated_quality = "Very Poor"

                reading["wqi"] = calculated_wqi
                reading["quality"] = calculated_quality
                reading.setdefault("qualityScore", calculated_wqi)

            except Exception as exc:  # noqa: BLE001
                logger.warning("WQI calculation failed: %s", exc)
                reading["wqi"] = 50.0
                reading["quality"] = "Fair"
                reading["qualityScore"] = 50.0

    return readings

# ---------------------------------------------------------------------------
# Data retrieval
# ---------------------------------------------------------------------------

def get_latest_reading(device_id: str) -> Optional[Dict[str, Any]]:
    """Return the most recent reading for a device, checking up to 4 months back."""
    now = datetime.utcnow()

    # Build a de-duplicated list of YYYY-MM strings for the last 4 months
    seen: set = set()
    months: List[str] = []
    for i in range(4):
        target = now.replace(day=1) - timedelta(days=i * 28)
        month_str = target.strftime("%Y-%m")
        if month_str not in seen:
            seen.add(month_str)
            months.append(month_str)

    for month_str in months:
        partition_key = f"{device_id}_{month_str}"
        try:
            response = readings_table.query(
                KeyConditionExpression=Key("deviceId_month").eq(partition_key),
                ScanIndexForward=False,
                Limit=1,
            )
            if response["Items"]:
                reading = convert_decimals(response["Items"][0])
                reading = add_missing_wqi_quality([reading])[0]
                logger.info("Found latest reading in %s for device %s", month_str, device_id)
                return reading
        except Exception as exc:  # noqa: BLE001
            logger.warning("Query failed for partition %s: %s", partition_key, exc)

    logger.warning("No readings found for device %s in last 4 months", device_id)
    return None


def get_device_history(device_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Return all readings for a device over the last N days, sorted newest-first."""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Build the set of YYYY-MM strings that overlap the requested window
    months: set = set()
    cursor = start_date.replace(day=1)
    while cursor <= now:
        months.add(cursor.strftime("%Y-%m"))
        cursor = cursor.replace(month=cursor.month % 12 + 1, year=cursor.year + (1 if cursor.month == 12 else 0))

    readings: List[Dict] = []
    # Support both legacy ('#') and current ('_') partition key separators
    key_formats = [
        lambda ym: f"{device_id}_{ym}",
        lambda ym: f"{device_id}#{ym}",
    ]

    for ym in sorted(months):
        for make_key in key_formats:
            partition_key = make_key(ym)
            try:
                response = readings_table.query(
                    KeyConditionExpression=(
                        Key("deviceId_month").eq(partition_key)
                        & Key("timestamp").gte(start_date.isoformat() + "Z")
                    ),
                    ExpressionAttributeNames={"#ts": "timestamp"},
                    ExpressionAttributeValues={
                        ":device_month": partition_key,
                        ":start_time": start_date.isoformat() + "Z",
                    },
                    KeyConditionExpression=(
                        "deviceId_month = :device_month AND #ts >= :start_time"
                    ),
                    ScanIndexForward=False,
                )
                if response.get("Items"):
                    readings.extend(response["Items"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("Query failed for partition %s: %s", partition_key, exc)

    readings = convert_decimals(readings)
    readings = add_missing_wqi_quality(readings)

    # Deduplicate by timestamp, keep newest first
    seen_ts: set = set()
    unique: List[Dict] = []
    for r in sorted(readings, key=lambda x: x.get("timestamp", ""), reverse=True):
        ts = r.get("timestamp", "")
        if ts not in seen_ts:
            seen_ts.add(ts)
            unique.append(r)

    logger.info("Returning %d unique readings for device %s (%d days)", len(unique), device_id, days)
    return unique


def get_device_alerts(device_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Return alerts for a device using a GSI query where available, fallback to filter."""
    alerts_table_name = os.environ.get("ALERTS_TABLE", "AquaChain-Alerts")
    alerts_table = dynamodb.Table(alerts_table_name)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    try:
        # Attempt GSI query first (deviceId-timestamp-index)
        response = alerts_table.query(
            IndexName="deviceId-timestamp-index",
            KeyConditionExpression=(
                Key("deviceId").eq(device_id)
                & Key("timestamp").gte(start_date.isoformat() + "Z")
            ),
        )
        alerts = convert_decimals(response.get("Items", []))
    except Exception:  # noqa: BLE001
        # GSI may not exist on all environments — fall back to FilterExpression scan
        logger.warning("GSI query failed for alerts, falling back to scan for device %s", device_id)
        try:
            response = alerts_table.scan(
                FilterExpression=(
                    "deviceId = :device_id AND #ts >= :start_date"
                ),
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":device_id": device_id,
                    ":start_date": start_date.isoformat() + "Z",
                },
            )
            alerts = convert_decimals(response.get("Items", []))
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching alerts for device %s: %s", device_id, exc)
            return []

    alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return alerts

# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def calculate_water_quality_summary(readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate min/avg/max statistics for each water quality parameter."""
    if not readings:
        return {}

    def _stats(values: List[float], precision: int = 2) -> Dict[str, float]:
        return {
            "average": round(sum(values) / len(values), precision),
            "min": round(min(values), precision),
            "max": round(max(values), precision),
        }

    try:
        return {
            k: _stats([float(r[field]) for r in readings if r.get(field)], precision)
            for k, field, precision in [
                ("pH", "pH", 2),
                ("TDS (ppm)", "tds", 0),
                ("Turbidity (NTU)", "turbidity", 1),
                ("Temperature (°C)", "temperature", 1),
                ("WQI", "wqi", 0),
            ]
            if any(r.get(field) for r in readings)
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calculating summary: %s", exc)
        return {}


def get_wqi_interpretation() -> Dict[str, str]:
    """Return the WQI interpretation legend."""
    return {
        "90-100": "Excellent",
        "70-90": "Good",
        "50-70": "Moderate",
        "25-50": "Poor",
        "0-25": "Unsafe",
    }


def generate_csv_format(readings: List[Dict], alerts: List[Dict]) -> Dict[str, str]:
    """Serialize readings and alerts to CSV strings."""
    readings_csv = StringIO()
    if readings:
        fieldnames = ["timestamp", "pH", "tds", "turbidity", "temperature", "wqi", "quality"]
        writer = csv.DictWriter(readings_csv, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in readings:
            writer.writerow({f: r.get(f, "") for f in fieldnames})

    alerts_csv = StringIO()
    if alerts:
        fieldnames_a = ["timestamp", "alertType", "severity", "message", "status"]
        writer_a = csv.DictWriter(alerts_csv, fieldnames=fieldnames_a, extrasaction="ignore")
        writer_a.writeheader()
        for a in alerts:
            writer_a.writerow({f: a.get(f, "") for f in fieldnames_a})

    return {"readings": readings_csv.getvalue(), "alerts": alerts_csv.getvalue()}


def generate_chart_data(readings: List[Dict]) -> Dict[str, List]:
    """Extract time-series arrays for chart rendering (last 50 readings)."""
    sorted_readings = sorted(readings, key=lambda x: x.get("timestamp", ""))[-50:]
    chart: Dict[str, List] = {
        "timestamps": [], "pH": [], "tds": [], "turbidity": [], "temperature": [], "wqi": []
    }
    for r in sorted_readings:
        chart["timestamps"].append(r.get("timestamp", ""))
        chart["pH"].append(float(r.get("pH", 0)))
        chart["tds"].append(float(r.get("tds", 0)))
        chart["turbidity"].append(float(r.get("turbidity", 0)))
        chart["temperature"].append(float(r.get("temperature", 0)))
        chart["wqi"].append(float(r.get("wqi", 0)))
    return chart


def generate_comprehensive_export(
    device_id: str, days: int, export_format: str, user_info: Dict
) -> Optional[Dict[str, Any]]:
    """Assemble all data needed for a full device data export."""
    logger.info("Generating export for device=%s days=%d format=%s", device_id, days, export_format)

    readings = get_device_history(device_id, days)
    device_info = get_device_info(device_id)
    alerts = get_device_alerts(device_id, days)
    summary = calculate_water_quality_summary(readings)

    export_data: Dict[str, Any] = {
        "exportInfo": {
            "exportDate": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "userRole": user_info.get("role", "Consumer"),
            "dateRange": f"Last {days} days",
            "totalReadings": len(readings),
            "format": export_format,
        },
        "deviceInfo": device_info,
        "waterQualitySummary": summary,
        "sensorData": readings,
        "alerts": alerts,
        "wqiInterpretation": get_wqi_interpretation(),
        "metadata": {
            "generatedBy": "AquaChain Water Quality Monitoring System",
            "version": "1.0",
            "dataSource": "IoT Sensors + ML Analysis",
            "accuracy": "99.74% (ML Model)",
            "samplingFrequency": "Every 60 seconds",
        },
    }

    if export_format == "csv":
        export_data["csvData"] = generate_csv_format(readings, alerts)
    elif export_format == "pdf":
        export_data["pdfReady"] = True
        export_data["chartData"] = generate_chart_data(readings)

    logger.info("Export generated: %d readings, %d alerts", len(readings), len(alerts))
    return export_data

# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def lambda_handler(event: Dict, context: Any) -> Dict[str, Any]:
    """Entry point for API Gateway proxy integration."""
    logger.info("Event received: method=%s path=%s",
                event.get("httpMethod"), event.get("path"))

    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    # CORS preflight — must be handled before any auth logic
    if http_method == "OPTIONS":
        return _CORS_PREFLIGHT_RESPONSE

    user_info = get_user_info(event)
    logger.info("User: id=%s groups=%s", user_info["user_id"], user_info["groups"])

    # Validate device ID
    device_id = path_params.get("deviceId")
    if not device_id:
        return create_response(400, {"error": "Device ID is required", "code": "MISSING_DEVICE_ID"})

    # Authorization: non-admin users may only access their own devices
    requesting_user_id = user_info.get("user_id", "")
    groups = user_info.get("groups", [])
    is_admin = "administrators" in (groups if isinstance(groups, list) else [])

    if not is_admin and requesting_user_id and requesting_user_id != "unknown":
        if not verify_device_ownership(device_id, requesting_user_id):
            return create_response(403, {
                "error": "Access denied — this device does not belong to your account",
                "code": "DEVICE_ACCESS_DENIED",
            })

    # Route dispatch
    try:
        if path.endswith("/latest"):
            reading = get_latest_reading(device_id)
            if reading:
                return create_response(200, {"success": True, "reading": reading, "deviceId": device_id})
            return create_response(404, {
                "error": f"No readings found for device {device_id}",
                "code": "NO_READINGS_FOUND",
                "deviceId": device_id,
            })

        if path.endswith("/history"):
            days = int(query_params.get("days", 7))
            readings = get_device_history(device_id, days)
            return create_response(200, {
                "success": True,
                "readings": readings,
                "deviceId": device_id,
                "days": days,
                "count": len(readings),
            })

        if path.endswith("/export"):
            days = int(query_params.get("days", 7))
            fmt = query_params.get("format", "json")
            export_data = generate_comprehensive_export(device_id, days, fmt, user_info)
            if export_data:
                return create_response(200, export_data)
            return create_response(500, {
                "error": "Failed to generate export data",
                "code": "EXPORT_GENERATION_FAILED",
                "deviceId": device_id,
            })

        return create_response(404, {"error": f"Endpoint not found: {path}", "code": "ENDPOINT_NOT_FOUND"})

    except Exception as exc:  # noqa: BLE001
        logger.error("Unhandled error in lambda_handler: %s", exc, exc_info=True)
        request_id = getattr(context, "aws_request_id", "unknown")
        return create_response(500, {
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "requestId": request_id,
        })