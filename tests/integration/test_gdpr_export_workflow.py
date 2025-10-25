"""
Integration tests for GDPR data export workflow
Tests the complete end-to-end export process
"""

import pytest
import json
import time
import os
from typing import Dict, Any

# These tests require AWS credentials and actual infrastructure
# Mark as integration tests that can be skipped in CI
pytestmark = pytest.mark.integration


@pytest.fixture
def api_base_url():
    """Get API base URL from environment"""
    return os.environ.get('API_BASE_URL', 'http://localhost:3000/api')


@pytest.fixture
def test_user_credentials():
    """Get test user credentials"""
    return {
        'email': os.environ.get('TEST_USER_EMAIL', 'test@example.com'),
        'password': os.environ.get('TEST_USER_PASSWORD', 'TestPassword123!')
    }


@pytest.fixture
def auth_token(api_base_url, test_user_credentials):
    """Authenticate and get JWT token"""
    import requests
    
    response = requests.post(
        f"{api_base_url}/auth/login",
        json=test_user_credentials
    )
    
    assert response.status_code == 200
    data = response.json()
    return data['token']


class TestGDPRExportWorkflow:
    """Integration tests for complete GDPR export workflow"""
    
    def test_complete_export_workflow(self, api_base_url, auth_token, test_user_credentials):
        """Test complete GDPR export workflow from request to download"""
        import requests
        
        # Step 1: Request data export
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'test-user-id',
                'email': test_user_credentials['email']
            }
        )
        
        assert response.status_code in [200, 202]
        export_data = response.json()
        
        assert 'request_id' in export_data
        request_id = export_data['request_id']
        
        # Step 2: Poll for completion (with timeout)
        max_attempts = 30
        attempt = 0
        export_completed = False
        
        while attempt < max_attempts:
            status_response = requests.get(
                f"{api_base_url}/gdpr/export/{request_id}",
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data['status'] == 'completed':
                export_completed = True
                assert 'download_url' in status_data
                download_url = status_data['download_url']
                break
            elif status_data['status'] == 'failed':
                pytest.fail(f"Export failed: {status_data.get('error_message')}")
            
            time.sleep(2)
            attempt += 1
        
        assert export_completed, "Export did not complete within timeout"
        
        # Step 3: Verify export URL is accessible
        download_response = requests.get(download_url)
        assert download_response.status_code == 200
        
        # Step 4: Verify export data structure
        export_content = download_response.json()
        
        assert 'export_metadata' in export_content
        assert 'profile' in export_content
        assert 'devices' in export_content
        assert 'sensor_readings' in export_content
        assert 'alerts' in export_content
        
        # Verify metadata
        metadata = export_content['export_metadata']
        assert 'export_date' in metadata
        assert 'user_id' in metadata
        assert 'request_id' in metadata
        assert metadata['request_id'] == request_id
    
    def test_list_user_exports(self, api_base_url, auth_token):
        """Test listing user's export requests"""
        import requests
        
        response = requests.get(
            f"{api_base_url}/gdpr/exports",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'exports' in data
        assert 'count' in data
        assert isinstance(data['exports'], list)
    
    def test_export_without_authentication(self, api_base_url):
        """Test that export requires authentication"""
        import requests
        
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            json={
                'user_id': 'test-user-id',
                'email': 'test@example.com'
            }
        )
        
        assert response.status_code in [401, 403]
    
    def test_export_unauthorized_user_data(self, api_base_url, auth_token):
        """Test that users cannot export other users' data"""
        import requests
        
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'different-user-id',
                'email': 'other@example.com'
            }
        )
        
        # Should return 403 Forbidden or 401 Unauthorized
        assert response.status_code in [401, 403]
    
    def test_export_data_completeness(self, api_base_url, auth_token, test_user_credentials):
        """Test that export includes all user data"""
        import requests
        
        # First, create some test data (devices, readings, etc.)
        # This would require additional setup
        
        # Request export
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'test-user-id',
                'email': test_user_credentials['email']
            }
        )
        
        assert response.status_code in [200, 202]
        export_data = response.json()
        request_id = export_data['request_id']
        
        # Wait for completion
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = requests.get(
                f"{api_base_url}/gdpr/export/{request_id}",
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            if status_response.json()['status'] == 'completed':
                download_url = status_response.json()['download_url']
                break
            
            time.sleep(2)
        
        # Download and verify
        download_response = requests.get(download_url)
        export_content = download_response.json()
        
        # Verify all sections are present
        required_sections = [
            'export_metadata',
            'profile',
            'devices',
            'sensor_readings',
            'alerts',
            'service_requests',
            'audit_logs'
        ]
        
        for section in required_sections:
            assert section in export_content, f"Missing section: {section}"
    
    def test_export_url_expiration(self, api_base_url, auth_token):
        """Test that export URLs have proper expiration"""
        import requests
        
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'test-user-id',
                'email': 'test@example.com'
            }
        )
        
        assert response.status_code in [200, 202]
        data = response.json()
        
        # Verify expiration information is provided
        if 'expires_in_days' in data:
            assert data['expires_in_days'] == 7
    
    def test_multiple_concurrent_exports(self, api_base_url, auth_token, test_user_credentials):
        """Test handling of multiple export requests"""
        import requests
        
        # Request multiple exports
        request_ids = []
        
        for i in range(3):
            response = requests.post(
                f"{api_base_url}/gdpr/export",
                headers={'Authorization': f'Bearer {auth_token}'},
                json={
                    'user_id': 'test-user-id',
                    'email': test_user_credentials['email']
                }
            )
            
            assert response.status_code in [200, 202]
            data = response.json()
            request_ids.append(data['request_id'])
        
        # Verify all requests are tracked
        assert len(set(request_ids)) == 3, "Request IDs should be unique"
        
        # Verify all can be retrieved
        for request_id in request_ids:
            status_response = requests.get(
                f"{api_base_url}/gdpr/export/{request_id}",
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            assert status_response.status_code == 200


class TestGDPRExportPerformance:
    """Performance tests for GDPR export"""
    
    def test_export_performance_small_dataset(self, api_base_url, auth_token):
        """Test export performance with small dataset"""
        import requests
        import time
        
        start_time = time.time()
        
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'test-user-id',
                'email': 'test@example.com'
            }
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code in [200, 202]
        
        # Export request should complete quickly (< 5 seconds)
        assert duration < 5.0, f"Export request took too long: {duration}s"
    
    def test_export_completion_time(self, api_base_url, auth_token, test_user_credentials):
        """Test that export completes within acceptable time"""
        import requests
        import time
        
        # Request export
        response = requests.post(
            f"{api_base_url}/gdpr/export",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'user_id': 'test-user-id',
                'email': test_user_credentials['email']
            }
        )
        
        request_id = response.json()['request_id']
        start_time = time.time()
        
        # Poll for completion
        max_wait = 60  # 60 seconds max
        while time.time() - start_time < max_wait:
            status_response = requests.get(
                f"{api_base_url}/gdpr/export/{request_id}",
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            if status_response.json()['status'] == 'completed':
                completion_time = time.time() - start_time
                
                # Should complete within 60 seconds for small datasets
                assert completion_time < 60.0
                return
            
            time.sleep(2)
        
        pytest.fail("Export did not complete within acceptable time")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
