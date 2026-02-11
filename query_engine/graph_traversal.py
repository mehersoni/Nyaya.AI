"""
Graph Traversal Engine for Knowledge Graph Navigation

This module implements the GraphTraversal class that navigates the legal knowledge graph
to retrieve relevant provisions based on query intent.

Supports traversal strategies:
- Direct lookup: Section/clause by ID
- Keyword search: Full-text search on legal text
- Relationship traversal: Follow edges (contains, references, defines)
- Multi-hop reasoning: Combine multiple provisions
"""

import json
import re
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from query_engine.query_parser import QueryIntent, IntentType


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    node_id: str
    node_type: str  # section, clause, definition, right
    content: Dict[str, Any]
    
    def get_text(self) -> str:
        """Get the main text content of the node"""
        if self.node_type == 'section':
            return self.content.get('text', '')
        elif self.node_type == 'clause':
            return self.content.get('text', '')
        elif self.node_type == 'definition':
            return self.content.get('definition', '')
        elif self.node_type == 'right':
            return self.content.get('description', '')
        return ''
    
    def get_citation(self) -> str:
        """Get formatted citation for this node"""
        if self.node_type == 'section':
            section_num = self.content.get('section_number', '')
            act = self.content.get('act', '')
            return f"Section {section_num}, {act}"
        elif self.node_type == 'clause':
            parent = self.content.get('parent_section', '')
            label = self.content.get('label', '')
            return f"{parent}, Clause {label}"
        elif self.node_type == 'definition':
            term = self.content.get('term', '')
            defined_in = self.content.get('defined_in', '')
            return f"Definition of '{term}' in {defined_in}"
        elif self.node_type == 'right':
            granted_by = self.content.get('granted_by', '')
            return f"Right granted by {granted_by}"
        return self.node_id


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph"""
    from_node: str
    to_node: str
    relation_type: str
    context: Optional[str] = None


@dataclass
class GraphContext:
    """Context retrieved from knowledge graph traversal"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    citations: List[str]
    confidence: float
    traversal_path: List[str]
    
    def get_primary_nodes(self) -> List[GraphNode]:
        """Get nodes that directly match the query"""
        return [node for node in self.nodes if node.node_id in self.traversal_path[:3]]
    
    def get_related_nodes(self) -> List[GraphNode]:
        """Get nodes that are related through edges"""
        primary_ids = {node.node_id for node in self.get_primary_nodes()}
        return [node for node in self.nodes if node.node_id not in primary_ids]


class GraphTraversal:
    """Traverse knowledge graph to retrieve relevant legal provisions."""
    
    def __init__(self, knowledge_graph_path: str = "knowledge_graph"):
        """
        Initialize the graph traversal engine.
        
        Args:
            knowledge_graph_path: Path to the knowledge graph data directory
        """
        self.kg_path = Path(knowledge_graph_path)
        self._load_knowledge_graph()
    
    def _load_knowledge_graph(self):
        """Load knowledge graph data from JSON files."""
        try:
            # Load nodes
            self.sections = self._load_json_file("nodes/sections.data.json")
            self.clauses = self._load_json_file("nodes/clauses.data.json")
            self.definitions = self._load_json_file("nodes/definitions.data.json")
            self.rights = self._load_json_file("nodes/rights.data.json")
            
            # Load edges
            self.contains_edges = self._load_json_file("edges/contains.data.json")
            self.references_edges = self._load_json_file("edges/references.data.json")
            self.defines_edges = self._load_json_file("edges/defines.data.json")
            
            # Create lookup indices
            self._create_indices()
            
        except Exception as e:
            raise RuntimeError(f"Failed to load knowledge graph: {e}")
    
    def _load_json_file(self, relative_path: str) -> List[Dict]:
        """Load JSON data from file."""
        file_path = self.kg_path / relative_path
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_indices(self):
        """Create lookup indices for efficient retrieval."""
        # Section lookup by ID and number
        self.section_by_id = {s['section_id']: s for s in self.sections}
        self.section_by_number = {s['section_number']: s for s in self.sections}
        
        # Clause lookup by ID and parent
        self.clause_by_id = {c['clause_id']: c for c in self.clauses}
        self.clauses_by_section = {}
        for clause in self.clauses:
            parent = clause['parent_section']
            if parent not in self.clauses_by_section:
                self.clauses_by_section[parent] = []
            self.clauses_by_section[parent].append(clause)
        
        # Definition lookup by term
        self.definition_by_term = {d['term'].lower(): d for d in self.definitions}
        
        # Rights lookup by ID and type
        self.right_by_id = {r['right_id']: r for r in self.rights}
        self.rights_by_type = {}
        for right in self.rights:
            right_type = right.get('right_type', 'unknown')
            if right_type not in self.rights_by_type:
                self.rights_by_type[right_type] = []
            self.rights_by_type[right_type].append(right)
        
        # Edge lookup by source
        self.edges_from = {}
        all_edges = (
            [(e['parent'], e['child'], 'contains') for e in self.contains_edges] +
            [(e['from'], e['to'], e['reference_type']) for e in self.references_edges] +
            [(e['source'], e['target'], 'defines') for e in self.defines_edges]
        )
        
        for from_node, to_node, relation in all_edges:
            if from_node not in self.edges_from:
                self.edges_from[from_node] = []
            self.edges_from[from_node].append((to_node, relation))
    
    def retrieve_context(self, intent: QueryIntent) -> GraphContext:
        """
        Traverse graph based on query intent.
        
        Args:
            intent: Parsed query intent from QueryParser
            
        Returns:
            GraphContext with relevant nodes, edges, and citations
        """
        nodes = []
        edges = []
        traversal_path = []
        
        if intent.intent_type == IntentType.DEFINITION_LOOKUP:
            nodes, edges, traversal_path = self._handle_definition_lookup(intent)
        elif intent.intent_type == IntentType.SECTION_RETRIEVAL:
            nodes, edges, traversal_path = self._handle_section_retrieval(intent)
        elif intent.intent_type == IntentType.RIGHTS_QUERY:
            nodes, edges, traversal_path = self._handle_rights_query(intent)
        elif intent.intent_type == IntentType.SCENARIO_ANALYSIS:
            nodes, edges, traversal_path = self._handle_scenario_analysis(intent)
        
        # Calculate confidence based on retrieval success
        confidence = self._calculate_confidence(intent, nodes, edges)
        
        # Generate citations
        citations = [node.get_citation() for node in nodes]
        
        return GraphContext(
            nodes=nodes,
            edges=edges,
            citations=citations,
            confidence=confidence,
            traversal_path=traversal_path
        )
    
    def _handle_definition_lookup(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle definition lookup queries."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Look for exact term matches
        for term in intent.legal_terms:
            term_lower = term.lower()
            if term_lower in self.definition_by_term:
                definition = self.definition_by_term[term_lower]
                node = GraphNode(
                    node_id=f"DEF_{term_lower}",
                    node_type='definition',
                    content=definition
                )
                nodes.append(node)
                traversal_path.append(node.node_id)
                
                # Find the section that defines this term
                defined_in = definition.get('defined_in')
                if defined_in and defined_in in self.section_by_id:
                    section = self.section_by_id[defined_in]
                    section_node = GraphNode(
                        node_id=section['section_id'],
                        node_type='section',
                        content=section
                    )
                    nodes.append(section_node)
                    
                    # Add defining edge
                    edge = GraphEdge(
                        from_node=section['section_id'],
                        to_node=node.node_id,
                        relation_type='defines'
                    )
                    edges.append(edge)
        
        # If no exact matches, search in section text
        if not nodes:
            nodes, edges, traversal_path = self._keyword_search(intent.legal_terms)
        
        return nodes, edges, traversal_path
    
    def _handle_section_retrieval(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle section retrieval queries."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Direct section lookup
        for section_num in intent.section_numbers:
            if section_num in self.section_by_number:
                section = self.section_by_number[section_num]
                node = GraphNode(
                    node_id=section['section_id'],
                    node_type='section',
                    content=section
                )
                nodes.append(node)
                traversal_path.append(node.node_id)
                
                # Add related clauses
                section_id = section['section_id']
                if section_id in self.clauses_by_section:
                    for clause in self.clauses_by_section[section_id]:
                        clause_node = GraphNode(
                            node_id=clause['clause_id'],
                            node_type='clause',
                            content=clause
                        )
                        nodes.append(clause_node)
                        
                        # Add contains edge
                        edge = GraphEdge(
                            from_node=section_id,
                            to_node=clause['clause_id'],
                            relation_type='contains'
                        )
                        edges.append(edge)
        
        return nodes, edges, traversal_path
    
    def _handle_rights_query(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle consumer rights queries."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Get consumer rights
        consumer_rights = self.rights_by_type.get('consumer_right', [])
        
        for right in consumer_rights:
            node = GraphNode(
                node_id=right['right_id'],
                node_type='right',
                content=right
            )
            nodes.append(node)
            traversal_path.append(node.node_id)
            
            # Find the section that grants this right
            granted_by = right.get('granted_by')
            if granted_by and granted_by in self.section_by_id:
                section = self.section_by_id[granted_by]
                section_node = GraphNode(
                    node_id=section['section_id'],
                    node_type='section',
                    content=section
                )
                nodes.append(section_node)
                
                # Add grants edge
                edge = GraphEdge(
                    from_node=section['section_id'],
                    to_node=right['right_id'],
                    relation_type='grants_right'
                )
                edges.append(edge)
        
        return nodes, edges, traversal_path
    
    def _handle_scenario_analysis(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle scenario analysis queries with scenario-specific routing."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Check for specific consumer scenarios and route to appropriate provisions
        query_lower = intent.original_query.lower()
        
        # Defective goods scenario
        if any(term in query_lower for term in ['defective', 'faulty', 'damaged', 'broken', 'defect']):
            nodes, edges, traversal_path = self._handle_defective_goods_scenario(intent)
        
        # Misleading advertisement scenario
        elif any(term in query_lower for term in ['misleading', 'false', 'advertisement', 'advertise']):
            nodes, edges, traversal_path = self._handle_misleading_ad_scenario(intent)
        
        # Overcharging scenario
        elif any(term in query_lower for term in ['overcharg', 'excess', 'extra', 'price', 'refund']):
            nodes, edges, traversal_path = self._handle_overcharging_scenario(intent)
        
        # Service deficiency scenario
        elif any(term in query_lower for term in ['service', 'deficiency', 'poor service', 'bad service']):
            nodes, edges, traversal_path = self._handle_service_deficiency_scenario(intent)
        
        # Generic scenario - fallback to keyword search but prioritize consumer-actionable sections
        else:
            nodes, edges, traversal_path = self._handle_generic_scenario(intent)
        
        return nodes, edges, traversal_path
    
    def _handle_defective_goods_scenario(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle defective goods scenarios with consumer-actionable guidance."""
        nodes = []
        edges = []
        traversal_path = []
        
        # 1. Add definition of "defect" from Section 2
        if 'defect' in self.definition_by_term:
            definition = self.definition_by_term['defect']
            def_node = GraphNode(
                node_id="DEF_defect",
                node_type='definition',
                content=definition
            )
            nodes.append(def_node)
            traversal_path.append(def_node.node_id)
        
        # 2. Add Section 35 - How to file complaint
        if '35' in self.section_by_number:
            section_35 = self.section_by_number['35']
            section_node = GraphNode(
                node_id=section_35['section_id'],
                node_type='section',
                content=section_35
            )
            nodes.append(section_node)
            traversal_path.append(section_node.node_id)
        
        # 3. Add Section 39 - Remedies available
        if '39' in self.section_by_number:
            section_39 = self.section_by_number['39']
            remedy_node = GraphNode(
                node_id=section_39['section_id'],
                node_type='section',
                content=section_39
            )
            nodes.append(remedy_node)
            traversal_path.append(remedy_node.node_id)
        
        # 4. Add consumer rights related to defective goods
        consumer_rights = self.rights_by_type.get('consumer_right', [])
        for right in consumer_rights[:2]:  # Limit to top 2 relevant rights
            if any(term in right.get('description', '').lower() for term in ['quality', 'defect', 'redressal']):
                right_node = GraphNode(
                    node_id=right['right_id'],
                    node_type='right',
                    content=right
                )
                nodes.append(right_node)
                traversal_path.append(right_node.node_id)
        
        return nodes, edges, traversal_path
    
    def _handle_misleading_ad_scenario(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle misleading advertisement scenarios."""
        nodes = []
        edges = []
        traversal_path = []
        
        # 1. Add definition of misleading advertisement (most important)
        if 'misleading advertisement' in self.definition_by_term:
            definition = self.definition_by_term['misleading advertisement']
            def_node = GraphNode(
                node_id="DEF_misleading_advertisement",
                node_type='definition',
                content=definition
            )
            nodes.append(def_node)
            traversal_path.append(def_node.node_id)
        
        # 2. Add definition of advertisement (general)
        if 'advertisement' in self.definition_by_term:
            definition = self.definition_by_term['advertisement']
            def_node = GraphNode(
                node_id="DEF_advertisement",
                node_type='definition',
                content=definition
            )
            nodes.append(def_node)
            traversal_path.append(def_node.node_id)
        
        # 3. Add Section 18 - CCPA powers and functions
        if '18' in self.section_by_number:
            section_18 = self.section_by_number['18']
            section_node = GraphNode(
                node_id=section_18['section_id'],
                node_type='section',
                content=section_18
            )
            nodes.append(section_node)
            traversal_path.append(section_node.node_id)
        
        # 4. Add Section 21 - Penalties for misleading advertisements
        if '21' in self.section_by_number:
            section_21 = self.section_by_number['21']
            section_node = GraphNode(
                node_id=section_21['section_id'],
                node_type='section',
                content=section_21
            )
            nodes.append(section_node)
            traversal_path.append(section_node.node_id)
        
        # 5. Add Section 35 - How to file complaint (secondary)
        if '35' in self.section_by_number:
            section_35 = self.section_by_number['35']
            section_node = GraphNode(
                node_id=section_35['section_id'],
                node_type='section',
                content=section_35
            )
            nodes.append(section_node)
            traversal_path.append(section_node.node_id)
        
        return nodes, edges, traversal_path
    
    def _handle_overcharging_scenario(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle overcharging scenarios."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Add complaint filing and remedy sections
        for section_num in ['35', '39']:
            if section_num in self.section_by_number:
                section = self.section_by_number[section_num]
                section_node = GraphNode(
                    node_id=section['section_id'],
                    node_type='section',
                    content=section
                )
                nodes.append(section_node)
                traversal_path.append(section_node.node_id)
        
        return nodes, edges, traversal_path
    
    def _handle_service_deficiency_scenario(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle service deficiency scenarios."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Add definition of deficiency if available
        if 'deficiency' in self.definition_by_term:
            definition = self.definition_by_term['deficiency']
            def_node = GraphNode(
                node_id="DEF_deficiency",
                node_type='definition',
                content=definition
            )
            nodes.append(def_node)
            traversal_path.append(def_node.node_id)
        
        # Add complaint filing and remedy sections
        for section_num in ['35', '39']:
            if section_num in self.section_by_number:
                section = self.section_by_number[section_num]
                section_node = GraphNode(
                    node_id=section['section_id'],
                    node_type='section',
                    content=section
                )
                nodes.append(section_node)
                traversal_path.append(section_node.node_id)
        
        return nodes, edges, traversal_path
    
    def _handle_generic_scenario(self, intent: QueryIntent) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Handle generic scenarios with consumer-focused sections."""
        nodes = []
        edges = []
        traversal_path = []
        
        # Prioritize consumer-actionable sections over institutional ones
        consumer_actionable_sections = ['35', '39', '2']  # Complaint filing, remedies, definitions
        
        for section_num in consumer_actionable_sections:
            if section_num in self.section_by_number:
                section = self.section_by_number[section_num]
                section_node = GraphNode(
                    node_id=section['section_id'],
                    node_type='section',
                    content=section
                )
                nodes.append(section_node)
                traversal_path.append(section_node.node_id)
        
        # Add relevant consumer rights
        consumer_rights = self.rights_by_type.get('consumer_right', [])
        for right in consumer_rights[:2]:  # Limit to top 2
            right_node = GraphNode(
                node_id=right['right_id'],
                node_type='right',
                content=right
            )
            nodes.append(right_node)
            traversal_path.append(right_node.node_id)
        
        return nodes, edges, traversal_path
    
    def _keyword_search(self, terms: List[str]) -> Tuple[List[GraphNode], List[GraphEdge], List[str]]:
        """Perform keyword search across all node types."""
        nodes = []
        edges = []
        traversal_path = []
        scored_matches = []
        
        # Search in sections
        for section in self.sections:
            score = self._calculate_text_match_score(section.get('text', ''), terms)
            if score > 0:
                scored_matches.append((score, 'section', section))
        
        # Search in definitions
        for definition in self.definitions:
            score = self._calculate_text_match_score(definition.get('definition', ''), terms)
            if score > 0:
                scored_matches.append((score, 'definition', definition))
        
        # Search in rights
        for right in self.rights:
            score = self._calculate_text_match_score(right.get('description', ''), terms)
            if score > 0:
                scored_matches.append((score, 'right', right))
        
        # Sort by score and take top matches
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        
        for score, node_type, content in scored_matches[:5]:  # Top 5 matches
            if node_type == 'section':
                node_id = content['section_id']
            elif node_type == 'definition':
                node_id = f"DEF_{content['term'].lower()}"
            elif node_type == 'right':
                node_id = content['right_id']
            
            node = GraphNode(
                node_id=node_id,
                node_type=node_type,
                content=content
            )
            nodes.append(node)
            traversal_path.append(node_id)
        
        return nodes, edges, traversal_path
    
    def _calculate_text_match_score(self, text: str, terms: List[str]) -> float:
        """Calculate relevance score for text against search terms."""
        if not text or not terms:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        for term in terms:
            term_lower = term.lower()
            # Exact phrase match gets higher score
            if term_lower in text_lower:
                score += 2.0
            else:
                # Individual word matches
                words = term_lower.split()
                word_matches = sum(1 for word in words if word in text_lower)
                score += word_matches / len(words)
        
        return score / len(terms)  # Normalize by number of terms
    
    def traverse_relationships(self, start_node: str, 
                              relation_types: List[str],
                              max_depth: int = 3) -> List[GraphNode]:
        """
        Multi-hop graph traversal for complex queries.
        
        Args:
            start_node: Starting node ID
            relation_types: Types of relationships to follow
            max_depth: Maximum traversal depth
            
        Returns:
            List of nodes found through traversal
        """
        visited = set()
        result_nodes = []
        queue = [(start_node, 0)]  # (node_id, depth)
        
        while queue:
            current_node, depth = queue.pop(0)
            
            if current_node in visited or depth > max_depth:
                continue
            
            visited.add(current_node)
            
            # Add current node to results if it exists
            node = self._get_node_by_id(current_node)
            if node:
                result_nodes.append(node)
            
            # Find connected nodes
            if current_node in self.edges_from:
                for target_node, relation in self.edges_from[current_node]:
                    if relation in relation_types and target_node not in visited:
                        queue.append((target_node, depth + 1))
        
        return result_nodes
    
    def _get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by its ID from any node type."""
        # Check sections
        if node_id in self.section_by_id:
            return GraphNode(
                node_id=node_id,
                node_type='section',
                content=self.section_by_id[node_id]
            )
        
        # Check clauses
        if node_id in self.clause_by_id:
            return GraphNode(
                node_id=node_id,
                node_type='clause',
                content=self.clause_by_id[node_id]
            )
        
        # Check rights
        if node_id in self.right_by_id:
            return GraphNode(
                node_id=node_id,
                node_type='right',
                content=self.right_by_id[node_id]
            )
        
        # Check definitions (by reconstructing ID)
        for term, definition in self.definition_by_term.items():
            def_id = f"DEF_{term}"
            if node_id == def_id:
                return GraphNode(
                    node_id=def_id,
                    node_type='definition',
                    content=definition
                )
        
        return None
    
    def _calculate_confidence(self, intent: QueryIntent, nodes: List[GraphNode], edges: List[GraphEdge]) -> float:
        """Calculate confidence score based on retrieval success."""
        base_confidence = intent.confidence
        
        # Boost confidence if we found relevant nodes
        if nodes:
            retrieval_boost = min(len(nodes) / 5.0, 0.3)  # Max 0.3 boost
            base_confidence += retrieval_boost
        
        # Boost confidence if we have edges (relationships)
        if edges:
            relationship_boost = min(len(edges) / 10.0, 0.2)  # Max 0.2 boost
            base_confidence += relationship_boost
        
        # Penalize if no results found
        if not nodes:
            base_confidence *= 0.5
        
        return min(base_confidence, 1.0)
    
    def get_section_hierarchy(self, section_id: str) -> List[GraphNode]:
        """Get hierarchical context for a section (chapter, related sections)."""
        hierarchy = []
        
        if section_id not in self.section_by_id:
            return hierarchy
        
        section = self.section_by_id[section_id]
        chapter_id = section.get('chapter')
        
        if chapter_id:
            # Find other sections in the same chapter
            related_sections = [
                s for s in self.sections 
                if s.get('chapter') == chapter_id and s['section_id'] != section_id
            ]
            
            for related in related_sections[:3]:  # Limit to 3 related sections
                node = GraphNode(
                    node_id=related['section_id'],
                    node_type='section',
                    content=related
                )
                hierarchy.append(node)
        
        return hierarchy