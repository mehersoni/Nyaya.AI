"""
Visualization data builder for knowledge graph traversal.

This module formats GraphContext data into a structure suitable for
frontend visualization of the graph traversal process.
"""

from typing import Dict, List, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


def build_graph_visualization_data(graph_context) -> Dict[str, Any]:
    """
    Build visualization data from GraphContext.
    
    Formats the traversal data captured during graph navigation into a
    structure suitable for API responses and frontend visualization.
    
    Args:
        graph_context: GraphContext object containing traversal data
        
    Returns:
        Dictionary with keys:
        - nodes_visited: List of node dictionaries with id, type, title, relevance_score
        - edges_traversed: List of edge dictionaries with from, to, type, weight
        - traversal_path: List of node IDs in chronological order
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 7.2, 7.3, 7.4, 7.5, 9.5
    """
    try:
        # Extract nodes_visited from GraphContext
        nodes_visited = _format_nodes(graph_context.nodes_visited)
        
        # Extract edges_traversed from GraphContext
        edges_traversed = _format_edges(graph_context.edges_traversed)
        
        # Extract traversal_path from GraphContext
        traversal_path = _format_traversal_path(graph_context.traversal_path)
        
        # Build initial graph data structure for validation
        initial_graph_data = {
            'nodes_visited': nodes_visited,
            'edges_traversed': edges_traversed,
            'traversal_path': traversal_path
        }
        
        # Validate the graph data BEFORE size limiting (Requirement 9.5)
        # This catches invalid references in the original GraphContext data
        is_valid, errors = validate_graph_data(initial_graph_data)
        
        if not is_valid:
            # Log validation errors with WARNING severity
            logger.warning(f"Graph visualization data validation failed: {'; '.join(errors)}")
            # Return empty graph_traversal object on validation failure
            return {
                'nodes_visited': [],
                'edges_traversed': [],
                'traversal_path': []
            }
        
        # After validation passes, apply size limiting (Requirements 7.3, 7.4)
        nodes_visited = _limit_nodes(nodes_visited)
        
        # Get set of valid node IDs after limiting
        valid_node_ids = {node['id'] for node in nodes_visited}
        
        # Filter edges to only include those referencing valid nodes
        # (this handles the case where node limiting removed some nodes)
        edges_traversed = [
            edge for edge in edges_traversed
            if edge['from'] in valid_node_ids and edge['to'] in valid_node_ids
        ]
        
        # Now apply edge limiting
        edges_traversed = _limit_edges(edges_traversed)
        
        # Filter traversal_path to only include valid node IDs
        traversal_path = [node_id for node_id in traversal_path if node_id in valid_node_ids]
        
        # Build final graph data structure
        graph_data = {
            'nodes_visited': nodes_visited,
            'edges_traversed': edges_traversed,
            'traversal_path': traversal_path
        }
        
        # Calculate serialized JSON size and log warning if needed (Requirements 7.2, 7.5)
        _check_data_size(graph_data)
        
        return graph_data
    except Exception as e:
        logger.error(f"Error building graph visualization data: {e}")
        return {
            'nodes_visited': [],
            'edges_traversed': [],
            'traversal_path': []
        }


def _format_nodes(nodes: List[Any]) -> List[Dict[str, Any]]:
    """
    Format node data for visualization.
    
    Extracts id, type, title, and relevance_score from GraphNode objects.
    Truncates titles to 100 characters if needed.
    
    Args:
        nodes: List of GraphNode objects
        
    Returns:
        List of formatted node dictionaries
        
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    formatted_nodes = []
    
    for node in nodes:
        try:
            # Extract title from node content
            title = _extract_node_title(node)
            
            # Truncate title to 100 characters if needed (Requirement 3.4)
            if len(title) > 100:
                title = title[:100]
            
            formatted_node = {
                'id': node.node_id,  # Requirement 3.1
                'type': node.node_type,  # Requirement 3.2
                'title': title,  # Requirement 3.3
                'relevance_score': node.relevance_score  # Requirement 3.5
            }
            
            formatted_nodes.append(formatted_node)
        except Exception as e:
            logger.warning(f"Error formatting node {getattr(node, 'node_id', 'unknown')}: {e}")
            continue
    
    return formatted_nodes


def _extract_node_title(node: Any) -> str:
    """
    Extract a human-readable title from a GraphNode.
    
    Args:
        node: GraphNode object
        
    Returns:
        Human-readable title string
    """
    content = node.content
    node_type = node.node_type
    
    if node_type == 'section':
        section_num = content.get('section_number', '')
        title = content.get('title', '')
        if section_num and title:
            return f"Section {section_num}: {title}"
        elif section_num:
            return f"Section {section_num}"
        elif title:
            return title
        return content.get('text', '')[:50]  # Fallback to first 50 chars of text
    
    elif node_type == 'clause':
        label = content.get('label', '')
        text = content.get('text', '')
        if label:
            return f"Clause {label}: {text[:50]}"
        return text[:50] if text else 'Clause'
    
    elif node_type == 'definition':
        term = content.get('term', '')
        if term:
            return f"Definition: {term}"
        return 'Definition'
    
    elif node_type == 'right':
        description = content.get('description', '')
        if description:
            return f"Right: {description[:50]}"
        return 'Right'
    
    # Fallback
    return node.node_id


def _format_edges(edges: List[Any]) -> List[Dict[str, Any]]:
    """
    Format edge data for visualization.
    
    Extracts from, to, type, and weight from GraphEdge objects.
    
    Args:
        edges: List of GraphEdge objects
        
    Returns:
        List of formatted edge dictionaries
        
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    formatted_edges = []
    
    for edge in edges:
        try:
            # Default weight to 1.0 if not present
            weight = getattr(edge, 'weight', 1.0)
            
            formatted_edge = {
                'from': edge.from_node,  # Requirement 4.1
                'to': edge.to_node,  # Requirement 4.2
                'type': edge.relation_type,  # Requirement 4.3
                'weight': weight  # Requirement 4.5
            }
            
            formatted_edges.append(formatted_edge)
        except Exception as e:
            logger.warning(f"Error formatting edge: {e}")
            continue
    
    return formatted_edges


def _format_traversal_path(traversal_path: List[str]) -> List[str]:
    """
    Format traversal path for visualization.
    
    Returns the list of node IDs in chronological order.
    Removes duplicates while preserving first occurrence.
    
    Args:
        traversal_path: List of node IDs in order visited
        
    Returns:
        List of unique node IDs in chronological order
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    # Remove duplicates while preserving order (Requirement 5.2)
    seen = set()
    unique_path = []
    
    for node_id in traversal_path:
        if node_id not in seen:
            seen.add(node_id)
            unique_path.append(node_id)
    
    return unique_path


def validate_graph_data(graph_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate graph visualization data structure and values.
    
    Performs comprehensive validation of the graph_traversal data to ensure:
    - All node IDs in traversal_path exist in nodes_visited
    - All from/to fields in edges_traversed reference valid node IDs
    - All relevance_score values are between 0.0 and 1.0
    - All weight values are between 0.0 and 1.0
    - All node_type values are valid
    
    Args:
        graph_data: Dictionary containing nodes_visited, edges_traversed, traversal_path
        
    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if all validations pass, False otherwise
        - error_messages: List of validation error descriptions
        
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
    """
    errors = []
    
    # Extract data components
    nodes_visited = graph_data.get('nodes_visited', [])
    edges_traversed = graph_data.get('edges_traversed', [])
    traversal_path = graph_data.get('traversal_path', [])
    
    # Build set of valid node IDs for efficient lookup
    valid_node_ids = {node['id'] for node in nodes_visited if 'id' in node}
    
    # Valid node types
    valid_node_types = {'section', 'clause', 'definition', 'right'}
    
    # Requirement 9.6: Validate node_type values
    for i, node in enumerate(nodes_visited):
        if 'type' not in node:
            errors.append(f"Node at index {i} missing 'type' field")
        elif node['type'] not in valid_node_types:
            errors.append(
                f"Node '{node.get('id', 'unknown')}' has invalid type '{node['type']}'. "
                f"Must be one of: {', '.join(valid_node_types)}"
            )
    
    # Requirement 9.3: Validate relevance_score values are between 0.0 and 1.0
    for i, node in enumerate(nodes_visited):
        if 'relevance_score' not in node:
            errors.append(f"Node '{node.get('id', 'unknown')}' missing 'relevance_score' field")
        else:
            score = node['relevance_score']
            if not isinstance(score, (int, float)):
                errors.append(
                    f"Node '{node.get('id', 'unknown')}' has non-numeric relevance_score: {score}"
                )
            elif score < 0.0 or score > 1.0:
                errors.append(
                    f"Node '{node.get('id', 'unknown')}' has relevance_score {score} "
                    f"outside valid range [0.0, 1.0]"
                )
    
    # Requirement 9.1: Validate all node IDs in traversal_path exist in nodes_visited
    for node_id in traversal_path:
        if node_id not in valid_node_ids:
            errors.append(
                f"Traversal path contains node ID '{node_id}' that does not exist in nodes_visited"
            )
    
    # Requirement 9.2: Validate all from/to fields in edges_traversed reference valid node IDs
    for i, edge in enumerate(edges_traversed):
        if 'from' not in edge:
            errors.append(f"Edge at index {i} missing 'from' field")
        elif edge['from'] not in valid_node_ids:
            errors.append(
                f"Edge at index {i} has 'from' node ID '{edge['from']}' "
                f"that does not exist in nodes_visited"
            )
        
        if 'to' not in edge:
            errors.append(f"Edge at index {i} missing 'to' field")
        elif edge['to'] not in valid_node_ids:
            errors.append(
                f"Edge at index {i} has 'to' node ID '{edge['to']}' "
                f"that does not exist in nodes_visited"
            )
    
    # Requirement 9.4: Validate all weight values are between 0.0 and 1.0
    for i, edge in enumerate(edges_traversed):
        if 'weight' not in edge:
            errors.append(f"Edge at index {i} missing 'weight' field")
        else:
            weight = edge['weight']
            if not isinstance(weight, (int, float)):
                errors.append(
                    f"Edge at index {i} has non-numeric weight: {weight}"
                )
            elif weight < 0.0 or weight > 1.0:
                errors.append(
                    f"Edge at index {i} has weight {weight} outside valid range [0.0, 1.0]"
                )
    
    # Return validation result
    is_valid = len(errors) == 0
    return is_valid, errors



def _limit_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Limit nodes_visited to top 50 by relevance_score if count exceeds 50.
    
    Args:
        nodes: List of formatted node dictionaries
        
    Returns:
        Limited list of nodes (max 50, sorted by relevance_score descending)
        
    Requirements: 7.3
    """
    if len(nodes) <= 50:
        return nodes
    
    # Sort by relevance_score descending and take top 50
    sorted_nodes = sorted(nodes, key=lambda n: n.get('relevance_score', 0.0), reverse=True)
    limited_nodes = sorted_nodes[:50]
    
    logger.info(f"Limited nodes_visited from {len(nodes)} to 50 nodes by relevance_score")
    
    return limited_nodes


def _limit_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Limit edges_traversed to top 100 by weight if count exceeds 100.
    
    Args:
        edges: List of formatted edge dictionaries
        
    Returns:
        Limited list of edges (max 100, sorted by weight descending)
        
    Requirements: 7.4
    """
    if len(edges) <= 100:
        return edges
    
    # Sort by weight descending and take top 100
    sorted_edges = sorted(edges, key=lambda e: e.get('weight', 0.0), reverse=True)
    limited_edges = sorted_edges[:100]
    
    logger.info(f"Limited edges_traversed from {len(edges)} to 100 edges by weight")
    
    return limited_edges


def _check_data_size(graph_data: Dict[str, Any]) -> None:
    """
    Calculate serialized JSON size and log warning if it exceeds 100 KB.
    
    Args:
        graph_data: Dictionary containing graph visualization data
        
    Requirements: 7.2, 7.5
    """
    try:
        # Serialize to JSON to calculate size
        serialized = json.dumps(graph_data)
        size_bytes = len(serialized.encode('utf-8'))
        size_kb = size_bytes / 1024
        
        # Log warning if size exceeds 100 KB (Requirement 7.2)
        if size_kb > 100:
            logger.warning(
                f"Graph visualization data size ({size_kb:.2f} KB) exceeds 100 KB limit. "
                f"Consider further limiting nodes or edges."
            )
        else:
            logger.debug(f"Graph visualization data size: {size_kb:.2f} KB")
    except Exception as e:
        logger.error(f"Error calculating graph data size: {e}")



def build_fallback_kg_structure(graph_context) -> Dict[str, Any]:
    """
    Build fallback KG structure when traversal data is empty.
    
    Shows the actual nodes from graph_context.nodes with inferred relationships.
    This provides a visualization of the knowledge graph structure even when
    traversal tracking didn't capture edges.
    
    Args:
        graph_context: GraphContext object
        
    Returns:
        Dictionary with nodes, edges, and traversal_path showing actual KG structure
        
    Requirements: Fallback visualization for empty traversal data
    """
    try:
        # Use the nodes from graph_context.nodes (these are the relevant nodes)
        nodes_visited = _format_nodes(graph_context.nodes)
        
        # Build edges based on node relationships and types
        edges_traversed = []
        
        # Group nodes by type for easier relationship inference
        sections = [n for n in nodes_visited if n['type'] == 'section']
        clauses = [n for n in nodes_visited if n['type'] == 'clause']
        definitions = [n for n in nodes_visited if n['type'] == 'definition']
        rights = [n for n in nodes_visited if n['type'] == 'right']
        
        # Strategy 1: Connect sections to rights they grant
        # Rights are typically granted by Section 2(9) or other sections
        for section in sections:
            for right in rights:
                # Create edge from section to right
                edges_traversed.append({
                    'from': section['id'],
                    'to': right['id'],
                    'type': 'grants_right',
                    'weight': 0.8
                })
        
        # Strategy 2: Connect sections to definitions they contain
        # Definitions are typically in Section 2
        for section in sections:
            if 'S2' in section['id'] or 'Definition' in section.get('title', ''):
                for definition in definitions:
                    edges_traversed.append({
                        'from': section['id'],
                        'to': definition['id'],
                        'type': 'defines',
                        'weight': 0.9
                    })
        
        # Strategy 3: Connect sections to their clauses
        for section in sections:
            section_num = section['id'].replace('CPA_2019_S', '').split('_')[0]
            for clause in clauses:
                # Check if clause belongs to this section
                if f'S{section_num}' in clause['id']:
                    edges_traversed.append({
                        'from': section['id'],
                        'to': clause['id'],
                        'type': 'contains',
                        'weight': 1.0
                    })
        
        # Strategy 4: Create sequential connections in traversal path
        # This shows the order in which nodes were retrieved
        for i in range(len(nodes_visited) - 1):
            from_node = nodes_visited[i]
            to_node = nodes_visited[i + 1]
            
            # Only add if not already connected
            existing_edge = any(
                e['from'] == from_node['id'] and e['to'] == to_node['id']
                for e in edges_traversed
            )
            
            if not existing_edge:
                # Determine edge type based on node types
                if from_node['type'] == 'section' and to_node['type'] == 'section':
                    edge_type = 'references'
                elif from_node['type'] == 'section' and to_node['type'] == 'right':
                    edge_type = 'grants_right'
                elif from_node['type'] == 'section' and to_node['type'] == 'definition':
                    edge_type = 'defines'
                else:
                    edge_type = 'related_to'
                
                edges_traversed.append({
                    'from': from_node['id'],
                    'to': to_node['id'],
                    'type': edge_type,
                    'weight': 0.6
                })
        
        # Build traversal path from node IDs
        traversal_path = [node['id'] for node in nodes_visited]
        
        logger.info(f"Built fallback KG structure: {len(nodes_visited)} nodes, {len(edges_traversed)} edges")
        
        return {
            'nodes_visited': nodes_visited,
            'edges_traversed': edges_traversed,
            'traversal_path': traversal_path
        }
    except Exception as e:
        logger.error(f"Error building fallback KG structure: {e}")
        return {
            'nodes_visited': [],
            'edges_traversed': [],
            'traversal_path': []
        }
