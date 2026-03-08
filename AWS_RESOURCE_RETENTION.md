# AWS Resource Retention Guide

## Current Deployment Status

**Dashboard URL**: https://nyayamrit-dashboard-public.s3.ap-south-1.amazonaws.com/index.html
**API Endpoint**: https://74u84pctjh.execute-api.ap-south-1.amazonaws.com/query
**Region**: ap-south-1 (Mumbai)
**Deployment Date**: March 8, 2026

## Resources to Keep Active (Minimum 2 Months)

### 1. Lambda Function
- **Name**: `nyayamrit-query-processor`
- **Runtime**: Python 3.11
- **Memory**: 2048 MB
- **Timeout**: 30 seconds
- **Status**: Active
- **Action**: No action needed - Lambda functions remain active indefinitely

### 2. S3 Buckets
- **Dashboard Bucket**: `nyayamrit-dashboard-public`
  - Contains: `index.html` (dashboard)
  - Public access enabled
  - Action: No action needed - S3 buckets remain active indefinitely

- **Knowledge Graph Bucket**: `nyayamrit-legal-docs-f4a8b2c3`
  - Contains: Knowledge graph JSON files
  - Action: No action needed

### 3. API Gateway
- **Type**: HTTP API
- **Endpoint**: https://74u84pctjh.execute-api.ap-south-1.amazonaws.com
- **Route**: POST /query
- **Action**: No action needed - API Gateway remains active indefinitely

### 4. DynamoDB Table
- **Name**: `QueryLogs`
- **Purpose**: Query logging
- **Action**: No action needed - DynamoDB tables remain active indefinitely

### 5. IAM Role
- **Name**: `NyayamritLambdaExecutionRole`
- **Purpose**: Lambda execution permissions
- **Action**: No action needed

## Cost Monitoring

### Expected Monthly Costs (Low Usage)
- **Lambda**: ~$0-5 (within free tier for low usage)
- **S3**: ~$0-1 (minimal storage)
- **API Gateway**: ~$0-3 (within free tier for first 1M requests)
- **DynamoDB**: ~$0-2 (on-demand pricing)
- **Bedrock**: ~$10-50 (depends on query volume)

**Total**: ~$10-60/month

### Free Tier Coverage (First 12 Months)
- Lambda: 1M requests/month free
- S3: 5GB storage free
- API Gateway: 1M requests/month free
- DynamoDB: 25GB storage free

## Monitoring & Alerts

### Set Up CloudWatch Alarms (Recommended)
```bash
# Monitor Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name nyayamrit-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=nyayamrit-query-processor \
  --evaluation-periods 1 \
  --region ap-south-1
```

### Check Resource Status
```bash
# Check Lambda status
aws lambda get-function --function-name nyayamrit-query-processor --region ap-south-1

# Check S3 bucket
aws s3 ls s3://nyayamrit-dashboard-public --region ap-south-1

# Check API Gateway
aws apigatewayv2 get-apis --region ap-south-1
```

## Retention Checklist

- [ ] All resources are in `ap-south-1` region
- [ ] Lambda function is active and deployed
- [ ] S3 buckets contain required files
- [ ] API Gateway endpoint is accessible
- [ ] DynamoDB table exists
- [ ] IAM role has correct permissions
- [ ] CloudWatch logs are being generated

## Important Notes

1. **No Automatic Deletion**: AWS resources do not auto-delete unless explicitly configured
2. **Billing**: Monitor AWS billing dashboard to avoid unexpected charges
3. **Free Tier**: Most services covered by free tier for low usage
4. **Backup**: Knowledge graph data is stored in S3 (durable)
5. **Logs**: CloudWatch logs retained for 7 days by default

## Emergency Contacts

If the site goes down:
1. Check Lambda function status
2. Check API Gateway endpoint
3. Check S3 bucket public access
4. Review CloudWatch logs for errors
5. Verify IAM role permissions

## Estimated Longevity

With current configuration and assuming low-moderate usage:
- **Minimum**: 2 months (guaranteed)
- **Expected**: 6-12 months (within free tier)
- **Maximum**: Indefinite (as long as AWS account is active)

The site will remain active as long as:
1. AWS account remains in good standing
2. No manual deletion of resources
3. Billing is current (if exceeding free tier)
