"""
OpenAPI specification generator for AquaChain API
Generates comprehensive API documentation
"""
import json
from typing import Dict, Any


def generate_openapi_spec() -> Dict[str, Any]:
    """Generate complete OpenAPI 3.0 specification for AquaChain API"""
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "AquaChain Water Quality Monitoring API",
            "description": "REST API for AquaChain water quality monitoring system with real-time IoT data processing, ML-powered analytics, and service management",
            "version": "1.0.0",
            "contact": {
                "name": "AquaChain API Support",
                "email": "api-support@aquachain.io"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.aquachain.io/v1",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.aquachain.io/v1",
                "description": "Staging server"
            }
        ],
        "security": [
            {
                "CognitoAuth": []
            }
        ],
        "components": {
            "securitySchemes": {
                "CognitoAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "AWS Cognito JWT token"
                }
            },
            "schemas": get_schemas(),
            "responses": get_common_responses(),
            "parameters": get_common_parameters()
        },
        "paths": get_api_paths(),
        "tags": [
            {
                "name": "readings",
                "description": "Water quality readings and historical data"
            },
            {
                "name": "service-requests",
                "description": "Service request management"
            },
            {
                "name": "users",
                "description": "User management and profiles"
            },
            {
                "name": "technicians",
                "description": "Technician management and availability"
            },
            {
                "name": "analytics",
                "description": "System analytics and reporting"
            },
            {
                "name": "audit",
                "description": "Audit trail and compliance"
            }
        ]
    }
    
    return spec


def get_schemas() -> Dict[str, Any]:
    """Define data schemas for API"""
    return {
        "WaterQualityReading": {
            "type": "object",
            "required": ["deviceId", "timestamp", "readings", "wqi"],
            "properties": {
                "deviceId": {
                    "type": "string",
                    "description": "Unique device identifier",
                    "example": "DEV-3421"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Reading timestamp in ISO 8601 format",
                    "example": "2025-10-19T14:23:45.123Z"
                },
                "readings": {
                    "$ref": "#/components/schemas/SensorReadings"
                },
                "wqi": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Water Quality Index (0-100)",
                    "example": 78.5
                },
                "anomalyType": {
                    "type": "string",
                    "enum": ["normal", "sensor_fault", "contamination"],
                    "description": "ML-detected anomaly classification",
                    "example": "normal"
                },
                "location": {
                    "$ref": "#/components/schemas/Location"
                }
            }
        },
        "SensorReadings": {
            "type": "object",
            "required": ["pH", "turbidity", "tds", "temperature", "humidity"],
            "properties": {
                "pH": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 14,
                    "description": "pH level (0-14)",
                    "example": 7.2
                },
                "turbidity": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Turbidity in NTU",
                    "example": 1.5
                },
                "tds": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Total Dissolved Solids in ppm",
                    "example": 145
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature in Celsius",
                    "example": 24.5
                },
                "humidity": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Humidity percentage",
                    "example": 68.2
                }
            }
        },
        "Location": {
            "type": "object",
            "required": ["latitude", "longitude"],
            "properties": {
                "latitude": {
                    "type": "number",
                    "minimum": -90,
                    "maximum": 90,
                    "description": "Latitude coordinate",
                    "example": 9.9312
                },
                "longitude": {
                    "type": "number",
                    "minimum": -180,
                    "maximum": 180,
                    "description": "Longitude coordinate",
                    "example": 76.2673
                },
                "address": {
                    "type": "string",
                    "description": "Human-readable address",
                    "example": "123 Main St, Kochi, Kerala, India"
                }
            }
        },
        "ServiceRequest": {
            "type": "object",
            "required": ["requestId", "consumerId", "deviceId", "status", "location"],
            "properties": {
                "requestId": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Unique service request identifier",
                    "example": "550e8400-e29b-41d4-a716-446655440000"
                },
                "consumerId": {
                    "type": "string",
                    "description": "Consumer user ID",
                    "example": "user-123"
                },
                "technicianId": {
                    "type": "string",
                    "description": "Assigned technician ID",
                    "example": "tech-456"
                },
                "deviceId": {
                    "type": "string",
                    "description": "Device requiring service",
                    "example": "DEV-3421"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "assigned", "accepted", "en_route", "in_progress", "completed", "cancelled"],
                    "description": "Current request status",
                    "example": "assigned"
                },
                "location": {
                    "$ref": "#/components/schemas/Location"
                },
                "issueDescription": {
                    "type": "string",
                    "description": "Description of the issue",
                    "example": "Device showing offline status"
                },
                "estimatedArrival": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Estimated technician arrival time",
                    "example": "2025-10-19T15:30:00Z"
                },
                "notes": {
                    "type": "array",
                    "items": {
                        "$ref": "#/components/schemas/ServiceNote"
                    }
                },
                "createdAt": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Request creation timestamp",
                    "example": "2025-10-19T14:23:45Z"
                },
                "completedAt": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Request completion timestamp",
                    "example": "2025-10-19T16:45:30Z"
                },
                "customerRating": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Customer satisfaction rating (1-5)",
                    "example": 4.5
                }
            }
        },
        "ServiceNote": {
            "type": "object",
            "required": ["timestamp", "author", "type", "content"],
            "properties": {
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Note timestamp",
                    "example": "2025-10-19T15:00:00Z"
                },
                "author": {
                    "type": "string",
                    "description": "Note author ID",
                    "example": "tech-456"
                },
                "type": {
                    "type": "string",
                    "enum": ["status_update", "technician_note", "customer_feedback"],
                    "description": "Type of note",
                    "example": "status_update"
                },
                "content": {
                    "type": "string",
                    "description": "Note content",
                    "example": "Arrived at location, beginning diagnostics"
                }
            }
        },
        "UserProfile": {
            "type": "object",
            "required": ["userId", "email", "role"],
            "properties": {
                "userId": {
                    "type": "string",
                    "description": "Unique user identifier",
                    "example": "user-123"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User email address",
                    "example": "user@example.com"
                },
                "role": {
                    "type": "string",
                    "enum": ["consumer", "technician", "administrator"],
                    "description": "User role",
                    "example": "consumer"
                },
                "profile": {
                    "$ref": "#/components/schemas/UserProfileData"
                },
                "deviceIds": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Associated device IDs",
                    "example": ["DEV-3421", "DEV-3422"]
                },
                "preferences": {
                    "$ref": "#/components/schemas/UserPreferences"
                }
            }
        },
        "UserProfileData": {
            "type": "object",
            "properties": {
                "firstName": {
                    "type": "string",
                    "example": "John"
                },
                "lastName": {
                    "type": "string",
                    "example": "Doe"
                },
                "phone": {
                    "type": "string",
                    "example": "+1-555-123-4567"
                },
                "address": {
                    "$ref": "#/components/schemas/Location"
                }
            }
        },
        "UserPreferences": {
            "type": "object",
            "properties": {
                "notifications": {
                    "type": "object",
                    "properties": {
                        "push": {
                            "type": "boolean",
                            "example": true
                        },
                        "sms": {
                            "type": "boolean",
                            "example": true
                        },
                        "email": {
                            "type": "boolean",
                            "example": false
                        }
                    }
                },
                "theme": {
                    "type": "string",
                    "enum": ["light", "dark", "auto"],
                    "example": "auto"
                },
                "language": {
                    "type": "string",
                    "example": "en"
                }
            }
        },
        "AnalyticsResponse": {
            "type": "object",
            "properties": {
                "timeRange": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "end": {
                            "type": "string",
                            "format": "date-time"
                        }
                    }
                },
                "metrics": {
                    "type": "object",
                    "description": "Analytics metrics data"
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "required": ["error", "message"],
            "properties": {
                "error": {
                    "type": "string",
                    "description": "Error type",
                    "example": "Bad Request"
                },
                "message": {
                    "type": "string",
                    "description": "Error message",
                    "example": "Invalid request parameters"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Error timestamp",
                    "example": "2025-10-19T14:23:45Z"
                },
                "requestId": {
                    "type": "string",
                    "description": "Request identifier for debugging",
                    "example": "req-123456"
                }
            }
        }
    }


def get_common_responses() -> Dict[str, Any]:
    """Define common API responses"""
    return {
        "BadRequest": {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        },
        "Unauthorized": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        },
        "Forbidden": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        },
        "NotFound": {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        },
        "TooManyRequests": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        },
        "InternalServerError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
                }
            }
        }
    }


def get_common_parameters() -> Dict[str, Any]:
    """Define common API parameters"""
    return {
        "DeviceId": {
            "name": "deviceId",
            "in": "path",
            "required": True,
            "schema": {
                "type": "string"
            },
            "description": "Device identifier",
            "example": "DEV-3421"
        },
        "RequestId": {
            "name": "requestId",
            "in": "path",
            "required": True,
            "schema": {
                "type": "string",
                "format": "uuid"
            },
            "description": "Service request identifier"
        },
        "Days": {
            "name": "days",
            "in": "query",
            "schema": {
                "type": "integer",
                "minimum": 1,
                "maximum": 90,
                "default": 7
            },
            "description": "Number of days of historical data"
        },
        "Limit": {
            "name": "limit",
            "in": "query",
            "schema": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            },
            "description": "Maximum number of results"
        },
        "StartDate": {
            "name": "startDate",
            "in": "query",
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "description": "Start date for data range"
        },
        "EndDate": {
            "name": "endDate",
            "in": "query",
            "schema": {
                "type": "string",
                "format": "date-time"
            },
            "description": "End date for data range"
        }
    }


def get_api_paths() -> Dict[str, Any]:
    """Define API paths and operations"""
    return {
        "/readings/{deviceId}": {
            "get": {
                "tags": ["readings"],
                "summary": "Get device readings",
                "description": "Retrieve water quality readings for a specific device",
                "parameters": [
                    {"$ref": "#/components/parameters/DeviceId"},
                    {"$ref": "#/components/parameters/Days"},
                    {"$ref": "#/components/parameters/Limit"},
                    {"$ref": "#/components/parameters/StartDate"},
                    {"$ref": "#/components/parameters/EndDate"}
                ],
                "responses": {
                    "200": {
                        "description": "Device readings retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "deviceId": {"type": "string"},
                                        "readings": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/WaterQualityReading"}
                                        },
                                        "count": {"type": "integer"},
                                        "summary": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/readings": {
            "get": {
                "tags": ["readings"],
                "summary": "Get user readings",
                "description": "Retrieve readings for all user's devices",
                "parameters": [
                    {"$ref": "#/components/parameters/Days"},
                    {
                        "name": "latest",
                        "in": "query",
                        "schema": {"type": "boolean", "default": false},
                        "description": "Return only latest reading per device"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "User readings retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "devices": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "deviceId": {"type": "string"},
                                                    "readings": {
                                                        "type": "array",
                                                        "items": {"$ref": "#/components/schemas/WaterQualityReading"}
                                                    }
                                                }
                                            }
                                        },
                                        "totalDevices": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            },
            "post": {
                "tags": ["readings"],
                "summary": "Create reading (Admin only)",
                "description": "Manually create a water quality reading",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WaterQualityReading"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Reading created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "reading": {"$ref": "#/components/schemas/WaterQualityReading"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/service-requests": {
            "get": {
                "tags": ["service-requests"],
                "summary": "Get service requests",
                "description": "Retrieve service requests for the authenticated user",
                "parameters": [
                    {
                        "name": "status",
                        "in": "query",
                        "schema": {
                            "type": "string",
                            "enum": ["pending", "assigned", "accepted", "en_route", "in_progress", "completed", "cancelled"]
                        },
                        "description": "Filter by status"
                    },
                    {"$ref": "#/components/parameters/Limit"},
                    {"$ref": "#/components/parameters/Days"}
                ],
                "responses": {
                    "200": {
                        "description": "Service requests retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "serviceRequests": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/ServiceRequest"}
                                        },
                                        "count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            },
            "post": {
                "tags": ["service-requests"],
                "summary": "Create service request",
                "description": "Create a new service request",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["deviceId", "location", "issueDescription"],
                                "properties": {
                                    "deviceId": {"type": "string"},
                                    "location": {"$ref": "#/components/schemas/Location"},
                                    "issueDescription": {"type": "string"},
                                    "priority": {
                                        "type": "string",
                                        "enum": ["low", "normal", "high", "urgent"],
                                        "default": "normal"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Service request created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "serviceRequest": {"$ref": "#/components/schemas/ServiceRequest"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/service-requests/{requestId}": {
            "get": {
                "tags": ["service-requests"],
                "summary": "Get service request",
                "description": "Retrieve a specific service request",
                "parameters": [
                    {"$ref": "#/components/parameters/RequestId"}
                ],
                "responses": {
                    "200": {
                        "description": "Service request retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "serviceRequest": {"$ref": "#/components/schemas/ServiceRequest"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            },
            "put": {
                "tags": ["service-requests"],
                "summary": "Update service request",
                "description": "Update service request status or add notes",
                "parameters": [
                    {"$ref": "#/components/parameters/RequestId"}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {
                                        "type": "string",
                                        "enum": ["accepted", "en_route", "in_progress", "completed", "cancelled"]
                                    },
                                    "note": {"type": "string"},
                                    "noteType": {
                                        "type": "string",
                                        "enum": ["status_update", "technician_note", "customer_feedback"]
                                    },
                                    "completionData": {
                                        "type": "object",
                                        "properties": {
                                            "customerRating": {
                                                "type": "number",
                                                "minimum": 1,
                                                "maximum": 5
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Service request updated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "requestId": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/analytics/{type}": {
            "get": {
                "tags": ["analytics"],
                "summary": "Get analytics data",
                "description": "Retrieve system analytics and metrics",
                "parameters": [
                    {
                        "name": "type",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": ["dashboard", "compliance", "performance", "water-quality", "service-metrics"]
                        },
                        "description": "Analytics type"
                    },
                    {"$ref": "#/components/parameters/Days"},
                    {"$ref": "#/components/parameters/StartDate"},
                    {"$ref": "#/components/parameters/EndDate"}
                ],
                "responses": {
                    "200": {
                        "description": "Analytics data retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AnalyticsResponse"}
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        }
    }


def save_openapi_spec(file_path: str = "openapi.json"):
    """Save OpenAPI specification to file"""
    spec = generate_openapi_spec()
    with open(file_path, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"OpenAPI specification saved to {file_path}")


if __name__ == "__main__":
    save_openapi_spec()