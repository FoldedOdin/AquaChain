"""
API Load Testing for AquaChain
Tests REST API performance with realistic user patterns and concurrent access
"""

import requests
import json
import time
import uuid
import statistics
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
import argparse
import random
import threading
from dataclasses import dataclass

@dataclass
class APILoadTestResult:
    """Results from an API load test execution."""
    endpoint: str
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
    status_code_distribution: Dict[int, int]
    duration: float

class UserSimulator:
    """Simulate realistic user behavior patterns."""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AquaChain-LoadTest/1.0'
        })
    
    def simulate_consumer_workflow(self, user_id: str, device_id: str, duration: int) -> List[Tuple[str, bool, float, int]]:
        """Simulate a consumer user's typical workflow."""
        results = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Consumer workflow: Check dashboard -> View history -> Maybe request service
            workflow_actions = [
                ('GET', f'/api/v1/readings/{device_id}', None),
                ('GET', f'/api/v1/readings/{device_id}/history?days=7', None),
                ('GET', f'/api/v1/users/{user_id}/profile', None)
            ]
            
            # 10% chance to request service
            if random.random() < 0.1:
                service_request = {
                    'deviceId': device_id,
                    'issueDescription': 'Water quality alert - need technician check',
                    'priority': 'normal'
                }
                workflow_actions.append(('POST', '/api/v1/service-requests', service_request))
            
            for method, endpoint, data in workflow_actions:
                success, response_time, status_code = self._make_request(method, endpoint, data)
                results.append((endpoint, success, response_time, status_code))
                
                # Realistic delay between actions
                time.sleep(random.uniform(1, 5))
            
            # Longer delay before next workflow cycle
            time.sleep(random.uniform(30, 120))
        
        return results
    
    def simulate_technician_workflow(self, technician_id: str, duration: int) -> List[Tuple[str, bool, float, int]]:
        """Simulate a technician user's typical workflow."""
        results = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Technician workflow: Check assignments -> Update status -> View device details
            workflow_actions = [
                ('GET', f'/api/v1/technicians/{technician_id}/assignments', None),
                ('GET', f'/api/v1/service-requests?technician={technician_id}&status=assigned', None)
            ]
            
            # 30% chance to update service request status
            if random.random() < 0.3:
                status_update = {
                    'status': random.choice(['accepted', 'en_route', 'in_progress', 'completed']),
                    'notes': 'Status updated via load test',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                request_id = f'req-{random.randint(1000, 9999)}'
                workflow_actions.append(('PUT', f'/api/v1/service-requests/{request_id}/status', status_update))
            
            for method, endpoint, data in workflow_actions:
                success, response_time, status_code = self._make_request(method, endpoint, data)
                results.append((endpoint, success, response_time, status_code))
                
                # Realistic delay between actions
                time.sleep(random.uniform(2, 8))
            
            # Longer delay before next workflow cycle
            time.sleep(random.uniform(60, 300))
        
        return results
    
    def simulate_admin_workflow(self, admin_id: str, duration: int) -> List[Tuple[str, bool, float, int]]:
        """Simulate an admin user's typical workflow."""
        results = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Admin workflow: System monitoring -> User management -> Reports
            workflow_actions = [
                ('GET', '/api/v1/admin/system/health', None),
                ('GET', '/api/v1/admin/metrics/alerts?period=24h', None),
                ('GET', '/api/v1/admin/users?limit=50', None),
                ('GET', '/api/v1/admin/devices?status=all&limit=100', None),
                ('GET', '/api/v1/admin/reports/compliance?startDate=2025-10-01&endDate=2025-10-20', None)
            ]
            
            for method, endpoint, data in workflow_actions:
                success, response_time, status_code = self._make_request(method, endpoint, data)
                results.append((endpoint, success, response_time, status_code))
                
                # Realistic delay between actions
                time.sleep(random.uniform(3, 10))
            
            # Longer delay before next workflow cycle
            time.sleep(random.uniform(120, 600))
        
        return results
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, float, int]:
        """Make HTTP request and measure response time."""
        url = f"{self.api_base_url}{endpoint}"
        
        start_time = time.time()
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=30)
            elif method == 'PUT':
                response = self.session.put(url, json=data, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Consider 2xx and 3xx as successful, 4xx as expected (auth errors), 5xx as failures
            success = response.status_code < 500
            
            return success, response_time, response.status_code
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return False, response_time, 0  # 0 indicates network/timeout error

class APILoadTester:
    """Load tester for AquaChain REST API."""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.lock = threading.Lock()
    
    def run_endpoint_load_test(self, endpoint: str, method: str = 'GET', 
                             concurrent_users: int = 50, duration: int = 300,
                             data: Optional[Dict] = None) -> APILoadTestResult:
        """Run load test against a specific endpoint."""
        print(f"🎯 Testing endpoint: {method} {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Duration: {duration} seconds")
        
        results = []
        status_codes = {}
        
        def worker():
            simulator = UserSimulator(self.api_base_url)
            end_time = time.time() + duration
            
            while time.time() < end_time:
                success, response_time, status_code = simulator._make_request(method, endpoint, data)
                
                with self.lock:
                    results.append((success, response_time, status_code))
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                
                # Small delay between requests
                time.sleep(random.uniform(0.1, 1.0))
        
        start_time = time.time()
        
        # Start concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent_users)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate metrics
        successful_requests = sum(1 for success, _, _ in results if success)
        failed_requests = len(results) - successful_requests
        response_times = [rt for _, rt, _ in results]
        
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
        
        return APILoadTestResult(
            endpoint=endpoint,
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
            status_code_distribution=status_codes,
            duration=actual_duration
        )
    
    def run_user_workflow_test(self, concurrent_users: int = 30, duration: int = 300) -> Dict[str, APILoadTestResult]:
        """Run load test simulating realistic user workflows."""
        print(f"👥 Testing user workflows:")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Duration: {duration} seconds")
        
        # Distribute users across different roles
        consumer_users = int(concurrent_users * 0.7)  # 70% consumers
        technician_users = int(concurrent_users * 0.25)  # 25% technicians
        admin_users = max(1, concurrent_users - consumer_users - technician_users)  # 5% admins
        
        all_results = []
        
        def run_consumer_workflow():
            user_id = f"consumer-{uuid.uuid4().hex[:8]}"
            device_id = f"device-{random.randint(1000, 9999)}"
            simulator = UserSimulator(self.api_base_url)
            return simulator.simulate_consumer_workflow(user_id, device_id, duration)
        
        def run_technician_workflow():
            technician_id = f"tech-{uuid.uuid4().hex[:8]}"
            simulator = UserSimulator(self.api_base_url)
            return simulator.simulate_technician_workflow(technician_id, duration)
        
        def run_admin_workflow():
            admin_id = f"admin-{uuid.uuid4().hex[:8]}"
            simulator = UserSimulator(self.api_base_url)
            return simulator.simulate_admin_workflow(admin_id, duration)
        
        start_time = time.time()
        
        # Start all user workflows concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit consumer workflows
            for _ in range(consumer_users):
                futures.append(executor.submit(run_consumer_workflow))
            
            # Submit technician workflows
            for _ in range(technician_users):
                futures.append(executor.submit(run_technician_workflow))
            
            # Submit admin workflows
            for _ in range(admin_users):
                futures.append(executor.submit(run_admin_workflow))
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                workflow_results = future.result()
                all_results.extend(workflow_results)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Group results by endpoint
        endpoint_results = {}
        for endpoint, success, response_time, status_code in all_results:
            if endpoint not in endpoint_results:
                endpoint_results[endpoint] = []
            endpoint_results[endpoint].append((success, response_time, status_code))
        
        # Calculate metrics for each endpoint
        results_by_endpoint = {}
        for endpoint, endpoint_data in endpoint_results.items():
            successful_requests = sum(1 for success, _, _ in endpoint_data if success)
            failed_requests = len(endpoint_data) - successful_requests
            response_times = [rt for _, rt, _ in endpoint_data]
            status_codes = {}
            
            for _, _, status_code in endpoint_data:
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]
                p99_response_time = statistics.quantiles(response_times, n=100)[98]
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = p95_response_time = p99_response_time = 0
                max_response_time = min_response_time = 0
            
            requests_per_second = len(endpoint_data) / actual_duration if actual_duration > 0 else 0
            error_rate = (failed_requests / len(endpoint_data)) * 100 if endpoint_data else 0
            
            results_by_endpoint[endpoint] = APILoadTestResult(
                endpoint=endpoint,
                total_requests=len(endpoint_data),
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time=avg_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                max_response_time=max_response_time,
                min_response_time=min_response_time,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                status_code_distribution=status_codes,
                duration=actual_duration
            )
        
        return results_by_endpoint
    
    def validate_sla_requirements(self, result: APILoadTestResult) -> Dict[str, bool]:
        """Validate API load test results against SLA requirements."""
        validations = {}
        
        # Requirement 11.5: 95th percentile API response time < 500ms
        validations['response_time_sla'] = result.p95_response_time < 500
        
        # Error rate should be low (excluding expected 4xx responses)
        server_errors = sum(count for status_code, count in result.status_code_distribution.items() 
                          if status_code >= 500)
        server_error_rate = (server_errors / result.total_requests) * 100 if result.total_requests > 0 else 0
        validations['server_error_rate_sla'] = server_error_rate < 1.0  # Less than 1% server errors
        
        # Minimum throughput requirement
        validations['throughput_sla'] = result.requests_per_second > 5  # Minimum 5 RPS per endpoint
        
        return validations
    
    def print_results(self, result: APILoadTestResult, test_name: str):
        """Print formatted API load test results."""
        print(f"\n📊 {test_name} Results:")
        print(f"   Endpoint: {result.endpoint}")
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
        
        # Status code distribution
        print(f"   Status Code Distribution:")
        for status_code, count in sorted(result.status_code_distribution.items()):
            percentage = (count / result.total_requests) * 100
            print(f"     {status_code}: {count} ({percentage:.1f}%)")
        
        # SLA validation
        validations = self.validate_sla_requirements(result)
        print(f"\n✅ SLA Validation:")
        for sla_name, passed in validations.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {sla_name}: {status}")

def main():
    """Main function to run API load tests."""
    parser = argparse.ArgumentParser(description='AquaChain API Load Testing')
    parser.add_argument('--api-url', type=str, default='https://api.aquachain.io', 
                       help='API base URL (default: https://api.aquachain.io)')
    parser.add_argument('--concurrent-users', type=int, default=50, 
                       help='Number of concurrent users (default: 50)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Test duration in seconds (default: 300)')
    parser.add_argument('--test-type', type=str, choices=['endpoints', 'workflows', 'both'], 
                       default='both', help='Type of test to run (default: both)')
    
    args = parser.parse_args()
    
    try:
        tester = APILoadTester(api_base_url=args.api_url)
        
        print("🔬 AquaChain API Load Testing")
        print("=" * 50)
        
        all_passed = True
        
        if args.test_type in ['endpoints', 'both']:
            # Test critical endpoints individually
            critical_endpoints = [
                ('/health', 'GET'),
                ('/api/v1/readings/test-device', 'GET'),
                ('/api/v1/service-requests', 'POST'),
                ('/api/v1/admin/system/health', 'GET')
            ]
            
            for endpoint, method in critical_endpoints:
                result = tester.run_endpoint_load_test(
                    endpoint=endpoint,
                    method=method,
                    concurrent_users=args.concurrent_users,
                    duration=min(args.duration, 180)  # Shorter duration for individual endpoints
                )
                tester.print_results(result, f"Endpoint Load Test - {method} {endpoint}")
                
                validations = tester.validate_sla_requirements(result)
                if not all(validations.values()):
                    all_passed = False
        
        if args.test_type in ['workflows', 'both']:
            # Test realistic user workflows
            workflow_results = tester.run_user_workflow_test(
                concurrent_users=args.concurrent_users,
                duration=args.duration
            )
            
            print(f"\n👥 User Workflow Test Results:")
            for endpoint, result in workflow_results.items():
                tester.print_results(result, f"Workflow Test - {endpoint}")
                
                validations = tester.validate_sla_requirements(result)
                if not all(validations.values()):
                    all_passed = False
        
        # Overall assessment
        print("\n🎯 Overall Assessment:")
        if all_passed:
            print("✅ All API load tests passed SLA requirements!")
            return 0
        else:
            print("❌ Some API load tests failed SLA requirements!")
            return 1
            
    except Exception as e:
        print(f"💥 API load test failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())