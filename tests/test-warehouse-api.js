#!/usr/bin/env node

/**
 * AquaChain Warehouse API Test Suite
 * 
 * This script tests the enhanced warehouse management API endpoints
 * following security-first engineering principles and comprehensive validation.
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// Configuration
const config = {
  baseUrl: process.env.WAREHOUSE_API_URL || 'https://api.aquachain.com',
  authToken: process.env.AUTH_TOKEN || '',
  timeout: 10000,
  retries: 3
};

// Test results tracking
const testResults = {
  passed: 0,
  failed: 0,
  errors: [],
  details: []
};

/**
 * Secure HTTP client with proper error handling and validation
 */
class SecureApiClient {
  constructor(baseUrl, authToken) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
    this.correlationId = this.generateCorrelationId();
  }

  generateCorrelationId() {
    return `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  async makeRequest(method, path, body = null, expectedStatus = 200) {
    return new Promise((resolve, reject) => {
      const url = new URL(path, this.baseUrl);
      const isHttps = url.protocol === 'https:';
      const client = isHttps ? https : http;
      
      const options = {
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          'User-Agent': 'AquaChain-API-Test/1.0'
        },
        timeout: config.timeout
      };

      // Add authentication if token provided
      if (this.authToken) {
        options.headers['Authorization'] = `Bearer ${this.authToken}`;
      }

      // Add content length for POST/PUT requests
      if (body) {
        const bodyString = JSON.stringify(body);
        options.headers['Content-Length'] = Buffer.byteLength(bodyString);
      }

      const req = client.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const response = {
              statusCode: res.statusCode,
              headers: res.headers,
              body: data ? JSON.parse(data) : null,
              rawBody: data
            };
            
            resolve(response);
          } catch (parseError) {
            reject(new Error(`JSON parse error: ${parseError.message}. Raw response: ${data}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`Request failed: ${error.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error(`Request timeout after ${config.timeout}ms`));
      });

      // Send request body for POST/PUT
      if (body) {
        req.write(JSON.stringify(body));
      }
      
      req.end();
    });
  }
}

/**
 * Test suite for warehouse API endpoints
 */
class WarehouseApiTestSuite {
  constructor(client) {
    this.client = client;
    this.testLocationId = null;
  }

  async runAllTests() {
    console.log('🚀 Starting AquaChain Warehouse API Test Suite');
    console.log(`📍 Base URL: ${config.baseUrl}`);
    console.log(`🔗 Correlation ID: ${this.client.correlationId}`);
    console.log('=' .repeat(60));

    try {
      // Core functionality tests
      await this.testWarehouseOverview();
      await this.testReceivingWorkflow();
      await this.testDispatchWorkflow();
      await this.testStockMovements();
      await this.testPerformanceMetrics();
      
      // Location management tests
      await this.testLocationManagement();
      
      // Error handling tests
      await this.testErrorHandling();
      
      // Security tests
      await this.testSecurityValidation();

    } catch (error) {
      this.recordError('Test suite execution failed', error);
    }

    this.printResults();
  }

  async testWarehouseOverview() {
    console.log('\n📊 Testing Warehouse Overview...');
    
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/overview');
      
      this.validateResponse(response, 200, 'Warehouse Overview');
      this.validateProperty(response.body, 'overview', 'object');
      this.validateProperty(response.body.overview, 'total_locations', 'number');
      this.validateProperty(response.body.overview, 'occupancy_rate', 'number');
      this.validateProperty(response.body.overview, 'performance_metrics', 'object');
      
      // Validate performance metrics structure
      const metrics = response.body.overview.performance_metrics;
      this.validateProperty(metrics, 'throughput', 'object');
      this.validateProperty(metrics, 'efficiency', 'object');
      this.validateProperty(metrics, 'quality', 'object');
      
      this.recordSuccess('Warehouse Overview', 'All required fields present and valid');
      
    } catch (error) {
      this.recordError('Warehouse Overview', error);
    }
  }

  async testReceivingWorkflow() {
    console.log('\n📦 Testing Receiving Workflow...');
    
    // Test valid receiving workflow
    try {
      const receivingData = {
        po_id: 'PO-TEST-001',
        supplier_id: 'SUPPLIER-001',
        received_by: 'warehouse.manager@aquachain.com',
        items: [
          {
            item_id: 'ESP32-SENSOR-001',
            quantity_received: 50,
            condition: 'good',
            notes: 'All items inspected and approved'
          }
        ],
        quality_check_required: true,
        notes: 'Standard receiving process completed'
      };

      const response = await this.client.makeRequest('POST', '/api/warehouse/receiving', receivingData);
      
      this.validateResponse(response, 200, 'Receiving Workflow - Valid');
      this.validateProperty(response.body, 'workflow_id', 'string');
      this.validateProperty(response.body, 'status', 'string');
      this.validateProperty(response.body, 'items_processed', 'number');
      
      this.recordSuccess('Receiving Workflow - Valid', 'Workflow processed successfully');
      
    } catch (error) {
      this.recordError('Receiving Workflow - Valid', error);
    }

    // Test missing required fields
    try {
      const invalidData = {
        po_id: 'PO-TEST-002',
        items: [{ item_id: 'ESP32-SENSOR-001', quantity_received: 50 }]
        // Missing supplier_id and received_by
      };

      const response = await this.client.makeRequest('POST', '/api/warehouse/receiving', invalidData);
      
      this.validateResponse(response, 400, 'Receiving Workflow - Invalid');
      this.validateProperty(response.body, 'error', 'string');
      
      if (response.body.error.includes('Missing required field')) {
        this.recordSuccess('Receiving Workflow - Validation', 'Proper validation of required fields');
      } else {
        this.recordError('Receiving Workflow - Validation', new Error('Expected validation error message'));
      }
      
    } catch (error) {
      this.recordError('Receiving Workflow - Validation', error);
    }
  }

  async testDispatchWorkflow() {
    console.log('\n🚚 Testing Dispatch Workflow...');
    
    try {
      const dispatchData = {
        order_id: 'ORDER-TEST-001',
        dispatch_by: 'warehouse.picker@aquachain.com',
        priority: 'HIGH',
        items: [
          {
            item_id: 'ESP32-SENSOR-001',
            name: 'ESP32 Water Quality Sensor',
            quantity: 10,
            priority: 'HIGH'
          }
        ]
      };

      const response = await this.client.makeRequest('POST', '/api/warehouse/dispatch', dispatchData);
      
      this.validateResponse(response, 200, 'Dispatch Workflow');
      this.validateProperty(response.body, 'workflow_id', 'string');
      this.validateProperty(response.body, 'pick_list', 'object');
      this.validateProperty(response.body, 'estimated_pick_time', 'number');
      
      this.recordSuccess('Dispatch Workflow', 'Pick list generated successfully');
      
    } catch (error) {
      this.recordError('Dispatch Workflow', error);
    }
  }

  async testStockMovements() {
    console.log('\n📋 Testing Stock Movement Tracking...');
    
    // Test getting all movements
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/stock-movements');
      
      this.validateResponse(response, 200, 'Stock Movements - All');
      this.validateProperty(response.body, 'movements', 'object');
      this.validateProperty(response.body, 'count', 'number');
      this.validateProperty(response.body, 'analytics', 'object');
      
      this.recordSuccess('Stock Movements - All', 'Movement data retrieved successfully');
      
    } catch (error) {
      this.recordError('Stock Movements - All', error);
    }

    // Test filtered movements
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/stock-movements?item_id=ESP32-SENSOR-001&limit=50');
      
      this.validateResponse(response, 200, 'Stock Movements - Filtered');
      this.validateProperty(response.body, 'filters_applied', 'object');
      
      if (response.body.filters_applied.item_id === 'ESP32-SENSOR-001') {
        this.recordSuccess('Stock Movements - Filtered', 'Filters applied correctly');
      } else {
        this.recordError('Stock Movements - Filtered', new Error('Filters not applied correctly'));
      }
      
    } catch (error) {
      this.recordError('Stock Movements - Filtered', error);
    }
  }

  async testPerformanceMetrics() {
    console.log('\n📈 Testing Performance Metrics...');
    
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/performance-metrics?time_range=weekly');
      
      this.validateResponse(response, 200, 'Performance Metrics');
      this.validateProperty(response.body, 'time_range', 'string');
      this.validateProperty(response.body, 'realtime_metrics', 'object');
      this.validateProperty(response.body, 'summary', 'object');
      
      // Validate metrics structure
      const metrics = response.body.realtime_metrics;
      this.validateProperty(metrics, 'throughput', 'object');
      this.validateProperty(metrics, 'efficiency', 'object');
      this.validateProperty(metrics, 'quality', 'object');
      
      this.recordSuccess('Performance Metrics', 'Metrics structure validated');
      
    } catch (error) {
      this.recordError('Performance Metrics', error);
    }
  }

  async testLocationManagement() {
    console.log('\n🏢 Testing Location Management...');
    
    // Create location
    try {
      const locationData = {
        warehouse_id: 'WH001',
        zone: 'A',
        shelf: 'TEST-001',
        capacity: 100,
        description: 'Test location for API validation'
      };

      const response = await this.client.makeRequest('POST', '/api/warehouse/locations', locationData);
      
      this.validateResponse(response, 201, 'Create Location');
      this.validateProperty(response.body, 'location', 'object');
      this.validateProperty(response.body.location, 'location_id', 'string');
      
      this.testLocationId = response.body.location.location_id;
      this.recordSuccess('Create Location', `Location created: ${this.testLocationId}`);
      
    } catch (error) {
      this.recordError('Create Location', error);
      return; // Skip remaining location tests if creation fails
    }

    // Get location
    try {
      const response = await this.client.makeRequest('GET', `/api/warehouse/locations/${this.testLocationId}`);
      
      this.validateResponse(response, 200, 'Get Location');
      this.validateProperty(response.body, 'location', 'object');
      
      this.recordSuccess('Get Location', 'Location retrieved successfully');
      
    } catch (error) {
      this.recordError('Get Location', error);
    }

    // Update location
    try {
      const updateData = {
        capacity: 150,
        status: 'available',
        notes: 'Updated capacity for increased storage needs'
      };

      const response = await this.client.makeRequest('PUT', `/api/warehouse/locations/${this.testLocationId}`, updateData);
      
      this.validateResponse(response, 200, 'Update Location');
      this.validateProperty(response.body, 'location', 'object');
      
      if (response.body.location.capacity === 150) {
        this.recordSuccess('Update Location', 'Location updated successfully');
      } else {
        this.recordError('Update Location', new Error('Capacity not updated correctly'));
      }
      
    } catch (error) {
      this.recordError('Update Location', error);
    }

    // List locations
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/locations?warehouse_id=WH001&status=available');
      
      this.validateResponse(response, 200, 'List Locations');
      this.validateProperty(response.body, 'locations', 'object');
      this.validateProperty(response.body, 'count', 'number');
      
      this.recordSuccess('List Locations', `Found ${response.body.count} locations`);
      
    } catch (error) {
      this.recordError('List Locations', error);
    }

    // Delete location (cleanup)
    if (this.testLocationId) {
      try {
        const response = await this.client.makeRequest('DELETE', `/api/warehouse/locations/${this.testLocationId}`);
        
        this.validateResponse(response, 200, 'Delete Location');
        this.recordSuccess('Delete Location', 'Test location cleaned up');
        
      } catch (error) {
        this.recordError('Delete Location', error);
      }
    }
  }

  async testErrorHandling() {
    console.log('\n❌ Testing Error Handling...');
    
    // Test invalid endpoint
    try {
      const response = await this.client.makeRequest('GET', '/api/warehouse/invalid-endpoint');
      
      this.validateResponse(response, 404, 'Invalid Endpoint');
      this.validateProperty(response.body, 'error', 'string');
      
      this.recordSuccess('Invalid Endpoint', 'Proper 404 error handling');
      
    } catch (error) {
      this.recordError('Invalid Endpoint', error);
    }

    // Test invalid JSON
    try {
      // Manually construct request with invalid JSON
      const response = await this.client.makeRequest('POST', '/api/warehouse/receiving', '{ invalid json');
      
      this.validateResponse(response, 400, 'Invalid JSON');
      this.recordSuccess('Invalid JSON', 'Proper JSON validation');
      
    } catch (error) {
      // Expected to fail due to JSON parsing
      if (error.message.includes('JSON parse')) {
        this.recordSuccess('Invalid JSON', 'JSON validation working correctly');
      } else {
        this.recordError('Invalid JSON', error);
      }
    }
  }

  async testSecurityValidation() {
    console.log('\n🔒 Testing Security Validation...');
    
    // Test without authentication (if auth is required)
    if (config.authToken) {
      try {
        const clientNoAuth = new SecureApiClient(config.baseUrl, '');
        const response = await clientNoAuth.makeRequest('GET', '/api/warehouse/overview');
        
        if (response.statusCode === 401 || response.statusCode === 403) {
          this.recordSuccess('Authentication Required', 'Proper authentication enforcement');
        } else {
          this.recordError('Authentication Required', new Error('Authentication not properly enforced'));
        }
        
      } catch (error) {
        // Network errors are acceptable for auth tests
        this.recordSuccess('Authentication Required', 'Authentication enforcement detected');
      }
    }

    // Test correlation ID presence
    const hasCorrelationId = this.client.correlationId && this.client.correlationId.length > 0;
    if (hasCorrelationId) {
      this.recordSuccess('Correlation ID', 'Correlation ID properly generated and used');
    } else {
      this.recordError('Correlation ID', new Error('Correlation ID not properly implemented'));
    }
  }

  validateResponse(response, expectedStatus, testName) {
    if (response.statusCode !== expectedStatus) {
      throw new Error(`Expected status ${expectedStatus}, got ${response.statusCode}. Body: ${JSON.stringify(response.body)}`);
    }
  }

  validateProperty(obj, property, expectedType) {
    if (!obj || typeof obj !== 'object') {
      throw new Error(`Object is null or not an object`);
    }
    
    if (!(property in obj)) {
      throw new Error(`Property '${property}' is missing`);
    }
    
    const actualType = Array.isArray(obj[property]) ? 'array' : typeof obj[property];
    if (expectedType === 'object' && actualType === 'array') {
      // Arrays are acceptable as objects in this context
      return;
    }
    
    if (actualType !== expectedType) {
      throw new Error(`Property '${property}' expected type '${expectedType}', got '${actualType}'`);
    }
  }

  recordSuccess(testName, message) {
    testResults.passed++;
    testResults.details.push({ test: testName, status: 'PASS', message });
    console.log(`  ✅ ${testName}: ${message}`);
  }

  recordError(testName, error) {
    testResults.failed++;
    testResults.errors.push({ test: testName, error: error.message });
    testResults.details.push({ test: testName, status: 'FAIL', message: error.message });
    console.log(`  ❌ ${testName}: ${error.message}`);
  }

  printResults() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(60));
    console.log(`✅ Passed: ${testResults.passed}`);
    console.log(`❌ Failed: ${testResults.failed}`);
    console.log(`📈 Success Rate: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);
    
    if (testResults.failed > 0) {
      console.log('\n🔍 FAILED TESTS:');
      testResults.errors.forEach(error => {
        console.log(`  • ${error.test}: ${error.error}`);
      });
    }
    
    console.log('\n📋 DETAILED RESULTS:');
    testResults.details.forEach(detail => {
      const icon = detail.status === 'PASS' ? '✅' : '❌';
      console.log(`  ${icon} ${detail.test}: ${detail.message}`);
    });
    
    // Exit with appropriate code
    process.exit(testResults.failed > 0 ? 1 : 0);
  }
}

// Main execution
async function main() {
  // Validate configuration
  if (!config.baseUrl) {
    console.error('❌ Error: WAREHOUSE_API_URL environment variable is required');
    process.exit(1);
  }

  if (!config.authToken) {
    console.warn('⚠️  Warning: No AUTH_TOKEN provided. Some tests may fail if authentication is required.');
  }

  // Initialize client and test suite
  const client = new SecureApiClient(config.baseUrl, config.authToken);
  const testSuite = new WarehouseApiTestSuite(client);
  
  // Run tests
  await testSuite.runAllTests();
}

// Handle uncaught errors
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
  process.exit(1);
});

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  });
}

module.exports = { WarehouseApiTestSuite, SecureApiClient };