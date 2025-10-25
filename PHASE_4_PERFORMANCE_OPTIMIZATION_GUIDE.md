# Phase 4 Performance Optimization Guide

## Overview

This guide documents performance optimization techniques implemented in Phase 4 of the AquaChain IoT water quality monitoring system. It provides best practices, implementation patterns, and troubleshooting guidance for maintaining optimal system performance.

## Table of Contents

1. [Performance Targets](#performance-targets)
2. [Database Query Optimization](#database-query-optimization)
3. [Frontend Performance](#frontend-performance)
4. [Lambda Function Optimization](#lambda-function-optimization)
5. [Caching Strategy](#caching-strategy)
6. [CDN Configuration](#cdn-configuration)
7. [WebSocket Optimization](#websocket-optimization)
8. [Monitoring and Alerting](#monitoring-and-alerting)

---

## Performance Targets

### System-Wide Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | < 500ms | P95 latency |
| Page Load Time | < 3 seconds | First Contentful Paint |
| Initial Bundle Size | < 500KB | Gzipped |
| Lambda Cold Start | < 2 seconds | P95 latency |
| Database Query Time | < 500ms | P95 latency |
| WebSocket Reconnect | < 5 seconds | Average time |
| Cache Hit Rate | > 80% | For cacheable requests |

### Performance Budget

**Frontend Bundle Sizes**:
- Main bundle: < 250KB
- Vendor bundle: < 200KB
- Route chunks: < 50KB each
- Total initial load: < 500KB

**API Endpoints**:
- List operations: < 300ms
- Get operations: < 200ms
- Create/Update operations: < 500ms
- Complex queries: < 1000ms

---

## Database Query Optimization

### Global Secondary Indexes (GSIs)

**Purpose**: Optimize DynamoDB query patterns to avoid expensive scan operations.

#### Devices Table GSIs

```python
# Primary Key: device_id (HASH)

# GSI-1: user_id-created_at-index
# Use case: List all devices for a user, sorted by creation date
response = table.query(
    IndexName='user_id-created_at-index',
    KeyConditionExpression=Key('user_id').eq(user_id),
    ScanIndexForward=False,  # Newest first
    Limit=100
)

# GSI-2: status-last_seen-index
# Use case: Find all active devices, sorted by last seen
response = table.query(
    IndexName='status-last_seen-index',
    KeyConditionExpression=Key('status').eq('active'),
    ScanIndexForward=False,
    Limit=100
)
```

#### SensorReadings Table GSIs

```python
# Primary Key: device_id (HASH) + timestamp (RANGE)

# GSI-1: device_id-metric_type-index
# Use case: Query specific metric type for a device
response = table.query(
    IndexName='device_id-metric_type-index',
    KeyConditionExpression=Key('device_id').eq(device_id) & 
                          Key('metric_type').eq('ph'),
    Limit=1000
)

# GSI-2: alert_level-timestamp-index
# Use case: Find all critical alerts in time range
response = table.query(
    IndexName='alert_level-timestamp-index',
    KeyConditionExpression=Key('alert_level').eq('critical') &
                          Key('timestamp').between(start_time, end_time)
)
```

#### Users Table GSIs

```python
# Primary Key: user_id (HASH)

# GSI-1: email-index
# Use case: User lookup by email
response = table.query(
    IndexName='email-index',
    KeyConditionExpression=Key('email').eq(email)
)

# GSI-2: organization_id-role-index
# Use case: List users by organization and role
response = table.query(
    IndexName='organization_id-role-index',
    KeyConditionExpression=Key('organization_id').eq(org_id) &
                          Key('role').eq('technician')
)
```

### Query Optimization Patterns

#### Pagination

**Always implement pagination for list operations**:

```python
def list_devices_paginated(
    user_id: str,
    limit: int = 100,
    last_key: Optional[Dict] = None
) -> Dict:
    """
    List devices with pagination support.
    
    Args:
        user_id: User identifier
        limit: Maximum items per page (default 100)
        last_key: Pagination token from previous request
        
    Returns:
        Dictionary with items, last_key, and has_more flag
    """
    query_params = {
        'IndexName': 'user_id-created_at-index',
        'KeyConditionExpression': Key('user_id').eq(user_id),
        'Limit': limit,
        'ScanIndexForward': False
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response
    }
```

#### Batch Operations

**Use batch operations for multiple items**:

```python
from boto3.dynamodb.conditions import Key

def batch_get_devices(device_ids: List[str]) -> List[Dict]:
    """
    Retrieve multiple devices in a single batch operation.
    
    Args:
        device_ids: List of device identifiers
        
    Returns:
        List of device records
    """
    # DynamoDB batch_get_item supports up to 100 items
    devices = []
    
    for i in range(0, len(device_ids), 100):
        batch = device_ids[i:i+100]
        
        response = dynamodb.batch_get_item(
            RequestItems={
                'Devices': {
                    'Keys': [{'device_id': device_id} for device_id in batch]
                }
            }
        )
        
        devices.extend(response['Responses']['Devices'])
    
    return devices
```

#### Query Performance Monitoring

**Monitor and log slow queries**:

```python
from lambda.shared.query_performance_monitor import QueryPerformanceMonitor

monitor = QueryPerformanceMonitor()

@monitor.track_query('list_devices')
def list_devices(user_id: str) -> List[Dict]:
    """List devices with automatic performance tracking"""
    start_time = time.time()
    
    response = table.query(
        IndexName='user_id-created_at-index',
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Log warning if query is slow
    if duration_ms > 500:
        logger.warning(
            'Slow query detected',
            query_type='list_devices',
            duration_ms=duration_ms,
            user_id=user_id,
            item_count=len(response['Items'])
        )
    
    return response['Items']
```

---

## Frontend Performance

### React Optimization Techniques

#### Memoization

**Use React.memo for expensive components**:

```typescript
import React, { memo } from 'react';

interface DeviceCardProps {
  device: Device;
  onSelect: (id: string) => void;
}

// Memoize component to prevent unnecessary re-renders
export const DeviceCard = memo<DeviceCardProps>(
  ({ device, onSelect }) => {
    return (
      <div onClick={() => onSelect(device.deviceId)}>
        <h3>{device.name}</h3>
        <p>Status: {device.status}</p>
      </div>
    );
  },
  // Custom comparison function
  (prevProps, nextProps) => {
    return (
      prevProps.device.deviceId === nextProps.device.deviceId &&
      prevProps.device.status === nextProps.device.status &&
      prevProps.device.name === nextProps.device.name
    );
  }
);
```

**Use useMemo for expensive computations**:

```typescript
import { useMemo } from 'react';

function DeviceAnalytics({ readings }: { readings: SensorReading[] }) {
  // Memoize expensive calculation
  const statistics = useMemo(() => {
    return calculateStatistics(readings);
  }, [readings]);
  
  // Memoize filtered data
  const criticalReadings = useMemo(() => {
    return readings.filter(r => r.alertLevel === 'critical');
  }, [readings]);
  
  return (
    <div>
      <Stats data={statistics} />
      <AlertList readings={criticalReadings} />
    </div>
  );
}
```

**Use useCallback for event handlers**:

```typescript
import { useCallback } from 'react';

function DeviceList({ devices }: { devices: Device[] }) {
  const navigate = useNavigate();
  
  // Memoize callback to prevent child re-renders
  const handleDeviceClick = useCallback((deviceId: string) => {
    navigate(`/devices/${deviceId}`);
  }, [navigate]);
  
  return (
    <div>
      {devices.map(device => (
        <DeviceCard
          key={device.deviceId}
          device={device}
          onSelect={handleDeviceClick}
        />
      ))}
    </div>
  );
}
```

#### Code Splitting

**Lazy load routes**:

```typescript
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy load dashboard components
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const TechnicianDashboard = lazy(() => import('./pages/TechnicianDashboard'));
const ConsumerDashboard = lazy(() => import('./pages/ConsumerDashboard'));
const DeviceManagement = lazy(() => import('./pages/DeviceManagement'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/technician" element={<TechnicianDashboard />} />
        <Route path="/consumer" element={<ConsumerDashboard />} />
        <Route path="/devices" element={<DeviceManagement />} />
      </Routes>
    </Suspense>
  );
}
```

**Lazy load heavy components**:

```typescript
import { lazy, Suspense } from 'react';

// Lazy load chart library
const ChartComponent = lazy(() => import('./components/ChartComponent'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      
      {showChart && (
        <Suspense fallback={<div>Loading chart...</div>}>
          <ChartComponent data={chartData} />
        </Suspense>
      )}
    </div>
  );
}
```

#### Asset Optimization

**Image optimization** (`craco.config.js`):

```javascript
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Add image optimization
      webpackConfig.module.rules.push({
        test: /\.(png|jpg|jpeg|gif)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024 // Inline images < 8KB
          }
        },
        use: [
          {
            loader: 'image-webpack-loader',
            options: {
              mozjpeg: { progressive: true, quality: 75 },
              optipng: { enabled: true },
              pngquant: { quality: [0.65, 0.90], speed: 4 },
              webp: { quality: 75 }
            }
          }
        ]
      });
      
      return webpackConfig;
    }
  }
};
```

**Bundle splitting**:

```javascript
// craco.config.js
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      webpackConfig.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          // Vendor bundle for node_modules
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
            reuseExistingChunk: true
          },
          // Common code shared across routes
          common: {
            minChunks: 2,
            priority: 5,
            reuseExistingChunk: true,
            name: 'common'
          },
          // Large libraries in separate chunks
          recharts: {
            test: /[\\/]node_modules[\\/]recharts/,
            name: 'recharts',
            priority: 20
          }
        }
      };
      
      return webpackConfig;
    }
  }
};
```

### Performance Monitoring

**Track Core Web Vitals**:

```typescript
import { usePerformanceMonitor } from './hooks/usePerformanceMonitor';

function App() {
  usePerformanceMonitor({
    onMetric: (metric) => {
      // Log performance metrics
      console.log(`${metric.name}: ${metric.value}`);
      
      // Send to analytics
      if (metric.value > metric.threshold) {
        analytics.track('performance_issue', {
          metric: metric.name,
          value: metric.value,
          threshold: metric.threshold
        });
      }
    }
  });
  
  return <AppContent />;
}
```

---

## Lambda Function Optimization

### Provisioned Concurrency

**Configure for high-traffic functions**:

```python
# infrastructure/cdk/stacks/lambda_performance_stack.py
from aws_cdk import aws_lambda as lambda_

# Create function with provisioned concurrency
data_processing_fn = lambda_python.PythonFunction(
    self, 'DataProcessing',
    entry='lambda/data_processing',
    runtime=lambda_.Runtime.PYTHON_3_11,
    memory_size=1024,
    timeout=Duration.seconds(30),
    reserved_concurrent_executions=100
)

# Add auto-scaling provisioned concurrency
version = data_processing_fn.current_version
alias = lambda_.Alias(
    self, 'DataProcessingAlias',
    alias_name='live',
    version=version
)

alias.add_auto_scaling(
    max_capacity=50,
    min_capacity=5
).scale_on_utilization(
    utilization_target=0.7
)
```

### Lambda Layers

**Reduce deployment package size**:

```
lambda/layers/
├── common/
│   ├── requirements.txt  # boto3, requests, pydantic
│   └── python/
└── ml/
    ├── requirements.txt  # numpy, pandas, scikit-learn
    └── python/
```

**Build layers**:

```bash
# Build common layer
cd lambda/layers/common
pip install -r requirements.txt -t python/
zip -r common-layer.zip python/

# Build ML layer
cd lambda/layers/ml
pip install -r requirements.txt -t python/
zip -r ml-layer.zip python/
```

**Attach layers to functions**:

```python
# infrastructure/cdk/stacks/lambda_layers_stack.py
common_layer = lambda_python.PythonLayerVersion(
    self, 'CommonLayer',
    entry='lambda/layers/common',
    compatible_runtimes=[lambda_.Runtime.PYTHON_3_11]
)

# Use layer in function
data_processing_fn = lambda_python.PythonFunction(
    self, 'DataProcessing',
    entry='lambda/data_processing',
    layers=[common_layer]
)
```

### Memory Optimization

**Profile and optimize memory allocation**:

```python
# lambda/scripts/profile_memory.py
import tracemalloc
import json

def profile_memory(func):
    """Decorator to profile memory usage"""
    def wrapper(event, context):
        tracemalloc.start()
        
        result = func(event, context)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(json.dumps({
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'function': func.__name__
        }))
        
        return result
    
    return wrapper

@profile_memory
def lambda_handler(event, context):
    # Function implementation
    pass
```

**Optimize memory settings**:

```python
# Based on profiling data, adjust memory allocation
# Rule of thumb: Set memory to 1.5x peak usage

# Low memory function (< 128MB peak)
lambda_.Function(memory_size=256)

# Medium memory function (128-512MB peak)
lambda_.Function(memory_size=1024)

# High memory function (> 512MB peak)
lambda_.Function(memory_size=2048)
```

### Cold Start Optimization

**Monitor cold starts**:

```python
from lambda.shared.cold_start_monitor import ColdStartMonitor

monitor = ColdStartMonitor()

def lambda_handler(event, context):
    # Track cold start
    is_cold_start = monitor.check_cold_start(context)
    
    if is_cold_start:
        logger.warning(
            'Cold start detected',
            function_name=context.function_name,
            request_id=context.request_id
        )
    
    # Function logic
    return process_request(event)
```

**Reduce cold start time**:

1. **Minimize dependencies**: Use Lambda layers
2. **Optimize imports**: Import only what you need
3. **Use provisioned concurrency**: For critical functions
4. **Keep functions warm**: Use CloudWatch Events to ping functions

```python
# Optimize imports - import inside function if rarely used
def lambda_handler(event, context):
    # Common imports at top
    import json
    import boto3
    
    # Heavy imports only when needed
    if event.get('use_ml'):
        import numpy as np
        import pandas as pd
        # ML processing
    
    # Regular processing
    return process_data(event)
```

---

## Caching Strategy

### ElastiCache Redis

**Cache Service Implementation**:

```python
from lambda.shared.cache_service import CacheService

cache = CacheService(os.environ['REDIS_ENDPOINT'])

def get_device_data(device_id: str) -> Dict:
    """Get device data with caching"""
    cache_key = f"device:{device_id}"
    
    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info('Cache hit', cache_key=cache_key)
        return cached_data
    
    # Cache miss - fetch from database
    logger.info('Cache miss', cache_key=cache_key)
    data = dynamodb.get_item(Key={'device_id': device_id})
    
    # Cache for 5 minutes
    cache.set(cache_key, data, ttl=300)
    
    return data
```

### Cache Invalidation

**Invalidate on updates**:

```python
def update_device(device_id: str, updates: Dict) -> Dict:
    """Update device and invalidate cache"""
    # Update database
    response = table.update_item(
        Key={'device_id': device_id},
        UpdateExpression='SET #name = :name, #status = :status',
        ExpressionAttributeNames={
            '#name': 'name',
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':name': updates['name'],
            ':status': updates['status']
        },
        ReturnValues='ALL_NEW'
    )
    
    # Invalidate cache
    cache.delete(f"device:{device_id}")
    cache.invalidate_pattern(f"user:*:devices")  # Invalidate list caches
    
    return response['Attributes']
```

### Cache TTL Strategy

**TTL Guidelines**:

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| User Profile | 15 minutes | Changes infrequently |
| Device Status | 5 minutes | Changes moderately |
| Sensor Readings | 1 minute | Changes frequently |
| Static Config | 1 hour | Rarely changes |
| Aggregated Stats | 10 minutes | Expensive to compute |

---

## CDN Configuration

### CloudFront Setup

**Cache Policies**:

```python
# infrastructure/cdk/stacks/cloudfront_stack.py

# Static assets - long TTL
static_cache_policy = cloudfront.CachePolicy(
    self, 'StaticCachePolicy',
    default_ttl=Duration.days(365),
    max_ttl=Duration.days(365),
    min_ttl=Duration.days(1),
    enable_accept_encoding_gzip=True,
    enable_accept_encoding_brotli=True
)

# API responses - no caching
api_cache_policy = cloudfront.CachePolicy.CACHING_DISABLED

# Distribution
distribution = cloudfront.Distribution(
    self, 'Distribution',
    default_behavior=cloudfront.BehaviorOptions(
        origin=origins.S3Origin(frontend_bucket),
        cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
        compress=True
    ),
    additional_behaviors={
        '/static/*': cloudfront.BehaviorOptions(
            origin=origins.S3Origin(frontend_bucket),
            cache_policy=static_cache_policy
        ),
        '/api/*': cloudfront.BehaviorOptions(
            origin=origins.HttpOrigin('api.aquachain.com'),
            cache_policy=api_cache_policy,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL
        )
    }
)
```

### Cache Invalidation

**Invalidate on deployment**:

```javascript
// frontend/deploy-cloudfront.js
const AWS = require('aws-sdk');
const cloudfront = new AWS.CloudFront();

async function invalidateCache(distributionId) {
  const params = {
    DistributionId: distributionId,
    InvalidationBatch: {
      CallerReference: Date.now().toString(),
      Paths: {
        Quantity: 2,
        Items: [
          '/index.html',
          '/static/*'
        ]
      }
    }
  };
  
  const result = await cloudfront.createInvalidation(params).promise();
  console.log('Cache invalidation created:', result.Invalidation.Id);
}
```

---

## WebSocket Optimization

### Connection Pooling

**Reuse connections**:

```typescript
// frontend/src/services/websocketService.ts
class WebSocketService {
  private connections: Map<string, WebSocket> = new Map();
  
  connect(topic: string, onMessage: (data: any) => void): void {
    // Reuse existing connection
    if (this.connections.has(topic)) {
      console.log(`Reusing connection for ${topic}`);
      return;
    }
    
    // Create new connection
    const ws = new WebSocket(`${WS_ENDPOINT}?topic=${topic}`);
    this.connections.set(topic, ws);
    
    ws.onmessage = (event) => {
      onMessage(JSON.parse(event.data));
    };
  }
  
  disconnect(topic: string): void {
    const ws = this.connections.get(topic);
    if (ws) {
      ws.close();
      this.connections.delete(topic);
    }
  }
}
```

### Automatic Reconnection

**Exponential backoff**:

```typescript
private handleReconnect(topic: string, onMessage: (data: any) => void): void {
  const attempts = this.reconnectAttempts.get(topic) || 0;
  
  if (attempts >= 5) {
    console.error(`Max reconnect attempts reached for ${topic}`);
    this.notifyUser('Connection lost. Please refresh the page.');
    return;
  }
  
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s
  const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
  
  setTimeout(() => {
    console.log(`Reconnecting to ${topic} (attempt ${attempts + 1})`);
    this.reconnectAttempts.set(topic, attempts + 1);
    this.connect(topic, onMessage);
  }, delay);
}
```

---

## Monitoring and Alerting

### Performance Metrics

**CloudWatch Metrics**:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metric(metric_name: str, value: float, unit: str = 'Milliseconds'):
    """Publish custom performance metric"""
    cloudwatch.put_metric_data(
        Namespace='AquaChain/Performance',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
        ]
    )

# Usage
query_duration = (time.time() - start_time) * 1000
publish_metric('QueryDuration', query_duration)
```

### Performance Alarms

**Set up CloudWatch Alarms**:

```python
# infrastructure/monitoring/performance_alarms.py
from aws_cdk import aws_cloudwatch as cloudwatch

# API latency alarm
api_latency_alarm = cloudwatch.Alarm(
    self, 'ApiLatencyAlarm',
    metric=api_gateway.metric_latency(),
    threshold=500,
    evaluation_periods=2,
    alarm_description='API latency exceeds 500ms'
)

# Lambda cold start alarm
cold_start_alarm = cloudwatch.Alarm(
    self, 'ColdStartAlarm',
    metric=cloudwatch.Metric(
        namespace='AquaChain/Performance',
        metric_name='ColdStartDuration',
        statistic='p95'
    ),
    threshold=2000,
    evaluation_periods=2,
    alarm_description='Lambda cold start exceeds 2 seconds'
)
```

---

## Troubleshooting

### Common Performance Issues

**Slow API Responses**:
1. Check CloudWatch metrics for Lambda duration
2. Review DynamoDB query patterns (scan vs query)
3. Check cache hit rate
4. Review network latency

**High Lambda Costs**:
1. Review memory allocation (over-provisioned?)
2. Check execution duration
3. Review provisioned concurrency settings
4. Optimize cold start times

**Frontend Performance Issues**:
1. Check bundle size with `npm run analyze`
2. Review React DevTools Profiler
3. Check for unnecessary re-renders
4. Review network waterfall in browser DevTools

---

**Document Version**: 1.0  
**Last Updated**: Phase 4 Implementation  
**Owner**: Performance Engineering Team
