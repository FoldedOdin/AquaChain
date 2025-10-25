# CloudFront CDN Quick Reference

Quick reference for CloudFront CDN configuration and deployment.

## Quick Deploy

```bash
# Set environment variables
export FRONTEND_BUCKET_NAME=aquachain-frontend-production
export CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
export AWS_REGION=us-east-1

# Deploy
cd frontend
npm run deploy:cloudfront
```

## Cache Policies

| Path Pattern | TTL | Cache-Control | Use Case |
|-------------|-----|---------------|----------|
| `/static/*` | 365 days | `public, max-age=31536000, immutable` | JS, CSS, images, fonts |
| `*.html` | 5 minutes | `public, max-age=300, must-revalidate` | HTML files |
| `/api/*` | 0 seconds | Dynamic | API endpoints (no caching) |
| `*.json` | 1 hour | `public, max-age=3600` | Manifest files |

## Distribution Behaviors

### Default Behavior (SPA)
- **Origin**: S3 bucket with OAI
- **Viewer Protocol**: HTTPS only
- **Compression**: Gzip + Brotli
- **Cache**: 24 hours default

### `/api/*` Behavior
- **Origin**: API Gateway (HTTPS)
- **Viewer Protocol**: HTTPS only
- **Compression**: Gzip + Brotli
- **Cache**: Disabled (0 seconds)
- **Methods**: All (GET, POST, PUT, DELETE, etc.)

### `/static/*` Behavior
- **Origin**: S3 bucket with OAI
- **Viewer Protocol**: HTTPS only
- **Compression**: Gzip + Brotli
- **Cache**: 365 days

## Common Commands

### Deploy
```bash
npm run deploy:cloudfront                 # Full deployment
npm run deploy:cloudfront:dry-run         # Test without changes
```

### Cache Invalidation
```bash
# Invalidate all
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"

# Invalidate specific paths
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/index.html" "/static/js/*"

# Check status
aws cloudfront get-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --id <invalidation-id>
```

### Manual S3 Upload
```bash
# Sync files
aws s3 sync build/ s3://$FRONTEND_BUCKET_NAME/ --delete

# Set cache headers for static assets
aws s3 cp s3://$FRONTEND_BUCKET_NAME/static/ s3://$FRONTEND_BUCKET_NAME/static/ \
  --recursive \
  --metadata-directive REPLACE \
  --cache-control "public, max-age=31536000, immutable"
```

## CDK Stack Configuration

### Create CloudFront Stack
```python
from infrastructure.cdk.stacks.cloudfront_stack import AquaChainCloudFrontStack

# In your CDK app
cloudfront_stack = AquaChainCloudFrontStack(
    app, "CloudFrontStack",
    config={
        'environment': 'production',
        'domain_name': 'app.aquachain.com',
        'hosted_zone_id': 'Z1234567890ABC'
    },
    api_gateway_domain='api.aquachain.com',  # API Gateway domain
    env=aws_env
)
```

### Deploy CDK Stack
```bash
cd infrastructure/cdk
cdk deploy CloudFrontStack
```

## Security Headers

CloudFront automatically adds:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

## WAF Protection

- **Rate Limiting**: 2000 requests per 5 minutes per IP
- **AWS Managed Rules**: Common Rule Set
- **AWS Managed Rules**: Known Bad Inputs
- **Scope**: CLOUDFRONT (global)

## Monitoring

### CloudWatch Metrics
```bash
# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=$CLOUDFRONT_DISTRIBUTION_ID \
  --start-time 2025-10-25T00:00:00Z \
  --end-time 2025-10-25T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Key Metrics
- **Requests**: Total requests
- **BytesDownloaded**: Data transferred
- **4xxErrorRate**: Client errors
- **5xxErrorRate**: Server errors
- **CacheHitRate**: Cache efficiency

## Troubleshooting

### Issue: 403 Forbidden
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket $FRONTEND_BUCKET_NAME

# Verify OAI permissions
aws cloudfront get-cloud-front-origin-access-identity \
  --id <oai-id>
```

### Issue: Stale Content
```bash
# Force invalidation
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"

# Hard refresh browser (Ctrl+Shift+R)
```

### Issue: Slow Performance
```bash
# Check bundle size
npm run build:check

# Analyze bundle
npm run build:analyze

# Check cache hit rate in CloudWatch
```

## Performance Targets

- **Initial Bundle Size**: < 500KB
- **Page Load Time**: < 3 seconds
- **Cache Hit Rate**: > 80%
- **Time to First Byte**: < 200ms
- **Lighthouse Score**: > 90

## Cost Estimates

### Monthly Costs (Typical)
- **Data Transfer**: 100GB × $0.085 = $8.50
- **Requests**: 1M × $0.0075/10K = $0.75
- **Invalidations**: Free (< 1000 paths)
- **Total**: ~$10/month

### Cost Optimization
1. Increase cache hit rate
2. Enable compression
3. Use Price Class 100 (US, Canada, Europe)
4. Minimize invalidations

## CI/CD Integration

### GitHub Actions Secrets
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
FRONTEND_BUCKET_NAME
CLOUDFRONT_DISTRIBUTION_ID
```

### Deployment Workflow
```yaml
- name: Deploy to CloudFront
  run: npm run deploy:cloudfront
  env:
    FRONTEND_BUCKET_NAME: ${{ secrets.FRONTEND_BUCKET_NAME }}
    CLOUDFRONT_DISTRIBUTION_ID: ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}
```

## DNS Configuration

### Route53 A Record
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.aquachain.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "d1234567890abc.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

## Best Practices

1. ✅ Use versioned URLs for static assets
2. ✅ Set appropriate cache TTLs
3. ✅ Enable compression (Gzip + Brotli)
4. ✅ Use HTTPS only
5. ✅ Monitor cache hit rate
6. ✅ Minimize invalidations
7. ✅ Test with dry-run before deploying
8. ✅ Automate deployments via CI/CD

## Related Documentation

- [CloudFront Deployment Guide](frontend/CLOUDFRONT_DEPLOYMENT_GUIDE.md)
- [Performance Quick Reference](frontend/PERFORMANCE_QUICK_REFERENCE.md)
- [CDK Stack Documentation](infrastructure/cdk/stacks/cloudfront_stack.py)

## Support

- AWS CloudFront Docs: https://docs.aws.amazon.com/cloudfront/
- Project Issues: https://github.com/aquachain/issues
- AWS Support: https://console.aws.amazon.com/support/
