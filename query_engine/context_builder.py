"""
Context Builder for LLM Integration

This module implements the ContextBuilder class that formats graph data retrieved
from knowledge graph traversal into structured context suitable for LLM consumption.

The context is structured with:
- Primary provisions (directly relevant to query)
- Related provisions (cross-references and hierarchical context)
- Definitions (for legal terms)
- Hierarchical context (parent sections/chapters)
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from query_engine.graph_traversal import GraphContext, GraphNode, GraphEdge
from query_engine.query_parser import QueryIntent, IntentType


@dataclass
class LLMContext:
    """Structured context for LLM consumption"""
    formatted_text: str
    citations: Dict[str, str]  # citation_key -> full_citation
    metadata: Dict[str, any]
    primary_provisions: List[str]
    related_provisions: List[str]
    definitions: List[str]
    hierarchical_context: List[str]
    
    def get_total_length(self) -> int:
        """Get total character length of formatted text"""
        return len(self.formatted_text)
    
    def get_citation_count(self) -> int:
        """Get number of citations included"""
        return len(self.citations)


class ContextBuilder:
    """Build structured context for LLM from graph data."""
    
    def __init__(self, max_context_length: int = 8000):
        """
        Initialize the context builder.
        
        Args:
            max_context_length: Maximum character length for LLM context
        """
        self.max_context_length = max_context_length
        self.citation_counter = 0
    
    def build_context(self, graph_context: GraphContext, intent: QueryIntent) -> LLMContext:
        """
        Format graph data for LLM consumption.
        
        Args:
            graph_context: Retrieved graph context from traversal
            intent: Original query intent
            
        Returns:
            LLMContext with structured text and metadata
        """
        self.citation_counter = 0  # Reset counter
        
        # Categorize nodes by relevance and type
        primary_nodes = graph_context.get_primary_nodes()
        related_nodes = graph_context.get_related_nodes()
        
        # Separate by node type
        sections = [n for n in graph_context.nodes if n.node_type == 'section']
        definitions = [n for n in graph_context.nodes if n.node_type == 'definition']
        rights = [n for n in graph_context.nodes if n.node_type == 'right']
        clauses = [n for n in graph_context.nodes if n.node_type == 'clause']
        
        # Build context sections
        context_parts = []
        citations = {}
        metadata = {
            'intent_type': intent.intent_type.value,
            'confidence': graph_context.confidence,
            'node_count': len(graph_context.nodes),
            'edge_count': len(graph_context.edges)
        }
        
        # 1. Primary Provisions Section
        primary_text, primary_citations = self._build_primary_provisions(primary_nodes, intent)
        if primary_text:
            context_parts.append("=== PRIMARY LEGAL PROVISIONS ===")
            context_parts.append(primary_text)
            citations.update(primary_citations)
        
        # 2. Definitions Section
        definitions_text, def_citations = self._build_definitions_section(definitions)
        if definitions_text:
            context_parts.append("\n=== LEGAL DEFINITIONS ===")
            context_parts.append(definitions_text)
            citations.update(def_citations)
        
        # 3. Consumer Rights Section (for rights queries)
        if intent.intent_type == IntentType.RIGHTS_QUERY and rights:
            rights_text, rights_citations = self._build_rights_section(rights)
            if rights_text:
                context_parts.append("\n=== CONSUMER RIGHTS ===")
                context_parts.append(rights_text)
                citations.update(rights_citations)
        
        # 4. Related Provisions Section
        related_text, related_citations = self._build_related_provisions(related_nodes, graph_context.edges)
        if related_text:
            context_parts.append("\n=== RELATED PROVISIONS ===")
            context_parts.append(related_text)
            citations.update(related_citations)
        
        # 5. Hierarchical Context (if needed)
        hierarchical_text, hier_citations = self._build_hierarchical_context(sections)
        if hierarchical_text:
            context_parts.append("\n=== CONTEXTUAL INFORMATION ===")
            context_parts.append(hierarchical_text)
            citations.update(hier_citations)
        
        # Combine all parts
        formatted_text = "\n".join(context_parts)
        
        # Truncate if too long
        if len(formatted_text) > self.max_context_length:
            formatted_text = self._truncate_context(formatted_text, citations)
        
        return LLMContext(
            formatted_text=formatted_text,
            citations=citations,
            metadata=metadata,
            primary_provisions=self._extract_provision_list(primary_nodes),
            related_provisions=self._extract_provision_list(related_nodes),
            definitions=[d.content.get('term', '') for d in definitions],
            hierarchical_context=self._extract_hierarchical_list(sections)
        )
    
    def _build_primary_provisions(self, nodes: List[GraphNode], intent: QueryIntent) -> tuple[str, Dict[str, str]]:
        """Build the primary provisions section."""
        if not nodes:
            return "", {}
        
        parts = []
        citations = {}
        
        for node in nodes:
            citation_key = self._get_next_citation_key()
            citation_text = node.get_citation()
            citations[citation_key] = citation_text
            
            if node.node_type == 'section':
                section_text = self._format_section_node(node, citation_key)
                parts.append(section_text)
            elif node.node_type == 'definition':
                def_text = self._format_definition_node(node, citation_key)
                parts.append(def_text)
            elif node.node_type == 'right':
                right_text = self._format_right_node(node, citation_key)
                parts.append(right_text)
        
        return "\n\n".join(parts), citations
    
    def _build_definitions_section(self, definitions: List[GraphNode]) -> tuple[str, Dict[str, str]]:
        """Build the definitions section."""
        if not definitions:
            return "", {}
        
        parts = []
        citations = {}
        
        for definition in definitions:
            citation_key = self._get_next_citation_key()
            citation_text = definition.get_citation()
            citations[citation_key] = citation_text
            
            term = definition.content.get('term', '')
            definition_text = definition.content.get('definition', '')
            
            formatted = f"**{term.upper()}**: {definition_text} [{citation_key}]"
            parts.append(formatted)
        
        return "\n\n".join(parts), citations
    
    def _build_rights_section(self, rights: List[GraphNode]) -> tuple[str, Dict[str, str]]:
        """Build the consumer rights section with comprehensive coverage."""
        if not rights:
            return "", {}
        
        parts = []
        citations = {}
        
        # Always include the six fundamental consumer rights from Section 2(9)
        fundamental_rights = [
            {
                "title": "Right to Safety",
                "description": "Protection against goods and services which are hazardous to life and property",
                "section": "Section 2(9)(a)",
                "key": "safety"
            },
            {
                "title": "Right to be Informed", 
                "description": "Right to be informed about the quality, quantity, potency, purity, standard and price of goods or services",
                "section": "Section 2(9)(b)",
                "key": "informed"
            },
            {
                "title": "Right to Choose",
                "description": "Right to be assured of access to a variety of goods and services at competitive prices",
                "section": "Section 2(9)(c)",
                "key": "choose"
            },
            {
                "title": "Right to be Heard",
                "description": "Right to be heard and to be assured that consumer interests will receive due consideration",
                "section": "Section 2(9)(d)",
                "key": "heard"
            },
            {
                "title": "Right to Seek Redressal",
                "description": "Right to seek redressal against unfair trade practices or restrictive trade practices or unscrupulous exploitation of consumers",
                "section": "Section 2(9)(e)",
                "key": "redressal"
            },
            {
                "title": "Right to Consumer Education",
                "description": "Right to consumer education and to be informed about consumer rights and remedies",
                "section": "Section 2(9)(f)",
                "key": "education"
            }
        ]
        
        parts.append("**Fundamental Consumer Rights (Section 2(9) of Consumer Protection Act, 2019):**")
        parts.append("")
        
        # Add fundamental rights with citations
        for i, right in enumerate(fundamental_rights, 1):
            citation_key = self._get_next_citation_key()
            citations[citation_key] = f"Section 2, Consumer Protection Act, 2019"
            
            parts.append(f"{i}. **{right['title']}**: {right['description']} [{citation_key}]")
        
        parts.append("")
        
        # Group additional rights by type
        rights_by_type = {}
        for right in rights:
            right_type = right.content.get('right_type', 'unknown')
            if right_type not in rights_by_type:
                rights_by_type[right_type] = []
            rights_by_type[right_type].append(right)
        
        # Add procedural and remedy rights
        for right_type, type_rights in rights_by_type.items():
            if right_type == 'procedural_right':
                parts.append("**Procedural Rights:**")
            elif right_type == 'remedy_right':
                parts.append("**Remedy Rights:**")
            elif right_type != 'consumer_right':  # Skip consumer_right as we handled them above
                parts.append(f"**{right_type.replace('_', ' ').title()} Rights:**")
            else:
                continue  # Skip consumer_right as we handled them above
            
            for right in type_rights:
                citation_key = self._get_next_citation_key()
                citation_text = right.get_citation()
                citations[citation_key] = citation_text
                
                description = right.content.get('description', '')
                scope = right.content.get('scope', '')
                
                right_text = f"• {description}"
                if scope:
                    right_text += f" (Scope: {scope})"
                right_text += f" [{citation_key}]"
                
                parts.append(right_text)
            
            parts.append("")  # Add spacing between right types
        
        return "\n".join(parts), citations
    
    def _build_related_provisions(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> tuple[str, Dict[str, str]]:
        """Build the related provisions section."""
        if not nodes:
            return "", {}
        
        parts = []
        citations = {}
        
        # Group nodes by relationship type
        referenced_nodes = set()
        for edge in edges:
            referenced_nodes.add(edge.to_node)
        
        for node in nodes:
            if node.node_id in referenced_nodes:
                citation_key = self._get_next_citation_key()
                citation_text = node.get_citation()
                citations[citation_key] = citation_text
                
                if node.node_type == 'section':
                    section_text = self._format_section_node(node, citation_key, brief=True)
                    parts.append(section_text)
        
        return "\n\n".join(parts), citations
    
    def _build_hierarchical_context(self, sections: List[GraphNode]) -> tuple[str, Dict[str, str]]:
        """Build hierarchical context information."""
        if not sections:
            return "", {}
        
        parts = []
        citations = {}
        
        # Group sections by chapter
        chapters = {}
        for section in sections:
            chapter = section.content.get('chapter_title', 'Unknown Chapter')
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(section)
        
        for chapter_title, chapter_sections in chapters.items():
            if len(chapter_sections) > 1:  # Only show if multiple sections
                parts.append(f"**{chapter_title}:**")
                for section in chapter_sections[:3]:  # Limit to 3 sections
                    section_num = section.content.get('section_number', '')
                    section_title = section.content.get('title', '')
                    parts.append(f"• Section {section_num}: {section_title}")
                parts.append("")
        
        return "\n".join(parts), citations
    
    def _format_section_node(self, node: GraphNode, citation_key: str, brief: bool = False) -> str:
        """Format a section node for display."""
        section_num = node.content.get('section_number', '')
        title = node.content.get('title', '')
        text = node.content.get('text', '')
        
        if brief:
            # Brief format for related provisions
            formatted = f"**Section {section_num}**: {title} [{citation_key}]"
            if len(text) > 200:
                formatted += f"\n{text[:200]}..."
            else:
                formatted += f"\n{text}"
        else:
            # Full format for primary provisions
            formatted = f"**Section {section_num}: {title}** [{citation_key}]\n\n{text}"
        
        return formatted
    
    def _format_definition_node(self, node: GraphNode, citation_key: str) -> str:
        """Format a definition node for display."""
        term = node.content.get('term', '')
        definition = node.content.get('definition', '')
        
        return f"**Definition of '{term}'** [{citation_key}]\n\n{definition}"
    
    def _format_right_node(self, node: GraphNode, citation_key: str) -> str:
        """Format a right node for display."""
        description = node.content.get('description', '')
        scope = node.content.get('scope', '')
        enforcement = node.content.get('enforcement_mechanism', '')
        
        formatted = f"**Consumer Right** [{citation_key}]\n\n{description}"
        
        if scope:
            formatted += f"\n\n**Scope**: {scope}"
        
        if enforcement:
            formatted += f"\n\n**Enforcement**: {enforcement}"
        
        return formatted
    
    def _get_next_citation_key(self) -> str:
        """Get the next citation key in sequence."""
        self.citation_counter += 1
        return f"Citation-{self.citation_counter}"
    
    def _extract_provision_list(self, nodes: List[GraphNode]) -> List[str]:
        """Extract list of provision identifiers."""
        provisions = []
        for node in nodes:
            if node.node_type == 'section':
                section_num = node.content.get('section_number', '')
                provisions.append(f"Section {section_num}")
            elif node.node_type == 'clause':
                parent = node.content.get('parent_section', '')
                label = node.content.get('label', '')
                provisions.append(f"{parent}, Clause {label}")
        return provisions
    
    def _extract_hierarchical_list(self, sections: List[GraphNode]) -> List[str]:
        """Extract hierarchical context list."""
        context = []
        chapters = set()
        
        for section in sections:
            chapter_title = section.content.get('chapter_title', '')
            if chapter_title and chapter_title not in chapters:
                chapters.add(chapter_title)
                context.append(chapter_title)
        
        return list(context)
    
    def _truncate_context(self, text: str, citations: Dict[str, str]) -> str:
        """Truncate context to fit within length limits while preserving structure."""
        if len(text) <= self.max_context_length:
            return text
        
        # Split into sections
        sections = text.split("===")
        
        # Keep primary provisions and definitions, truncate others
        truncated_sections = []
        current_length = 0
        
        for i, section in enumerate(sections):
            section_length = len(section)
            
            if i <= 2:  # Keep first 3 sections (primary + definitions)
                truncated_sections.append(section)
                current_length += section_length
            elif current_length + section_length < self.max_context_length:
                truncated_sections.append(section)
                current_length += section_length
            else:
                # Add truncation notice
                remaining_space = self.max_context_length - current_length - 100
                if remaining_space > 0:
                    truncated_section = section[:remaining_space] + "\n\n[Context truncated due to length limits]"
                    truncated_sections.append(truncated_section)
                break
        
        return "===".join(truncated_sections)
    
    def format_for_audience(self, context: LLMContext, audience: str = "citizen") -> LLMContext:
        """
        Format context for specific audience (citizen, lawyer, judge).
        
        Args:
            context: Original LLM context
            audience: Target audience type
            
        Returns:
            Modified LLMContext formatted for the audience
        """
        if audience == "citizen":
            # Simplify language and add explanatory notes
            formatted_text = self._simplify_for_citizens(context.formatted_text)
        elif audience == "lawyer":
            # Add more technical details and cross-references
            formatted_text = self._enhance_for_lawyers(context.formatted_text, context.citations)
        elif audience == "judge":
            # Add precedent context and legal analysis
            formatted_text = self._enhance_for_judges(context.formatted_text, context.citations)
        else:
            formatted_text = context.formatted_text
        
        return LLMContext(
            formatted_text=formatted_text,
            citations=context.citations,
            metadata={**context.metadata, 'audience': audience},
            primary_provisions=context.primary_provisions,
            related_provisions=context.related_provisions,
            definitions=context.definitions,
            hierarchical_context=context.hierarchical_context
        )
    
    def _simplify_for_citizens(self, text: str) -> str:
        """Simplify legal text for citizen audience."""
        # Add explanatory notes for complex terms
        simplified = text
        
        # Add citizen-friendly headers
        simplified = simplified.replace("=== PRIMARY LEGAL PROVISIONS ===", 
                                      "=== RELEVANT LAWS THAT APPLY TO YOUR SITUATION ===")
        simplified = simplified.replace("=== LEGAL DEFINITIONS ===", 
                                      "=== WHAT THESE LEGAL TERMS MEAN ===")
        simplified = simplified.replace("=== CONSUMER RIGHTS ===", 
                                      "=== YOUR RIGHTS AS A CONSUMER ===")
        
        return simplified
    
    def _enhance_for_lawyers(self, text: str, citations: Dict[str, str]) -> str:
        """Enhance context for lawyer audience with technical details."""
        enhanced = text
        
        # Add citation summary at the end
        if citations:
            enhanced += "\n\n=== CITATION SUMMARY ===\n"
            for key, citation in citations.items():
                enhanced += f"{key}: {citation}\n"
        
        return enhanced
    
    def _enhance_for_judges(self, text: str, citations: Dict[str, str]) -> str:
        """Enhance context for judge audience with legal analysis."""
        enhanced = text
        
        # Add judicial context note
        enhanced = "=== JUDICIAL CONTEXT ===\n" + \
                  "The following provisions are relevant for judicial consideration:\n\n" + enhanced
        
        return enhanced