# AquaChain Load Testing Framework

This directory contains comprehensive load testing tools for the AquaChain system, designed to validate performance under production-scale loads and ensure SLA compliance.

## Test Categories

### 1. IoT Data Ingestion Load Tests
- **File**: `test_iot_ingestion_load.py`
- **Purpose**: Test IoT data processing pipeline under concurrent device load
- **Scenarios**: 1000 concurrent devices, burst traffic, sustained load

### 2. API Load Tests
- **File**: `test_api_load.py`
- **Purpose**: Test REST API performance with realistic user patterns
- **Scenarios**: Consumer dashboard access, technician workflows, admin operations

### 3. Database Performance Tests
- **File**: `test_database_load.py`
- **Purpose**: Test DynamoDB performance under concurrent read/write operations
- **Scenarios**: Time-series queries, ledger writes, concurrent access patterns

### 4. End-to-End Latency Tests
- **File**: `test_e2e_latency.py`
- **Purpose**: Test complete alert delivery pipeline latency
- **Scenarios**: Critical event detection to notification delivery

### 5. Load Test Orchestrator
- **File**: `load_test_orchestrator.py`
- **Purpose**: Coordinate and execute all load tests with reporting

## Usage

```bash
# Run all load tests
python tests/load/load_test_orchestrator.py

# Run specific test category
python tests/load/test_iot_ingestion_load.py

# Run with custom parameters
python tests/load/test_api_load.py --concurrent-users 500 --duration 300
```

## Requirements

- Python 3.11+
- boto3
- requests
- concurrent.futures
- statistics
- matplotlib (for reporting)
- locust (for advanced load testing)