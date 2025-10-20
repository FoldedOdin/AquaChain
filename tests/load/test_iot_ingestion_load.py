"""
IoT Data Ingestion Load Testing for AquaChain
Tests the complete IoT data processing pipeline under concurrent device load
"""

import asyncio
import json
import time
import uuid
import boto3
import statistics
import concurrent.futures
from datetime import datetime, timezone
from typing import List, Dict, Tuple
import argparse
import random
import threading
from dataclasses import dataclass

@dataclass
class LoadTestResult:
    """Results from a load test execution."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    requests_per_second: float
    error_rate: float
    duration: float

class IoTDataGenerator:
    """Generate realistic IoT sensor data for load testing."""
    
    def __init__(self):
        self.device_locations = [
            {"latitude": 9.9312, "longitude": 76.2673, "city": "Kochi"},
            {"latitude": 12.9716, "longitude": 77.5946, "city": "Bangalore"},
            {"latitude": 13.0827, "longitude": 80.2707, "city": "Chennai"},
            {"latitude": 19.0760, "longitude": 72.8777, "city": "Mumbai"},
            {"latitude": 28.7041, "longitude": 77.1025, "city": "Delhi"}
        ]
    
    def generate_device_data(self, device_id: str, anomaly_probability: float = 0.05) -> Dict:
        """Generate realistic sensor data for a device."""
        location = random.choice(self.device_locations)
        
        # Determine if this should be an anomaly
        is_anomaly = random.random() < anomaly_probability
        
        if is_anomaly:
            # Generate anomalous readings
            readings = {
                "pH": random.choice([random.uniform(3.0, 5.0), random.uniform(9.5, 12.0)]),
                "turbidity": random.uniform(50.0, 200.0),
                "tds": random.uniform(2000, 5000),
                "temperature": random.uniform(15.0, 35.0),
                "humidity": random.uniform(30.0, 90.0)
            }
        else:
            # Generate normal readings
            readings = {
                "pH": random.uniform(6.5, 8.5),
                "turbidity": random.uniform(0.5, 5.0),
                "tds": random.uniform(100, 500),
                "temperature": random.uniform(20.0, 30.0),
                "humidity": random.uniform(50.0, 80.0)
            }
        
        return {
            "deviceId": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": location,
            "readings": readings,
            "diagnostics": {
                "batteryLevel": random.randint(20, 100),
                "signalStrength": random.randint(-90, -30),
                "sensorStatus": "normal" if not is_anomaly else "warning"
            }
        }

class IoTIngestionLoadTester:
    """Load tester for IoT data ingestion pipeline."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.iot_client = boto3.client('iot-data', region_name=aws_region)
        self.lambda_client = boto3.client('lambda', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.data_generator = IoTDataGenerator()
        
        # Test configuration
        self.iot_topic_prefix = "aquachain"
        self.processing_function_name = "AquaChain-data-processing"
        
        # Metrics collection
        self.response_times = []
        self.errors = []
        self.lock = threading.Lock()
    
    def publish_iot_message(self, device_id: str, data: Dict) -> Tuple[bool, float]:
        """Publish a single IoT message and measure response time."""
        topic = f"{self.iot_topic_prefix}/{device_id}/data"
        
        start_time = time.time()
        try:
            response = self.iot_client.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(data)
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            return True, response_time
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            with self.lock:
                self.errors.append(str(e))
            
            return False, response_time
    
    def simulate_device_batch(self, device_ids: List[str], duration: int, 
                            messages_per_minute: int = 2) -> List[Tuple[bool, float]]:
        """Simulate a batch of devices sending data for specified duration."""
        results = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            batch_results = []
            
            # Send messages from all devices in this batch
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(device_ids)) as executor:
                futures = []
                
                for device_id in device_ids:
                    data = self.data_generator.generate_device_data(device_id)
                    future = executor.submit(self.publish_iot_message, device_id, data)
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures):
                    success, response_time = future.result()
                    batch_results.append((success, response_time))
            
            results.extend(batch_results)
            
            # Wait before next batch (simulate device transmission interval)
            sleep_time = 60.0 / messages_per_minute
            time.sleep(sleep_time)
        
        return results
    
    def run_concurrent_device_test(self, num_devices: int, duration: int, 
                                 messages_per_minute: int = 2) -> LoadTestResult:
        """Run load test with concurrent devices."""
        print(f"🚀 Starting IoT ingestion load test:")
        print(f"   Devices: {num_devices}")
        print(f"   Duration: {duration} seconds")
        print(f"   Messages per device per minute: {messages_per_minute}")
        
        # Generate device IDs
        device_ids = [f"LOAD-TEST-{i:04d}" for i in range(num_devices)]
        
        # Split devices into batches for concurrent execution
        batch_size = min(50, num_devices)  # Limit batch size to avoid overwhelming
        device_batches = [device_ids[i:i + batch_size] 
                         for i in range(0, len(device_ids), batch_size)]
        
        start_time = time.time()
        all_results = []
        
        # Execute batches concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(device_batches)) as executor:
            futures = []
            
            for batch in device_batches:
                future = executor.submit(
                    self.simulate_device_batch, 
                    batch, 
                    duration, 
                    messages_per_minute
                )
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                batch_results = future.result()
                all_results.extend(batch_results)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate metrics
        successful_requests = sum(1 for success, _ in all_results if success)
        failed_requests = len(all_results) - successful_requests
        response_times = [rt for _, rt in all_results]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        requests_per_second = len(all_results) / actual_duration if actual_duration > 0 else 0
        error_rate = (failed_requests / len(all_results)) * 100 if all_results else 0
        
        return LoadTestResult(
            total_requests=len(all_results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            duration=actual_duration
        )
    
    def run_burst_traffic_test(self, peak_devices: int, burst_duration: int = 60) -> LoadTestResult:
        """Test system behavior under sudden traffic bursts."""
        print(f"💥 Starting burst traffic test:")
        print(f"   Peak devices: {peak_devices}")
        print(f"   Burst duration: {burst_duration} seconds")
        
        # Generate burst of messages
        device_ids = [f"BURST-TEST-{i:04d}" for i in range(peak_devices)]
        
        start_time = time.time()
        results = []
        
        # Send burst of messages simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=peak_devices) as executor:
            futures = []
            
            for device_id in device_ids:
                data = self.data_generator.generate_device_data(device_id, anomaly_probability=0.1)
                future = executor.submit(self.publish_iot_message, device_id, data)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                success, response_time = future.result()
                results.append((success, response_time))
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate metrics
        successful_requests = sum(1 for success, _ in results if success)
        failed_requests = len(results) - successful_requests
        response_times = [rt for _, rt in results]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        requests_per_second = len(results) / actual_duration if actual_duration > 0 else 0
        error_rate = (failed_requests / len(results)) * 100 if results else 0
        
        return LoadTestResult(
            total_requests=len(results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            duration=actual_duration
        )
    
    def validate_sla_requirements(self, result: LoadTestResult) -> Dict[str, bool]:
        """Validate load test results against SLA requirements."""
        validations = {}
        
        # Requirement 11.1: 99.5% uptime (error rate < 0.5%)
        validations['error_rate_sla'] = result.error_rate < 0.5
        
        # Requirement 11.2: 95th percentile response time < 500ms for IoT ingestion
        validations['response_time_sla'] = result.p95_response_time < 500
        
        # Requirement 11.3: System should handle 1000 concurrent devices
        validations['concurrent_devices_sla'] = result.successful_requests > 0
        
        # Requirement 11.4: Requests per second should meet minimum throughput
        validations['throughput_sla'] = result.requests_per_second > 10  # Minimum 10 RPS
        
        return validations
    
    def print_results(self, result: LoadTestResult, test_name: str):
        """Print formatted load test results."""
        print(f"\n📊 {test_name} Results:")
        print(f"   Total Requests: {result.total_requests}")
        print(f"   Successful: {result.successful_requests}")
        print(f"   Failed: {result.failed_requests}")
        print(f"   Error Rate: {result.error_rate:.2f}%")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Requests/sec: {result.requests_per_second:.2f}")
        print(f"   Avg Response Time: {result.avg_response_time:.2f}ms")
        print(f"   95th Percentile: {result.p95_response_time:.2f}ms")
        print(f"   99th Percentile: {result.p99_response_time:.2f}ms")
        print(f"   Max Response Time: {result.max_response_time:.2f}ms")
        
        # SLA validation
        validations = self.validate_sla_requirements(result)
        print(f"\n✅ SLA Validation:")
        for sla_name, passed in validations.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {sla_name}: {status}")

def main():
    """Main function to run IoT ingestion load tests."""
    parser = argparse.ArgumentParser(description='AquaChain IoT Ingestion Load Testing')
    parser.add_argument('--devices', type=int, default=100, 
                       help='Number of concurrent devices (default: 100)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Test duration in seconds (default: 300)')
    parser.add_argument('--messages-per-minute', type=int, default=2, 
                       help='Messages per device per minute (default: 2)')
    parser.add_argument('--burst-devices', type=int, default=500, 
                       help='Number of devices for burst test (default: 500)')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    try:
        tester = IoTIngestionLoadTester(aws_region=args.aws_region)
        
        print("🔬 AquaChain IoT Ingestion Load Testing")
        print("=" * 50)
        
        # Test 1: Concurrent devices sustained load
        concurrent_result = tester.run_concurrent_device_test(
            num_devices=args.devices,
            duration=args.duration,
            messages_per_minute=args.messages_per_minute
        )
        tester.print_results(concurrent_result, "Concurrent Devices Test")
        
        # Test 2: Burst traffic test
        burst_result = tester.run_burst_traffic_test(
            peak_devices=args.burst_devices
        )
        tester.print_results(burst_result, "Burst Traffic Test")
        
        # Overall assessment
        print("\n🎯 Overall Assessment:")
        concurrent_validations = tester.validate_sla_requirements(concurrent_result)
        burst_validations = tester.validate_sla_requirements(burst_result)
        
        all_passed = all(concurrent_validations.values()) and all(burst_validations.values())
        
        if all_passed:
            print("✅ All SLA requirements met!")
            return 0
        else:
            print("❌ Some SLA requirements failed!")
            return 1
            
    except Exception as e:
        print(f"💥 Load test failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())