# Requirements Document: AWS Hackathon Integration

## Introduction

This document specifies requirements for integrating Nyayamrit with AWS for a **hackathon demo**. Focus: working AWS deployment in 2-3 days, not enterprise production.

## Success Criteria

✅ System runs on AWS (not localhost)  
✅ Uses AWS Bedrock (Claude 3 Haiku)  
✅ Accessible via public URL  
✅ Zero-hallucination guarantee maintained  
✅ Demo-ready with 5-10 test queries  

## BUILD NOW - 8 Core Requirements

### Requirement 1: AWS Bedrock Integration

**Goal**: Replace Gemini/OpenAI with AWS Bedrock

#### Acceptance Criteria

1. Create `BedrockProvider` class in `llm_integration/providers.py`
2. Use Claude 3 Haiku model (`anthropic.claude-3-haiku-20240307-v1:0`)
3. Use boto3 SDK with IAM role authentication
4. Implement retry logic (3 attempts, 1s delay)
5. Maintain existing prompt templates
6. Test: "What are my consumer rights?" returns all 6 rights
7. Verify zero-hallucination guarantee works

---

### Requirement 2: Graph Database Layer

**Goal**: Store knowledge graph in AWS

**Decision**: Keep existing JSON files (fastest for hackathon)

#### Acceptance Criteria

1. Upload JSON files to S3 bucket
2. Lambda loads JSON at startup
3. Use existing in-memory graph traversal code
4. Test: Graph queries return correct results

**Alternative**: Use Neptune if you want full AWS purity (adds 1-2 days)

---

### Requirement 3: Lambda + API Gateway

**Goal**: Deploy as serverless function with public URL

#### Acceptance Criteria

1. Package all code in single Lambda function
2. Set timeout: 30 seconds
3. Set memory: 2048 MB
4. Create API Gateway REST API
5. Add POST `/query` endpoint
6. Enable CORS
7. Add basic rate limiting (100 req/min)
8. Get public URL: `https://xxx.execute-api.region.amazonaws.com/prod/query`
9. Test with curl/Postman

---

### Requirement 4: S3 Document Storage

**Goal**: Store PDF files and JSON in S3

#### Acceptance Criteria

1. Create S3 bucket: `nyayamrit-legal-docs-{random}`
2. Enable versioning
3. Upload `consumer_protection_act_2019.pdf`
4. Upload knowledge graph JSON files
5. Set bucket policy for Lambda read access
6. Test: Lambda can download files

---

### Requirement 5: DynamoDB Logging

**Goal**: Log queries for demo

#### Acceptance Criteria

1. Create DynamoDB table: `QueryLogs`
2. Partition key: `query_id` (string)
3. Sort key: `timestamp` (number)
4. Attributes: `user_query`, `response`, `confidence_score`
5. Use on-demand billing
6. Lambda writes log after each query
7. Test: Query DynamoDB to see logs

---

### Requirement 6: Basic Testing

**Goal**: Verify system works on AWS

#### Acceptance Criteria

1. Test query: "What are my consumer rights?"
2. Verify response includes all 6 rights
3. Verify citations are correct
4. Verify confidence score > 0.8
5. Test 5-10 different queries
6. Verify zero hallucinations
7. Check CloudWatch logs show requests
8. Check DynamoDB has query logs
9. Measure response time (< 5 seconds acceptable)

---

### Requirement 7: Basic Security

**Goal**: Use AWS best practices

#### Acceptance Criteria

1. Use IAM roles (not access keys)
2. Deploy in `ap-south-1` (Mumbai) region
3. Use HTTPS for API Gateway
4. Set least-privilege IAM policies
5. Enable CloudWatch logging
6. Don't log sensitive data

---

### Requirement 8: Basic Observability

**Goal**: Monitor system with CloudWatch

#### Acceptance Criteria

1. Lambda logs to CloudWatch (automatic)
2. Log request IDs for correlation
3. Log errors with stack traces
4. Create basic CloudWatch dashboard
5. Monitor: invocations, errors, duration
6. Retain logs for 30 days

---

## 3-Day Implementation Checklist

### Day 1: AWS Setup & Bedrock
- [ ] Create AWS account / use existing
- [ ] Set up IAM role for Lambda
- [ ] Create `BedrockProvider` class
- [ ] Test Bedrock API with sample query
- [ ] Verify zero-hallucination still works

### Day 2: Lambda & API Gateway
- [ ] Package code for Lambda deployment
- [ ] Create Lambda function
- [ ] Create API Gateway
- [ ] Test `/query` endpoint
- [ ] Deploy web interface to S3 static hosting

### Day 3: Storage & Polish
- [ ] Upload PDFs and JSON to S3
- [ ] Create DynamoDB table for logs
- [ ] Test end-to-end flow
- [ ] Fix bugs
- [ ] Prepare demo script

---

## What You DON'T Need

❌ Load testing (10k users)  
❌ GuardDuty, AWS Config, WAF  
❌ 99.9% SLA measurement  
❌ Well-Architected review  
❌ Savings Plans / Reserved Instances  
❌ 80% code coverage  
❌ Chaos engineering  
❌ 1M node guarantee  
❌ SDK generation  
❌ Developer portal  
❌ Quarterly DR drills  
❌ Cross-region replication  
❌ ElastiCache caching  
❌ CloudFront CDN  
❌ Secrets Manager rotation  
❌ X-Ray tracing  
❌ EventBridge workflows  
❌ Cognito authentication (optional)  

---

## Future Enterprise Roadmap

The following can be added later for production:

- ElastiCache Redis caching
- RDS PostgreSQL for analytics
- CloudFront CDN for global users
- WAF for security
- Secrets Manager for credential rotation
- X-Ray for distributed tracing
- EventBridge for event-driven workflows
- Cognito for user authentication
- Multi-region deployment
- Advanced monitoring and alerting

---

## Glossary

- **Bedrock**: AWS managed LLM service (Claude 3 Haiku)
- **Lambda**: Serverless function (runs query pipeline)
- **API Gateway**: REST API endpoint (public URL)
- **S3**: Object storage (PDF files, JSON)
- **DynamoDB**: NoSQL database (audit logs)
- **CloudWatch**: Basic logging (included with Lambda)
- **IAM**: Identity and Access Management (roles, policies)

---

**Keep it simple. Make it work. Win the hackathon!** 🚀
