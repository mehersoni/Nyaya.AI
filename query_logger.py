"""DynamoDB Query Logger for AWS Lambda.

This module logs all queries and responses to DynamoDB for demo analytics
and monitoring. Logging is non-critical and errors are handled gracefully.
"""

import logging
import time
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class QueryLogger:
    """Log queries to DynamoDB.
    
    This class writes query logs to DynamoDB for analytics and monitoring.
    Since logging is non-critical, all errors are caught and logged but
    do not fail the request.
    """
    
    def __init__(self, table_name: str, region: str = "ap-south-1"):
        """Initialize DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table for query logs
            region: AWS region (default: ap-south-1 for Mumbai)
        """
        self.table_name = table_name
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Initialized QueryLogger for table: {table_name}, region: {region}")
    
    def log_query(
        self,
        query_id: str,
        query: str,
        response: str,
        confidence_score: float,
        metadata: Dict[str, Any]
    ) -> None:
        """Write query log to DynamoDB.
        
        Logs the query, response, confidence score, and additional metadata
        to DynamoDB. This method handles all errors gracefully since logging
        is non-critical and should not fail the request.
        
        Args:
            query_id: Unique identifier for the query (UUID)
            query: User's query text
            response: Generated response text
            confidence_score: Confidence score (0.0 to 1.0)
            metadata: Additional metadata dictionary containing:
                - citations: List of citation strings
                - processing_time: Processing time in seconds
                - audience: Target audience (citizen, lawyer, judge)
                - intent_type: Query intent type
                - llm_model: LLM model identifier
                - llm_tokens: Number of tokens used
                - error: Optional error message if processing failed
        """
        try:
            # Prepare the item for DynamoDB
            item = {
                'query_id': query_id,
                'timestamp': int(time.time()),
                'user_query': query,
                'response': response,
                'confidence_score': confidence_score,
            }
            
            # Add metadata fields
            if 'citations' in metadata:
                item['citations'] = metadata['citations']
            
            if 'processing_time' in metadata:
                item['processing_time'] = metadata['processing_time']
            
            if 'audience' in metadata:
                item['audience'] = metadata['audience']
            
            if 'intent_type' in metadata:
                item['intent_type'] = metadata['intent_type']
            
            if 'llm_model' in metadata:
                item['llm_model'] = metadata['llm_model']
            
            if 'llm_tokens' in metadata:
                item['llm_tokens'] = metadata['llm_tokens']
            
            if 'error' in metadata:
                item['error'] = metadata['error']
            
            # Write to DynamoDB
            logger.debug(f"Writing query log to DynamoDB: query_id={query_id}")
            self.table.put_item(Item=item)
            logger.info(f"Successfully logged query: {query_id}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.warning(
                f"Failed to log query to DynamoDB ({error_code}): {error_msg}. "
                f"Continuing without logging (non-critical)."
            )
        except BotoCoreError as e:
            logger.warning(
                f"BotoCoreError while logging query: {str(e)}. "
                f"Continuing without logging (non-critical)."
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error while logging query: {str(e)}. "
                f"Continuing without logging (non-critical)."
            )
