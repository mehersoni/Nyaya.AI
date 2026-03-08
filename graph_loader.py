"""S3 Graph Loader for AWS Lambda.

This module loads knowledge graph JSON files from S3 at Lambda startup
and caches them in global variables for warm start reuse.
"""

import json
import logging
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class S3GraphLoader:
    """Load knowledge graph from S3 bucket.
    
    This class downloads all knowledge graph JSON files from S3 and
    provides them as a structured dictionary. It's designed to be used
    at Lambda cold start with results cached in global variables.
    """
    
    def __init__(self, bucket_name: str, region: str = "ap-south-1"):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket containing knowledge graph files
            region: AWS region (default: ap-south-1 for Mumbai)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        logger.info(f"Initialized S3GraphLoader for bucket: {bucket_name}, region: {region}")
    
    def load_graph_data(self) -> Dict[str, Any]:
        """Load all JSON files from S3 and return graph data.
        
        Downloads all node and edge JSON files from the knowledge_graph
        directory in S3 and returns them as a structured dictionary.
        
        Returns:
            Dictionary with the following structure:
            {
                'sections': List of section nodes,
                'clauses': List of clause nodes,
                'definitions': List of definition nodes,
                'rights': List of rights nodes,
                'contains_edges': List of contains edges,
                'contains_clause_edges': List of contains_clause edges,
                'references_edges': List of references edges,
                'defines_edges': List of defines edges,
                'grants_right_edges': List of grants_right edges
            }
        
        Raises:
            ClientError: If S3 access fails (bucket not found, access denied, etc.)
            ValueError: If JSON files are malformed
        """
        logger.info("Loading knowledge graph data from S3...")
        
        try:
            graph_data = {
                # Node files
                'sections': self._load_json_file('knowledge_graph/nodes/sections.data.json'),
                'clauses': self._load_json_file('knowledge_graph/nodes/clauses.data.json'),
                'definitions': self._load_json_file('knowledge_graph/nodes/definitions.data.json'),
                'rights': self._load_json_file('knowledge_graph/nodes/rights.data.json'),
                
                # Edge files
                'contains_edges': self._load_json_file('knowledge_graph/edges/contains.data.json'),
                'contains_clause_edges': self._load_json_file('knowledge_graph/edges/contains_clause.data.json'),
                'references_edges': self._load_json_file('knowledge_graph/edges/references.data.json'),
                'defines_edges': self._load_json_file('knowledge_graph/edges/defines.data.json'),
                'grants_right_edges': self._load_json_file('knowledge_graph/edges/grants_right.data.json'),
            }
            
            # Log statistics
            total_nodes = sum(len(graph_data[key]) for key in ['sections', 'clauses', 'definitions', 'rights'])
            total_edges = sum(len(graph_data[key]) for key in ['contains_edges', 'contains_clause_edges', 'references_edges', 'defines_edges', 'grants_right_edges'])
            
            logger.info(f"Successfully loaded graph data: {total_nodes} nodes, {total_edges} edges")
            logger.info(f"  - Sections: {len(graph_data['sections'])}")
            logger.info(f"  - Clauses: {len(graph_data['clauses'])}")
            logger.info(f"  - Definitions: {len(graph_data['definitions'])}")
            logger.info(f"  - Rights: {len(graph_data['rights'])}")
            
            return graph_data
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"S3 ClientError ({error_code}): {error_msg}")
            raise
        except BotoCoreError as e:
            logger.error(f"BotoCoreError: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading graph data: {str(e)}")
            raise
    
    def download_file(self, key: str) -> bytes:
        """Download single file from S3.
        
        Args:
            key: S3 object key (path within bucket)
        
        Returns:
            File contents as bytes
        
        Raises:
            ClientError: If S3 access fails
        """
        logger.debug(f"Downloading file: s3://{self.bucket_name}/{key}")
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            logger.debug(f"Successfully downloaded {len(content)} bytes from {key}")
            return content
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to download {key}: {error_code} - {error_msg}")
            raise
    
    def _load_json_file(self, key: str) -> List[Dict[str, Any]]:
        """Load and parse a JSON file from S3.
        
        Args:
            key: S3 object key for the JSON file
        
        Returns:
            Parsed JSON data as a list of dictionaries
        
        Raises:
            ClientError: If S3 access fails
            ValueError: If JSON parsing fails
        """
        try:
            content = self.download_file(key)
            data = json.loads(content.decode('utf-8'))
            
            if not isinstance(data, list):
                raise ValueError(f"Expected list in {key}, got {type(data).__name__}")
            
            logger.debug(f"Loaded {len(data)} items from {key}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {key}: {str(e)}")
            raise ValueError(f"Invalid JSON in {key}: {str(e)}")


# Global cache for warm starts
_cached_graph_data: Dict[str, Any] = None
_cached_bucket_name: str = None


def get_cached_graph_data(bucket_name: str, region: str = "ap-south-1") -> Dict[str, Any]:
    """Get graph data with caching for Lambda warm starts.
    
    This function implements the caching strategy for Lambda containers.
    On cold start, it loads the graph data from S3 and caches it in a
    global variable. On warm starts, it returns the cached data.
    
    Args:
        bucket_name: S3 bucket name
        region: AWS region
    
    Returns:
        Graph data dictionary
    """
    global _cached_graph_data, _cached_bucket_name
    
    # Check if we have cached data for this bucket
    if _cached_graph_data is not None and _cached_bucket_name == bucket_name:
        logger.info("Using cached graph data (warm start)")
        return _cached_graph_data
    
    # Cold start - load from S3
    logger.info("Loading graph data from S3 (cold start)")
    loader = S3GraphLoader(bucket_name, region)
    _cached_graph_data = loader.load_graph_data()
    _cached_bucket_name = bucket_name
    
    return _cached_graph_data
