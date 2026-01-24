# Live Metrics Setup Guide

## 🎯 Overview

Your landing page metrics can now pull real-time data from various sources instead of using static values. This guide shows you how to set it up.

## 📊 Current Status

**Default Mode**: Static metrics (hardcoded values)  
**Available Modes**: Static, Live API, CloudWatch, Custom Monitoring

---

## 🚀 Quick Start: Enable Live Metrics

### Step 1: Enable Auto-Updates

Edit `frontend/src/config/landingPageMetrics.ts`:

```typescript
// Change from:
export const METRICS_UPDATE_INTERVAL = 0;

// To (update every 1 minute):
export const METRICS_UPDATE_INTERVAL = 60000;
```

### Step 2: Set API Endpoint

Create or edit `frontend/.env`:

```bash
# Add your metrics API endpoint
REACT_APP_METRICS_API_URL=https://api.yourdomain.com
```

### Step 3: Rebuild

```bash
cd frontend
npm run build
```

That's it! Your metrics will now update automatically every minute.

---

## 🔌 Data Source Options

### Option 1: Custom API Endpoint (Recommended)

**Best for**: Custom backend, Lambda functions, any REST API

1. **Create an API endpoint** that returns:
```json
{
  "success": true,
  "data": {
    "uptime": 99.8,
    "responseTime": 28,
    "dataIntegrity": 100,
    "lastUpdated": "2025-01-08T12:00:00Z"
  },
  "timestamp": "2025-01-08T12:00:00Z"
}
```

2. **Set environment variable**:
```bash
REACT_APP_METRICS_API_URL=https://api.yourdomain.com
```

3. **Enable updates** in config:
```typescript
export const METRICS_UPDATE_INTERVAL = 60000; // 1 minute
```

### Option 2: AWS CloudWatch

**Best for**: AWS-hosted applications

The service includes a `fetchFromCloudWatch()` method. To use it:

1. **Update the hook** in your component:
```typescript
const { metrics } = useLiveMetrics({
  enabled: true,
  source: 'cloudwatch',
  updateInterval: 300000 // 5 minutes
});
```

2. **Implement CloudWatch integration** in `metricsService.ts`:
```typescript
async fetchFromCloudWatch(): Promise<LiveMetrics> {
  // Use AWS SDK to fetch metrics
  const cloudwatch = new CloudWatchClient({ region: 'us-east-1' });
  
  // Fetch your metrics
  const uptime = await getMetric('SystemUptime');
  const responseTime = await getMetric('AlertResponseTime');
  
  return {
    uptime,
    responseTime,
    dataIntegrity: 100,
    lastUpdated: new Date().toISOString()
  };
}
```

### Option 3: Monitoring Services

**Best for**: Datadog, New Relic, Prometheus, Grafana

Similar to CloudWatch, implement the `fetchFromMonitoring()` method:

```typescript
const { metrics } = useLiveMetrics({
  enabled: true,
  source: 'monitoring',
  updateInterval: 120000 // 2 minutes
});
```

---

## 🏗️ Backend API Implementation

### Example: AWS Lambda Function

```python
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    # Fetch real metrics from your systems
    cloudwatch = boto3.client('cloudwatch')
    
    # Get uptime from CloudWatch
    uptime_response = cloudwatch.get_metric_statistics(
        Namespace='AquaChain',
        MetricName='SystemUptime',
        StartTime=datetime.now() - timedelta(days=30),
        EndTime=datetime.now(),
        Period=86400,
        Statistics=['Average']
    )
    
    uptime = uptime_response['Datapoints'][0]['Average'] if uptime_response['Datapoints'] else 99.8
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'success': True,
            'data': {
                'uptime': uptime,
                'responseTime': 28,
                'dataIntegrity': 100,
                'lastUpdated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        })
    }
```

### Example: Node.js Express API

```javascript
const express = require('express');
const app = express();

app.get('/metrics', async (req, res) => {
  // Fetch from your monitoring system
  const metrics = await fetchSystemMetrics();
  
  res.json({
    success: true,
    data: {
      uptime: metrics.uptime,
      responseTime: metrics.avgResponseTime,
      dataIntegrity: metrics.dataIntegrity,
      lastUpdated: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  });
});

app.listen(3000);
```

---

## 🎨 UI Features

When live metrics are enabled, users will see:

✅ **Real-time updates** - Metrics refresh automatically  
✅ **Last updated timestamp** - Shows when data was last fetched  
✅ **Refresh button** - Manual refresh option  
✅ **Loading indicator** - Shows when fetching new data  
✅ **Automatic fallback** - Uses static values if API fails  

---

## 🔧 Configuration Options

### Update Intervals

```typescript
// Update every 30 seconds (frequent)
export const METRICS_UPDATE_INTERVAL = 30000;

// Update every 1 minute (recommended)
export const METRICS_UPDATE_INTERVAL = 60000;

// Update every 5 minutes (conservative)
export const METRICS_UPDATE_INTERVAL = 300000;

// Disable live updates (static only)
export const METRICS_UPDATE_INTERVAL = 0;
```

### Custom Hook Usage

```typescript
// In your component
const { 
  metrics,        // Formatted metrics for display
  rawMetrics,     // Raw data from API
  isLoading,      // Loading state
  error,          // Error if fetch failed
  lastUpdated,    // Timestamp of last update
  refetch         // Manual refresh function
} = useLiveMetrics({
  enabled: true,
  updateInterval: 60000,
  source: 'api' // or 'cloudwatch' or 'monitoring'
});
```

---

## 🛡️ Error Handling

The system automatically handles errors:

1. **API Failure**: Falls back to mock data
2. **Network Issues**: Uses cached data
3. **Invalid Response**: Shows last known good values
4. **Timeout**: Retries on next interval

---

## 📈 Monitoring Your Metrics API

### Health Check

Add a health check endpoint:

```javascript
app.get('/metrics/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});
```

### Caching

The service includes built-in caching (1 minute default):

```typescript
// Adjust cache duration
metricsService.setCacheDuration(120000); // 2 minutes
```

---

## 🧪 Testing

### Test with Mock Data

The service automatically provides mock data for development:

```typescript
// In metricsService.ts
private getMockMetrics(): LiveMetrics {
  return {
    uptime: 99.8 + (Math.random() * 0.2 - 0.1),
    responseTime: 28 + (Math.random() * 4 - 2),
    dataIntegrity: 100,
    lastUpdated: new Date().toISOString()
  };
}
```

### Test API Integration

```bash
# Test your metrics endpoint
curl https://api.yourdomain.com/metrics

# Should return:
{
  "success": true,
  "data": {
    "uptime": 99.8,
    "responseTime": 28,
    "dataIntegrity": 100,
    "lastUpdated": "2025-01-08T12:00:00Z"
  }
}
```

---

## 🎯 Best Practices

1. **Cache Aggressively**: Don't hit your API too frequently
2. **Use CDN**: Cache API responses at edge locations
3. **Monitor Costs**: CloudWatch API calls cost money
4. **Graceful Degradation**: Always have fallback values
5. **Rate Limiting**: Implement rate limits on your API
6. **CORS**: Configure proper CORS headers
7. **Authentication**: Secure your metrics endpoint if needed

---

## 📝 Summary

| Mode | Setup Complexity | Cost | Real-time | Best For |
|------|-----------------|------|-----------|----------|
| Static | ⭐ Easy | Free | ❌ No | MVP, demos |
| API | ⭐⭐ Medium | Low | ✅ Yes | Production |
| CloudWatch | ⭐⭐⭐ Complex | Medium | ✅ Yes | AWS apps |
| Monitoring | ⭐⭐⭐ Complex | Varies | ✅ Yes | Enterprise |

---

## 🆘 Troubleshooting

**Metrics not updating?**
- Check `METRICS_UPDATE_INTERVAL` is > 0
- Verify API endpoint in `.env`
- Check browser console for errors

**API errors?**
- Verify CORS headers
- Check API response format
- Test endpoint with curl

**Performance issues?**
- Increase update interval
- Enable caching
- Use CDN for API

---

## 📚 Related Files

- `frontend/src/services/metricsService.ts` - API integration
- `frontend/src/hooks/useLiveMetrics.ts` - React hook
- `frontend/src/config/landingPageMetrics.ts` - Configuration
- `frontend/src/components/LandingPage/FeaturesShowcase.tsx` - UI component

---

Need help? Check the inline documentation in each file!
