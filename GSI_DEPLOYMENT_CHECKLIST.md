# DynamoDB GSI Deployment Checklist

## Pre-Deployment

### 1. Review Changes
- [ ] Review all GSI definitions in `infrastructure/cdk/stacks/data_stack.py`
- [ ] Review all GSI definitions in `infrastructure/dynamodb/tables.py`
- [ ] Verify attribute definitions match GSI requirements
- [ ] Check that billing mode is appropriate (PAY_PER_REQUEST recommended)

### 2. Backup Existing Data
- [ ] Enable point-in-time recovery on all tables (if not already enabled)
- [ ] Create on-demand backups of existing tables:
  ```bash
  aws dynamodb create-backup --table-name aquachain-devices --backup-name devices-pre-gsi
  aws dynamodb create-backup --table-name aquachain-readings --backup-name readings-pre-gsi
  aws dynamodb create-backup --table-name aquachain-users --backup-name users-pre-gsi
  ```

### 3. Test in Development
- [ ] Deploy to development environment first
- [ ] Verify GSI creation completes successfully
- [ ] Test all query functions with sample data
- [ ] Verify pagination works correctly
- [ ] Check CloudWatch metrics are being published

## Deployment Steps

### Step 1: Deploy Infrastructure Changes

#### Option A: Using CDK (Recommended)
```bash
cd infrastructure/cdk

# Review changes
cdk diff AquaChainDataStack

# Deploy changes
cdk deploy AquaChainDataStack --require-approval never

# Verify deployment
aws dynamodb describe-table --table-name aquachain-devices
aws dynamodb describe-table --table-name aquachain-readings
aws dynamodb describe-table --table-name aquachain-users
```

#### Option B: Using boto3 script
```bash
cd infrastructure/dynamodb
python tables.py
```

### Step 2: Wait for GSI Creation
- [ ] Monitor GSI creation status:
  ```bash
  # Check devices table GSIs
  aws dynamodb describe-table --table-name aquachain-devices \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]'
  
  # Check readings table GSIs
  aws dynamodb describe-table --table-name aquachain-readings \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]'
  
  # Check users table GSIs
  aws dynamodb describe-table --table-name aquachain-users \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]'
  ```

- [ ] Wait for all GSIs to show status "ACTIVE"
- [ ] Note: GSI creation can take several minutes to hours depending on table size

### Step 3: Deploy Lambda Functions

#### Deploy shared query module
```bash
cd lambda/shared
# Ensure dynamodb_queries.py and query_performance_monitor.py are included in deployment package
```

#### Deploy device management Lambda
```bash
cd lambda/device_management
# Package dependencies
pip install -r requirements.txt -t .
# Create deployment package
zip -r device-management.zip .
# Deploy
aws lambda update-function-code \
  --function-name aquachain-device-management \
  --zip-file fileb://device-management.zip
```

#### Deploy readings query Lambda
```bash
cd lambda/readings_query
# Package dependencies
pip install -r requirements.txt -t .
# Create deployment package
zip -r readings-query.zip .
# Deploy
aws lambda update-function-code \
  --function-name aquachain-readings-query \
  --zip-file fileb://readings-query.zip
```

#### Update user management Lambda
```bash
cd lambda/user_management
# Package dependencies
pip install -r requirements.txt -t .
# Create deployment package
zip -r user-management.zip .
# Deploy
aws lambda update-function-code \
  --function-name aquachain-user-management \
  --zip-file fileb://user-management.zip
```

### Step 4: Setup Performance Monitoring
```bash
# Set SNS topic ARN for alerts
export ALERT_TOPIC_ARN=arn:aws:sns:us-east-1:ACCOUNT_ID:aquachain-alerts

# Run monitoring setup script
cd infrastructure/monitoring
python query_performance_alarms.py
```

- [ ] Verify CloudWatch alarms created:
  ```bash
  aws cloudwatch describe-alarms --alarm-name-prefix "AquaChain-"
  ```

- [ ] Verify CloudWatch dashboard created:
  ```bash
  aws cloudwatch get-dashboard --dashboard-name AquaChain-Query-Performance
  ```

### Step 5: Update API Gateway (if applicable)
- [ ] Add new routes for device management endpoints
- [ ] Add new routes for readings query endpoints
- [ ] Add new routes for user query endpoints
- [ ] Deploy API Gateway changes
- [ ] Test endpoints with curl or Postman

## Post-Deployment Verification

### 1. Functional Testing

#### Test device queries
```bash
# Test query devices by user
curl "https://api.aquachain.com/devices/by-user?userId=test-user-123"

# Test query devices by status
curl "https://api.aquachain.com/devices/by-status?status=active"

# Test get device
curl "https://api.aquachain.com/devices/test-device-456"
```

#### Test readings queries
```bash
# Test query by metric type
curl "https://api.aquachain.com/readings/by-metric?deviceId=test-device&metricType=pH"

# Test query by alert level
curl "https://api.aquachain.com/readings/by-alert-level?alertLevel=critical"

# Test critical alerts
curl "https://api.aquachain.com/readings/critical-alerts?hours=24"
```

#### Test user queries
```bash
# Test query user by email
curl "https://api.aquachain.com/users/by-email?email=test@example.com"

# Test query users by organization
curl "https://api.aquachain.com/users/by-organization?organizationId=org-123"
```

### 2. Performance Verification
- [ ] Check CloudWatch metrics for query duration
- [ ] Verify average query duration < 100ms
- [ ] Verify p99 query duration < 500ms
- [ ] Check for any slow query warnings in logs

### 3. Pagination Testing
- [ ] Test pagination with limit parameter
- [ ] Verify lastKey parameter works correctly
- [ ] Test retrieving multiple pages
- [ ] Verify has_more flag is accurate

### 4. Error Handling Testing
- [ ] Test with invalid parameters
- [ ] Test with non-existent IDs
- [ ] Verify error responses are properly formatted
- [ ] Check error logs in CloudWatch

### 5. Monitoring Verification
- [ ] Check CloudWatch dashboard shows data
- [ ] Verify metrics are being published
- [ ] Test alarm by triggering slow query (if possible)
- [ ] Verify SNS notifications work

## Rollback Plan

### If GSI creation fails:
1. Check CloudWatch logs for error details
2. Verify table has sufficient capacity
3. Delete failed GSI:
   ```bash
   aws dynamodb update-table \
     --table-name TABLE_NAME \
     --global-secondary-index-updates '[{"Delete":{"IndexName":"INDEX_NAME"}}]'
   ```
4. Fix issue and retry

### If Lambda deployment fails:
1. Revert to previous Lambda version:
   ```bash
   aws lambda update-function-code \
     --function-name FUNCTION_NAME \
     --s3-bucket BACKUP_BUCKET \
     --s3-key PREVIOUS_VERSION.zip
   ```

### If queries are failing:
1. Check Lambda logs in CloudWatch
2. Verify GSI status is ACTIVE
3. Check IAM permissions for DynamoDB access
4. Revert Lambda functions if necessary

### Complete rollback:
1. Restore tables from backup:
   ```bash
   aws dynamodb restore-table-from-backup \
     --target-table-name aquachain-devices-restored \
     --backup-arn BACKUP_ARN
   ```
2. Update application to use restored tables
3. Investigate and fix issues before retry

## Performance Monitoring (First Week)

### Daily Checks
- [ ] Review CloudWatch dashboard
- [ ] Check for slow query alarms
- [ ] Review query duration trends
- [ ] Check RCU consumption
- [ ] Review error logs

### Weekly Review
- [ ] Analyze query performance metrics
- [ ] Identify optimization opportunities
- [ ] Adjust alarm thresholds if needed
- [ ] Review pagination usage patterns
- [ ] Document any issues and resolutions

## Success Criteria

- [ ] All GSIs created and status = ACTIVE
- [ ] All Lambda functions deployed successfully
- [ ] All API endpoints responding correctly
- [ ] Average query duration < 100ms
- [ ] P99 query duration < 500ms
- [ ] No GSI throttling events
- [ ] CloudWatch metrics publishing correctly
- [ ] CloudWatch alarms configured and working
- [ ] Pagination working correctly
- [ ] Error handling working as expected
- [ ] No increase in error rates
- [ ] RCU consumption reduced vs scan operations

## Documentation Updates

- [ ] Update API documentation with new endpoints
- [ ] Update developer guide with GSI usage examples
- [ ] Update operations runbook with monitoring procedures
- [ ] Update architecture diagrams with GSI information
- [ ] Create training materials for team

## Communication

### Before Deployment
- [ ] Notify team of deployment schedule
- [ ] Share deployment plan and timeline
- [ ] Identify deployment owner and backup

### During Deployment
- [ ] Post status updates in team channel
- [ ] Monitor for issues
- [ ] Be ready to rollback if needed

### After Deployment
- [ ] Announce successful deployment
- [ ] Share performance metrics
- [ ] Document any issues encountered
- [ ] Schedule knowledge sharing session

## Notes

### GSI Creation Time Estimates
- Empty table: 5-10 minutes
- Small table (<1GB): 10-30 minutes
- Medium table (1-10GB): 30-60 minutes
- Large table (>10GB): 1-4 hours

### Cost Considerations
- GSI creation is free
- GSI storage costs same as base table
- GSI queries consume RCUs from GSI capacity
- PAY_PER_REQUEST mode recommended for variable workloads

### Best Practices
- Deploy during low-traffic period
- Monitor closely for first 24 hours
- Keep rollback plan ready
- Test thoroughly in staging first
- Document all changes and decisions

## Sign-off

- [ ] Development Lead: _________________ Date: _______
- [ ] DevOps Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

## Deployment Log

| Date | Time | Action | Result | Notes |
|------|------|--------|--------|-------|
|      |      |        |        |       |
|      |      |        |        |       |
|      |      |        |        |       |
