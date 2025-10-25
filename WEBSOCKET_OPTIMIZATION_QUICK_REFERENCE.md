# WebSocket Optimization Quick Reference

## Overview

Task 14 implements WebSocket connection pooling, automatic reconnection, and multi-region load balancing for the AquaChain system.

## Key Features

### ✅ Connection Pooling (14.1)
- Reuses existing connections for same topics
- Maintains connection map with subscriber tracking
- Automatic cleanup on component unmount
- Multiple subscribers per connection

### ✅ Automatic Reconnection (14.2)
- Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Max 5 reconnection attempts
- User notifications after max attempts
- Heartbeat to keep connections alive

### ✅ Multi-Region Load Balancing (14.3)
- Route53 health checks for each region
- Weighted routing (Primary: 100, Secondary: 50, Tertiary: 25)
- Automatic failover to healthy regions
- CloudWatch monitoring and alarms

## Quick Start

### Using WebSocket Service

```typescript
import { websocketService } from './services/websocketService';

// Connect to a topic
websocketService.connect('device-updates', (data) => {
  console.log('Received:', data);
});

// Check connection status
const status = websocketService.getConnectionStatus('device-updates');
console.log('Connected:', status.isConnected);
console.log('Subscribers:', status.subscriberCount);

// Disconnect
websocketService.disconnect('device-updates');
```

### Using React Hook

```typescript
import { useRealTimeUpdates } from './hooks/useRealTimeUpdates';

function MyComponent() {
  const {
    updates,
    latestUpdate,
    isConnected,
    error,
    reconnectAttempts
  } = useRealTimeUpdates('device-updates');

  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      {error && <p>Error: {error.message}</p>}
      {reconnectAttempts > 0 && (
        <p>Reconnecting... (attempt {reconnectAttempts}/5)</p>
      )}
    </div>
  );
}
```

## Configuration

### Environment Variables

```bash
# Primary endpoint (required)
REACT_APP_WEBSOCKET_ENDPOINT=wss://api.aquachain.com/ws

# Secondary endpoint (optional)
REACT_APP_WEBSOCKET_ENDPOINT_SECONDARY=wss://api-west.aquachain.com/ws

# Tertiary endpoint (optional)
REACT_APP_WEBSOCKET_ENDPOINT_TERTIARY=wss://api-eu.aquachain.com/ws

# Enable multi-region
REACT_APP_ENABLE_MULTI_REGION=true
```

### Service Options

```typescript
const websocketService = new WebSocketService({
  maxReconnectAttempts: 5,      // Max reconnection attempts
  reconnectDelay: 1000,          // Initial delay (ms)
  heartbeatInterval: 30000,      // Heartbeat interval (ms)
  enableMultiRegion: true        // Enable multi-region support
});
```

## Infrastructure

### Deploy Multi-Region Stack

```bash
cd infrastructure/cdk
cdk deploy AquaChainWebSocketMultiRegionStack
```

### Health Check Configuration

```python
health_check_config={
    "type": "HTTPS",
    "resource_path": "/health",
    "port": 443,
    "request_interval": 30,
    "failure_threshold": 3
}
```

### Route53 Weighted Routing

- **Primary (us-east-1)**: Weight 100
- **Secondary (us-west-2)**: Weight 50
- **Tertiary (eu-west-1)**: Weight 25

## Monitoring

### CloudWatch Metrics

```bash
# View WebSocket connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name ConnectCount \
  --dimensions Name=ApiId,Value=abc123

# View error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiId,Value=abc123
```

### Health Check Status

```bash
# Check health check status
aws route53 get-health-check-status \
  --health-check-id abc123
```

### Subscribe to Alerts

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:aquachain-websocket-health-prod \
  --protocol email \
  --notification-endpoint ops@aquachain.com
```

## Testing

### Test Connection Pooling

```typescript
// Multiple subscribers to same topic
websocketService.connect('test', handler1);
websocketService.connect('test', handler2);

// Verify only one connection
const connections = websocketService.getActiveConnections();
console.log(connections); // ['test']

// Check subscriber count
const status = websocketService.getConnectionStatus('test');
console.log(status.subscriberCount); // 2
```

### Test Reconnection

```typescript
// Simulate connection drop
const connection = websocketService.connections.get('test');
connection?.ws.close();

// Service will automatically reconnect
// Check reconnect attempts after 5 seconds
setTimeout(() => {
  const status = websocketService.getConnectionStatus('test');
  console.log('Attempts:', status.reconnectAttempts);
}, 5000);
```

### Test Multi-Region Failover

```bash
# Disable primary region
aws route53 update-health-check \
  --health-check-id abc123 \
  --disabled

# Client should failover to secondary
# Check logs for failover event
```

## Troubleshooting

### Connection Fails

1. Check WebSocket endpoint URL
2. Verify authentication token
3. Check CORS configuration
4. Review Lambda logs

### Reconnection Loop

1. Verify all regions are healthy
2. Check Route53 health checks
3. Review CloudWatch alarms
4. Check Lambda errors

### High Latency

1. Check Lambda cold starts
2. Enable provisioned concurrency
3. Optimize Lambda code
4. Add more regions

## Files Modified/Created

### Frontend
- ✅ `frontend/src/services/websocketService.ts` - WebSocket service with pooling
- ✅ `frontend/src/hooks/useRealTimeUpdates.ts` - Updated to use service
- ✅ `frontend/src/hooks/useRealTimeData.ts` - Updated to use service
- ✅ `frontend/src/contexts/NotificationContext.tsx` - Notification context
- ✅ `frontend/src/components/Notifications/ToastNotification.tsx` - Toast component

### Infrastructure
- ✅ `infrastructure/cdk/stacks/websocket_multi_region_stack.py` - Multi-region stack
- ✅ `WEBSOCKET_MULTI_REGION_GUIDE.md` - Deployment guide
- ✅ `WEBSOCKET_OPTIMIZATION_QUICK_REFERENCE.md` - This file

## Performance Metrics

### Before Optimization
- Multiple WebSocket connections per page
- No automatic reconnection
- Manual failover required
- No connection pooling

### After Optimization
- Single connection per topic (pooled)
- Automatic reconnection with backoff
- Automatic multi-region failover
- 5-minute region re-enablement

## Requirements Met

✅ **9.1**: WebSocket connection pooling implemented
✅ **9.2**: Automatic reconnection with exponential backoff
✅ **9.3**: Multi-region load balancing with Route53
✅ **9.4**: User notification after max reconnect attempts

## Next Steps

1. Deploy multi-region infrastructure
2. Configure Route53 health checks
3. Set up CloudWatch alarms
4. Test failover scenarios
5. Monitor connection metrics

## Support

For issues:
- Check CloudWatch logs: `/aws/apigateway/aquachain-websocket-prod`
- Review health checks in Route53 console
- Check SNS alerts
- Contact DevOps team
