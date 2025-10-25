# ElastiCache Redis Caching - Quick Reference

## Quick Start

### Deploy Cache Infrastructure
```bash
cd infrastructure/cdk
cdk deploy AquaChain-Cache-dev
```

### Get Redis Endpoint
```bash
aws cloudformation describe-stacks \
  --stack-name AquaChain-Cache-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
  --output text
```

### Update Lambda Environment
```bash
export REDIS_ENDPOINT=<your-redis-endpoint>
aws lambda update-function-configuration \
  --function-name <function-name> \
  --environment "Variables={REDIS_ENDPOINT=$REDIS_ENDPOINT}"
```

## Using CacheService in Lambda

### Import and Initialize
```python
from cache_service import get_cache_service

cache = get_cache_service()
```

### Basic Operations
```python
# Set value with 5-minute TTL
cache.set('device:123', device_data, ttl=300)

# Get value
data = cache.get('device:123')

# Delete value
cache.delete('device:123')

# Check if exists
if cache.exists('device:123'):
    print("Key exists")
```

### Pattern-Based Invalidation
```python
# Invalidate all device caches
cache.invalidate_pattern('device:*')

# Invalidate all user profiles
cache.invalidate_pattern('user:profile:*')
```

### Batch Operations
```python
# Get multiple keys
keys = ['device:1', 'device:2', 'device:3']
results = cache.get_many(keys)

# Set multiple keys
data = {
    'device:1': {'status': 'active'},
    'device:2': {'status': 'inactive'}
}
cache.set_many(data, ttl=300)
```

## Cache Key Patterns

| Data Type | Pattern | TTL | Example |
|-----------|---------|-----|---------|
| Device | `device:{device_id}` | 300s | `device:abc-123` |
| User Profile | `user:profile:{user_id}` | 600s | `user:profile:user-456` |
| Latest Reading | `reading:latest:{device_id}` | 60s | `reading:latest:abc-123` |

## Cache Invalidation Rules

### When to Invalidate
- ✅ After UPDATE operations
- ✅ After DELETE operations
- ✅ After status changes
- ❌ After READ operations
- ❌ On cache miss

### Example: Update with Invalidation
```python
def update_device(device_id, updates):
    # Update database
    result = dynamodb.update_item(...)
    
    # Invalidate cache
    cache.delete(f'device:{device_id}')
    
    return result
```

## Monitoring Cache Performance

### Check Cache Stats
```python
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Memory used: {stats['used_memory']}")
```

### CloudWatch Logs
Look for these log entries:
```json
{
  "message": "Device found in cache",
  "cache_hit": true,
  "device_id": "abc-123"
}
```

## Troubleshooting

### Cache Not Working
1. Check `REDIS_ENDPOINT` environment variable is set
2. Verify Lambda is in same VPC as Redis
3. Check security group allows port 6379
4. Review CloudWatch logs for connection errors

### High Miss Rate
1. Increase TTL values
2. Implement cache warming
3. Review access patterns
4. Check invalidation frequency

### Stale Data
1. Reduce TTL values
2. Ensure invalidation on writes
3. Use pattern-based invalidation for related data

## Configuration by Environment

| Environment | Node Type | Nodes | Snapshots |
|------------|-----------|-------|-----------|
| Dev | cache.t3.micro | 1 | None |
| Staging | cache.t3.small | 1 | 7 days |
| Production | cache.m5.large | 2 | 14 days |

## Best Practices

1. **Always set TTL** - Prevent stale data accumulation
2. **Invalidate on writes** - Keep cache consistent with database
3. **Use meaningful keys** - Follow naming patterns for easy management
4. **Handle cache failures gracefully** - Application should work without cache
5. **Monitor hit rates** - Aim for 70%+ hit rate
6. **Log cache operations** - Use structured logging for debugging

## Common Patterns

### Cache-Aside (Lazy Loading)
```python
def get_device(device_id):
    # Try cache first
    cached = cache.get(f'device:{device_id}')
    if cached:
        return cached
    
    # Cache miss - fetch from DB
    device = db.get_item(device_id)
    
    # Store in cache
    cache.set(f'device:{device_id}', device, ttl=300)
    
    return device
```

### Write-Through
```python
def update_device(device_id, updates):
    # Update database
    device = db.update_item(device_id, updates)
    
    # Update cache
    cache.set(f'device:{device_id}', device, ttl=300)
    
    return device
```

### Write-Behind (Invalidate)
```python
def update_device(device_id, updates):
    # Update database
    device = db.update_item(device_id, updates)
    
    # Invalidate cache (next read will refresh)
    cache.delete(f'device:{device_id}')
    
    return device
```

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Cache hit rate | >70% | Monitor |
| Cache latency | <10ms | ~5ms |
| DynamoDB reduction | >70% | Monitor |
| API latency improvement | >80% | Monitor |

## Security

- ✅ Redis in private VPC subnets
- ✅ Security group restricts access to Lambda
- ✅ No public internet access
- ⚠️ Consider enabling encryption at rest (production)
- ⚠️ Consider enabling encryption in transit (production)
- ⚠️ Consider Redis AUTH password (production)

## Cost Optimization

1. **Right-size nodes** - Start small, scale up based on metrics
2. **Use reserved instances** - Save 30-50% for production
3. **Monitor memory usage** - Upgrade only when needed
4. **Optimize TTL values** - Balance freshness vs. hit rate
5. **Review cached data** - Don't cache everything

## Related Documentation

- Full implementation: `TASK_12_CACHING_IMPLEMENTATION.md`
- Design document: `.kiro/specs/phase-4-medium-priority/design.md`
- Cache service code: `lambda/shared/cache_service.py`
- CDK stack: `infrastructure/cdk/stacks/cache_stack.py`
