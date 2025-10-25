# WebSocket Multi-Region Deployment Guide

This guide explains how to deploy and configure multi-region WebSocket APIs for high availability and geographic load balancing.

## Overview

The AquaChain WebSocket service supports multi-region deployment with:
- **Connection Pooling**: Reuses existing connections for the same topics
- **Automatic Reconnection**: Exponential backoff with max 5 attempts
- **Multi-Region Failover**: Automatic failover to healthy regions
- **Health Checks**: Route53 health checks for each region
- **User Notifications**: Toast notifications when connection fails

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Route53 DNS                              │
│              ws.aquachain.com (Weighted Routing)             │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼──────┐ ┌───▼──────┐
        │   Primary    │ │Secondary │ │ Tertiary │
        │  us-east-1   │ │us-west-2 │ │eu-west-1 │
        │  Weight: 100 │ │Weight: 50│ │Weight: 25│
        └──────────────┘ └──────────┘ └──────────┘
                │             │             │
        ┌───────▼──────┐ ┌───▼──────┐ ┌───▼──────┐
        │   Health     │ │  Health  │ │  Health  │
        │   Check      │ │  Check   │ │  Check   │
        └──────────────┘ └──────────┘ └──────────┘
```

## Prerequisites

1. **AWS Account** with permissions for:
   - API Gateway
   - Lambda
   - Route53
   - CloudWatch
   - SNS

2. **Domain Name** registered in Route53

3. **Multiple AWS Regions** configured

## Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Primary WebSocket endpoint (required)
REACT_APP_WEBSOCKET_ENDPOINT=wss://your-api-id.execute-api.us-east-1.amazonaws.com/prod

# Secondary WebSocket endpoint (optional)
REACT_APP_WEBSOCKET_ENDPOINT_SECONDARY=wss://your-api-id.execute-api.us-west-2.amazonaws.com/prod

# Tertiary WebSocket endpoint (optional)
REACT_APP_WEBSOCKET_ENDPOINT_TERTIARY=wss://your-api-id.execute-api.eu-west-1.amazonaws.com/prod

# Enable multi-region support
REACT_APP_ENABLE_MULTI_REGION=true
```

### 2. CDK Configuration

Update `infrastructure/cdk/config.json`:

```json
{
  "environment": "production",
  "enable_multi_region": true,
  "primary_region": "us-east-1",
  "secondary_region": "us-west-2",
  "tertiary_region": "eu-west-1",
  "hosted_zone_id": "Z1234567890ABC",
  "domain_name": "aquachain.com"
}
```

## Deployment Steps

### Step 1: Deploy Primary Region

```bash
cd infrastructure/cdk
export AWS_REGION=us-east-1
cdk deploy AquaChainApiStack --profile production
```

Note the WebSocket API endpoint from the output.

### Step 2: Deploy Secondary Region (Optional)

```bash
export AWS_REGION=us-west-2
cdk deploy AquaChainApiStack --profile production
```

### Step 3: Deploy Tertiary Region (Optional)

```bash
export AWS_REGION=eu-west-1
cdk deploy AquaChainApiStack --profile production
```

### Step 4: Deploy Multi-Region Stack

```bash
export AWS_REGION=us-east-1
cdk deploy AquaChainWebSocketMultiRegionStack --profile production
```

This creates:
- Route53 health checks for each region
- Weighted routing records
- CloudWatch alarms
- SNS topic for health alerts

### Step 5: Update Frontend Configuration

Update your frontend environment variables with the endpoints from each region.

### Step 6: Deploy Frontend

```bash
cd frontend
npm run build
npm run deploy
```

## Health Checks

### Route53 Health Checks

Each region has a health check that:
- Checks every 30 seconds
- Requires 3 consecutive failures to mark unhealthy
- Monitors the `/health` endpoint
- Uses HTTPS on port 443

### CloudWatch Alarms

Alarms are created for:
- **5XX Errors**: Triggers when error rate > 10 per minute
- **Connection Count**: Monitors active connections
- **Latency**: Tracks response times

### SNS Notifications

Subscribe to the health alert topic:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:aquachain-websocket-health-prod \
  --protocol email \
  --notification-endpoint ops@aquachain.com
```

## Client-Side Behavior

### Connection Pooling

The WebSocketService automatically:
1. Reuses existing connections for the same topic
2. Maintains a connection map
3. Cleans up connections on unmount

```typescript
// Multiple components can subscribe to the same topic
// Only one WebSocket connection is created
websocketService.connect('device-updates', handleUpdate1);
websocketService.connect('device-updates', handleUpdate2);
```

### Automatic Reconnection

When a connection drops:
1. Attempts reconnection with exponential backoff
2. Max 5 attempts (1s, 2s, 4s, 8s, 16s delays)
3. After max attempts, marks region as unhealthy
4. Tries next available region
5. Shows user notification if all regions fail

### Region Failover

The service automatically:
1. Tries primary region first (highest weight)
2. Falls back to secondary if primary is unhealthy
3. Falls back to tertiary if secondary is unhealthy
4. Re-enables regions after 5 minutes

## Monitoring

### CloudWatch Dashboard

View the WebSocket health dashboard:

```bash
aws cloudwatch get-dashboard \
  --dashboard-name aquachain-websocket-health-prod
```

### Metrics to Monitor

1. **ConnectCount**: Number of active connections
2. **MessageCount**: Messages sent/received
3. **5XXError**: Server errors
4. **IntegrationLatency**: Lambda execution time
5. **ClientError**: 4XX errors

### Logs

WebSocket logs are in CloudWatch Logs:

```bash
aws logs tail /aws/apigateway/aquachain-websocket-prod --follow
```

## Testing

### Test Connection Pooling

```typescript
import { websocketService } from './services/websocketService';

// Connect multiple subscribers to same topic
const handler1 = (data) => console.log('Handler 1:', data);
const handler2 = (data) => console.log('Handler 2:', data);

websocketService.connect('test-topic', handler1);
websocketService.connect('test-topic', handler2);

// Check connection status
const status = websocketService.getConnectionStatus('test-topic');
console.log('Subscribers:', status.subscriberCount); // Should be 2

// Disconnect one subscriber
websocketService.disconnect('test-topic', handler1);
// Connection stays open for handler2
```

### Test Automatic Reconnection

```typescript
// Simulate connection drop
const ws = websocketService.connections.get('test-topic')?.ws;
ws?.close();

// Service will automatically attempt reconnection
// Check reconnect attempts
setTimeout(() => {
  const status = websocketService.getConnectionStatus('test-topic');
  console.log('Reconnect attempts:', status.reconnectAttempts);
}, 5000);
```

### Test Multi-Region Failover

```bash
# Disable primary region health check
aws route53 update-health-check \
  --health-check-id abc123 \
  --disabled

# Client should automatically failover to secondary region
# Check CloudWatch logs for failover events
```

## Troubleshooting

### Connection Fails Immediately

**Symptom**: WebSocket connection closes immediately after opening

**Solutions**:
1. Check CORS configuration in API Gateway
2. Verify authentication token is valid
3. Check Lambda function logs for errors
4. Ensure security groups allow WebSocket traffic

### Reconnection Loop

**Symptom**: Client keeps reconnecting without success

**Solutions**:
1. Check if all regions are healthy
2. Verify Route53 health checks are passing
3. Check CloudWatch alarms for issues
4. Review Lambda function errors

### High Latency

**Symptom**: Messages take long to arrive

**Solutions**:
1. Check Lambda cold starts
2. Enable provisioned concurrency
3. Optimize Lambda function code
4. Consider adding more regions

### Region Not Failing Over

**Symptom**: Client stays connected to unhealthy region

**Solutions**:
1. Verify health check configuration
2. Check Route53 TTL settings (should be low)
3. Ensure client-side health check is enabled
4. Review CloudWatch metrics

## Best Practices

1. **Use Connection Pooling**: Always use the WebSocketService instead of creating raw WebSocket connections

2. **Handle Errors Gracefully**: Show user-friendly notifications when connections fail

3. **Monitor Health**: Set up CloudWatch alarms and SNS notifications

4. **Test Failover**: Regularly test failover scenarios

5. **Optimize Regions**: Choose regions close to your users

6. **Set Appropriate TTLs**: Use low TTL (60s) for DNS records to enable fast failover

7. **Use Heartbeats**: Send periodic ping messages to keep connections alive

8. **Clean Up Connections**: Always disconnect when components unmount

## Cost Optimization

1. **Connection Pooling**: Reduces number of WebSocket connections
2. **Regional Deployment**: Only deploy regions you need
3. **Health Check Frequency**: Balance between cost and failover speed
4. **Lambda Provisioned Concurrency**: Only for high-traffic functions

## Security

1. **Authentication**: Always authenticate WebSocket connections
2. **Authorization**: Verify user permissions for each topic
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Encryption**: Use WSS (WebSocket Secure) only
5. **CORS**: Configure CORS properly for your domain

## Support

For issues or questions:
- Check CloudWatch logs
- Review health check status
- Contact DevOps team
- Create GitHub issue

## References

- [AWS API Gateway WebSocket APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
- [Route53 Health Checks](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)
- [WebSocket API Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api-best-practices.html)
