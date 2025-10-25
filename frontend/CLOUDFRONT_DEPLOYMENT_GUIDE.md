# CloudFront Deployment Guide

This guide explains how to deploy the AquaChain frontend to AWS S3 with CloudFront CDN.

## Overview

The CloudFront deployment provides:
- **Global CDN**: Fast content delivery worldwide
- **Optimized Caching**: Long TTL for static assets (365 days), no caching for API endpoints
- **Automatic Invalidation**: Cache invalidation on deployments
- **Compression**: Gzip and Brotli compression for all responses
- **Security**: HTTPS-only, security headers, WAF protection

## Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      CloudFront Distribution        │
│  ┌──────────────┬────────────────┐  │
│  │  /static/*   │    /api/*      │  │
│  │  (365 days)  │  (no cache)    │  │
│  └──────┬───────┴────────┬───────┘  │
└─────────┼────────────────┼──────────┘
          │                │
          ▼                ▼
    ┌─────────┐      ┌──────────┐
    │   S3    │      │   API    │
    │ Bucket  │      │ Gateway  │
    └─────────┘      └──────────┘
```

## Prerequisites

1. **AWS CLI**: Install and configure AWS CLI
   ```bash
   aws --version
   aws configure
   ```

2. **AWS Credentials**: Ensure you have appropriate IAM permissions:
   - `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on the frontend bucket
   - `cloudfront:CreateInvalidation` on the distribution

3. **Environment Variables**: Set the following:
   ```bash
   export FRONTEND_BUCKET_NAME=aquachain-frontend-production
   export CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
   export AWS_REGION=us-east-1
   ```

## Deployment Steps

### 1. Quick Deployment

Deploy to CloudFront with a single command:

```bash
npm run deploy:cloudfront
```

This will:
1. Build the application
2. Upload files to S3
3. Set appropriate cache headers
4. Invalidate CloudFront cache

### 2. Dry Run

Test the deployment without making changes:

```bash
npm run deploy:cloudfront:dry-run
```

### 3. Manual Deployment

For more control, use the AWS CLI directly:

```bash
# Build the application
npm run build

# Upload to S3
aws s3 sync build/ s3://$FRONTEND_BUCKET_NAME/ --delete

# Set cache headers for static assets (365 days)
aws s3 cp s3://$FRONTEND_BUCKET_NAME/static/ s3://$FRONTEND_BUCKET_NAME/static/ \
  --recursive \
  --metadata-directive REPLACE \
  --cache-control "public, max-age=31536000, immutable"

# Set cache headers for HTML files (5 minutes)
aws s3 cp s3://$FRONTEND_BUCKET_NAME/ s3://$FRONTEND_BUCKET_NAME/ \
  --recursive \
  --exclude "*" \
  --include "*.html" \
  --metadata-directive REPLACE \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"
```

## Cache Configuration

### Static Assets (`/static/*`)
- **TTL**: 365 days
- **Cache-Control**: `public, max-age=31536000, immutable`
- **Compression**: Gzip + Brotli
- **Use Case**: JavaScript, CSS, images, fonts

### HTML Files
- **TTL**: 5 minutes
- **Cache-Control**: `public, max-age=300, must-revalidate`
- **Compression**: Gzip + Brotli
- **Use Case**: index.html, other HTML files

### API Endpoints (`/api/*`)
- **TTL**: 0 seconds (no caching)
- **Cache-Control**: Dynamic based on API response
- **Compression**: Gzip + Brotli
- **Use Case**: All API requests

### JSON Files
- **TTL**: 1 hour
- **Cache-Control**: `public, max-age=3600`
- **Compression**: Gzip + Brotli
- **Use Case**: manifest.json, asset-manifest.json

## Cache Invalidation

### Automatic Invalidation

The deployment script automatically invalidates the CloudFront cache for all paths (`/*`).

### Manual Invalidation

Invalidate specific paths:

```bash
# Invalidate all paths
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"

# Invalidate specific paths
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/index.html" "/static/js/*"
```

### Check Invalidation Status

```bash
aws cloudfront get-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --id <invalidation-id>
```

## DNS Configuration

### Using Custom Domain

If you have a custom domain configured:

1. **Certificate**: Ensure SSL certificate is created in `us-east-1`
2. **Route53**: Create A and AAAA records pointing to CloudFront
3. **CloudFront**: Add domain to distribution's alternate domain names

Example Route53 configuration:
```bash
# A record (IPv4)
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

## Monitoring

### CloudWatch Metrics

Monitor CloudFront performance:
- **Requests**: Total number of requests
- **BytesDownloaded**: Total bytes served
- **ErrorRate**: 4xx and 5xx error rates
- **CacheHitRate**: Percentage of requests served from cache

### CloudFront Logs

Access logs are stored in S3:
```
s3://aquachain-cloudfront-logs-production/cloudfront/
```

Analyze logs:
```bash
# Download recent logs
aws s3 sync s3://aquachain-cloudfront-logs-production/cloudfront/ ./logs/

# Analyze with awslogs or similar tools
```

## Troubleshooting

### Issue: Cache Not Invalidating

**Solution**: Wait 5-10 minutes for invalidation to complete, or check invalidation status:
```bash
aws cloudfront list-invalidations --distribution-id $CLOUDFRONT_DISTRIBUTION_ID
```

### Issue: 403 Forbidden Errors

**Solution**: Check S3 bucket policy and CloudFront OAI permissions:
```bash
aws s3api get-bucket-policy --bucket $FRONTEND_BUCKET_NAME
```

### Issue: Stale Content After Deployment

**Solution**: 
1. Verify cache headers are set correctly
2. Create a new invalidation
3. Check browser cache (hard refresh with Ctrl+Shift+R)

### Issue: Slow Initial Load

**Solution**:
1. Check bundle size: `npm run build:check`
2. Verify code splitting is working
3. Check CloudFront cache hit rate
4. Consider using Lambda@Edge for optimization

## Performance Optimization

### Bundle Size

Keep bundle size under 500KB:
```bash
npm run build:check
```

### Code Splitting

Verify lazy loading is working:
```bash
npm run build:analyze
```

### Cache Hit Rate

Target 80%+ cache hit rate:
- Monitor in CloudWatch
- Adjust cache policies if needed
- Use versioned URLs for static assets

## Security

### HTTPS Only

All traffic is forced to HTTPS via CloudFront viewer protocol policy.

### Security Headers

CloudFront adds security headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `X-XSS-Protection`
- `Referrer-Policy`

### WAF Protection

CloudFront distribution is protected by AWS WAF:
- Rate limiting (2000 requests per 5 minutes)
- AWS Managed Rules (Common Rule Set)
- AWS Managed Rules (Known Bad Inputs)

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/deploy.yml`:

```yaml
name: Deploy to CloudFront

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
        
      - name: Build
        run: npm run build
        working-directory: ./frontend
        
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Deploy to CloudFront
        run: npm run deploy:cloudfront
        working-directory: ./frontend
        env:
          FRONTEND_BUCKET_NAME: ${{ secrets.FRONTEND_BUCKET_NAME }}
          CLOUDFRONT_DISTRIBUTION_ID: ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}
```

## Cost Optimization

### CloudFront Pricing

- **Data Transfer**: $0.085/GB (first 10TB)
- **Requests**: $0.0075 per 10,000 HTTPS requests
- **Invalidations**: First 1,000 paths free per month

### Tips to Reduce Costs

1. **Optimize Cache Hit Rate**: Reduce origin requests
2. **Use Compression**: Reduce data transfer
3. **Limit Invalidations**: Batch invalidations when possible
4. **Use Price Class 100**: Serve from US, Canada, Europe only

## Best Practices

1. **Version Static Assets**: Use content hashing in filenames
2. **Minimize Invalidations**: Use versioned URLs instead
3. **Monitor Performance**: Track Core Web Vitals
4. **Test Before Deploy**: Use dry-run mode
5. **Automate Deployments**: Use CI/CD pipelines
6. **Set Appropriate TTLs**: Balance freshness and performance
7. **Use Compression**: Enable Gzip and Brotli
8. **Monitor Costs**: Set up billing alerts

## Additional Resources

- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [CloudFront Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/best-practices.html)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review CloudFront access logs
3. Contact AWS Support
4. Open an issue in the project repository
