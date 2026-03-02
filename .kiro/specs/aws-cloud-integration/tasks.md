# Implementation Plan: AWS Hackathon Integration

## Overview

This plan implements a serverless AWS deployment of Nyayamrit for hackathon demonstration. The implementation follows a 3-day timeline, packaging the entire application in a single Lambda function with API Gateway, using AWS Bedrock for LLM inference, S3 for knowledge graph storage, and DynamoDB for query logging.

## Tasks

- [ ] 1. Set up AWS infrastructure and IAM roles
  - Create S3 bucket with versioning enabled
  - Create DynamoDB table for query logs
  - Create IAM execution role with policies for Lambda, S3, Bedrock, DynamoDB, and CloudWatch
  - Enable AWS Bedrock model access for Claude 3 Haiku
  - _Requirements: 4.1, 4.2, 5.1, 5.2, 7.1, 7.4_

- [ ] 2. Implement AWS Bedrock provider
  - [ ] 2.1 Create BedrockProvider class in llm_integration/providers.py
    - Implement boto3 bedrock-runtime client initialization
    - Implement generate_response method with Claude 3 Haiku API format
    - Implement is_available method for service health check
    - Use IAM role-based authentication
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 2.2 Implement retry logic with exponential backoff
    - Add retry decorator for transient errors (ThrottlingException, ServiceUnavailableException)
    - Implement 3 retry attempts with 1s, 2s, 4s delays
    - Log retry attempts to CloudWatch
    - _Requirements: 1.4_
  
  - [ ]* 2.3 Write property test for Bedrock retry logic
    - **Property 1: Bedrock Retry Logic**
    - **Validates: Requirements 1.4**
  
  - [ ]* 2.4 Write property test for prompt template compatibility
    - **Property 2: Prompt Template Backward Compatibility**
    - **Validates: Requirements 1.5**
  
  - [ ]* 2.5 Write unit tests for BedrockProvider
    - Test request/response format conversion
    - Test error handling for different Bedrock errors
    - Test token usage tracking
    - Mock boto3 client using moto library
    - _Requirements: 1.1, 1.2, 1.4_

- [ ] 3. Implement S3 graph loader
  - [ ] 3.1 Create S3GraphLoader class in aws_lambda/graph_loader.py
    - Initialize boto3 S3 client
    - Implement load_graph_data method to download all JSON files
    - Implement download_file method for individual file retrieval
    - Add caching strategy using global variables for warm starts
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ]* 3.2 Write property test for graph query consistency
    - **Property 4: Graph Query Result Consistency**
    - **Validates: Requirements 2.4**
  
  - [ ]* 3.3 Write unit tests for S3GraphLoader
    - Test loading all JSON files from S3
    - Test handling missing files
    - Test handling malformed JSON
    - Test caching behavior across invocations
    - Mock S3 using moto library
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4. Implement DynamoDB query logger
  - [ ] 4.1 Create QueryLogger class in aws_lambda/query_logger.py
    - Initialize boto3 DynamoDB client
    - Implement log_query method to write query logs
    - Include query_id, timestamp, user_query, response, confidence_score, citations, metadata
    - Handle DynamoDB errors gracefully (non-critical path)
    - _Requirements: 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 4.2 Write property test for query logging completeness
    - **Property 5: Query Logging Completeness**
    - **Validates: Requirements 5.6**
  
  - [ ]* 4.3 Write unit tests for QueryLogger
    - Test DynamoDB item creation
    - Test handling of DynamoDB errors
    - Test log data structure and completeness
    - Mock DynamoDB using moto library
    - _Requirements: 5.3, 5.4, 5.6_

- [ ] 5. Checkpoint - Verify AWS components work independently
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Lambda handler
  - [ ] 6.1 Create lambda_handler function in aws_lambda/handler.py
    - Parse API Gateway event to extract query request
    - Initialize components with caching for warm starts
    - Route requests to GraphRAG engine
    - Format responses for API Gateway with proper status codes
    - Handle errors and timeouts with appropriate HTTP responses
    - _Requirements: 3.1, 3.2, 3.3, 3.8_
  
  - [ ] 6.2 Implement CloudWatch logging with correlation IDs
    - Generate unique request_id for each invocation
    - Log all operations with request_id for correlation
    - Log errors with complete stack traces
    - Exclude sensitive data from logs
    - _Requirements: 6.7, 7.6, 8.1, 8.2, 8.3_
  
  - [ ]* 6.3 Write property test for request logging correlation
    - **Property 6: Request Logging with Correlation IDs**
    - **Validates: Requirements 6.7, 8.1, 8.2**
  
  - [ ]* 6.4 Write property test for error logging with stack traces
    - **Property 7: Error Logging with Stack Traces**
    - **Validates: Requirements 8.3**
  
  - [ ]* 6.5 Write property test for sensitive data exclusion
    - **Property 8: Sensitive Data Exclusion**
    - **Validates: Requirements 7.6**
  
  - [ ]* 6.6 Write unit tests for Lambda handler
    - Test API Gateway event parsing
    - Test response formatting
    - Test error handling for various failure scenarios
    - Test cold start vs warm start behavior
    - Test timeout handling
    - _Requirements: 3.1, 3.8, 3.9_

- [ ] 7. Integrate components and wire Lambda function
  - [ ] 7.1 Wire S3GraphLoader to load knowledge graph at cold start
    - Load graph data from S3 bucket specified in environment variable
    - Cache loaded data in global variables
    - Handle S3 access errors with 503 responses
    - _Requirements: 2.1, 2.2, 2.3, 4.6_
  
  - [ ] 7.2 Wire BedrockProvider to LLMManager
    - Register BedrockProvider as available provider
    - Configure with model ID from environment variable
    - Maintain existing prompt templates
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [ ] 7.3 Wire QueryLogger to log all processed queries
    - Log queries after successful processing
    - Include all required metadata (confidence, citations, processing time)
    - Handle logging errors gracefully
    - _Requirements: 5.6, 6.8_
  
  - [ ] 7.4 Implement zero-hallucination validation
    - Validate all citations reference actual sections in loaded graph
    - Verify all factual claims are supported by citations
    - Calculate confidence scores
    - _Requirements: 1.7, 6.3, 6.6_
  
  - [ ]* 7.5 Write property test for zero-hallucination guarantee
    - **Property 3: Zero-Hallucination Guarantee**
    - **Validates: Requirements 1.7, 6.3, 6.6**

- [ ] 8. Create Lambda deployment package
  - [ ] 8.1 Create deployment script in deployment/deploy.sh
    - Create lambda_package directory
    - Install dependencies from requirements.txt
    - Copy source code directories (llm_integration, query_engine, aws_lambda)
    - Create ZIP file for Lambda deployment
    - _Requirements: 3.1_
  
  - [ ] 8.2 Create requirements-lambda.txt with Lambda dependencies
    - Include boto3, pydantic, and other required packages
    - Pin versions for reproducibility
    - _Requirements: 3.1_
  
  - [ ] 8.3 Create IAM policy files
    - Create trust-policy.json for Lambda execution role
    - Create lambda-policy.json with S3, Bedrock, DynamoDB, CloudWatch permissions
    - _Requirements: 7.1, 7.4_

- [ ] 9. Deploy Lambda function and API Gateway
  - [ ] 9.1 Upload knowledge graph files to S3
    - Upload all JSON files from knowledge_graph directory
    - Upload consumer_protection_act_2019.pdf
    - Verify files are accessible
    - _Requirements: 2.1, 4.3, 4.4, 4.5_
  
  - [ ] 9.2 Create and deploy Lambda function
    - Create Lambda function with Python 3.11 runtime
    - Set timeout to 30 seconds
    - Set memory to 2048 MB
    - Configure environment variables (S3_BUCKET_NAME, BEDROCK_MODEL_ID, DYNAMODB_TABLE_NAME)
    - Attach IAM execution role
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 9.3 Create API Gateway REST API
    - Create HTTP API with Lambda integration
    - Add POST /query endpoint
    - Enable CORS with appropriate headers
    - Add basic rate limiting (100 req/min)
    - Get public URL
    - _Requirements: 3.4, 3.5, 3.6, 3.7_
  
  - [ ] 9.4 Add Lambda permission for API Gateway
    - Grant API Gateway permission to invoke Lambda function
    - _Requirements: 3.4_

- [ ] 10. Checkpoint - Test deployed system end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Run integration tests and validation
  - [ ] 11.1 Test core query: "What are my consumer rights?"
    - Verify response includes all 6 rights
    - Verify citations are correct
    - Verify confidence score > 0.8
    - _Requirements: 1.6, 6.1, 6.2, 6.3, 6.4_
  
  - [ ] 11.2 Test additional queries
    - Test: "I bought a defective product"
    - Test: "Define consumer"
    - Test: "Show me Section 18"
    - Test invalid query (empty string)
    - Test long query (>1000 chars)
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 11.3 Verify zero-hallucination guarantee
    - Check all responses for unsupported claims
    - Verify all citations reference actual sections
    - _Requirements: 1.7, 6.6_
  
  - [ ] 11.4 Verify logging and observability
    - Check CloudWatch logs show requests with correlation IDs
    - Check DynamoDB has query logs with all required fields
    - Verify no sensitive data in logs
    - _Requirements: 6.7, 6.8, 7.6, 8.1, 8.2, 8.3_
  
  - [ ] 11.5 Measure performance
    - Measure response time (should be < 5 seconds)
    - Test cold start vs warm start performance
    - _Requirements: 6.9_
  
  - [ ]* 11.6 Run property-based test suite
    - Execute all 8 property tests with 100+ iterations each
    - Verify all properties hold across randomized inputs
    - _Requirements: 1.4, 1.5, 1.7, 2.4, 5.6, 6.7, 7.6, 8.1, 8.2, 8.3_

- [ ] 12. Create CloudWatch dashboard and documentation
  - [ ] 12.1 Create CloudWatch dashboard
    - Add widgets for Lambda invocations, errors, duration
    - Add widgets for DynamoDB write metrics
    - Add widgets for API Gateway request count and latency
    - Set log retention to 30 days
    - _Requirements: 8.4, 8.5, 8.6_
  
  - [ ] 12.2 Create AWS deployment documentation
    - Document deployment steps in README_AWS.md
    - Include API endpoint URL
    - Include example curl commands
    - Document environment variables
    - Document troubleshooting common issues
    - _Requirements: 3.8_
  
  - [ ] 12.3 Prepare demo script
    - Create list of 5-10 test queries for demo
    - Document expected responses
    - Create demo walkthrough guide
    - _Requirements: 6.5_

- [ ] 13. Final checkpoint - System ready for hackathon demo
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Implementation follows 3-day hackathon timeline: Day 1 (Tasks 1-5), Day 2 (Tasks 6-10), Day 3 (Tasks 11-13)
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and AWS service integration
- Focus on working demo, not enterprise production features
- Keep implementation simple and pragmatic for hackathon success
