"""
Query Parser for Natural Language Intent Extraction

This module implements the QueryParser class that extracts legal intent from user queries
and identifies relevant entities for knowledge graph traversal.

Supports intent types:
- definition_lookup: User wants to understand legal terms
- section_retrieval: User wants specific section information
- rights_query: User wants to know about consumer rights
- scenario_analysis: User wants analysis of a legal scenario
"""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Supported query intent types"""
    DEFINITION_LOOKUP = "definition_lookup"
    SECTION_RETRIEVAL = "section_retrieval"
    RIGHTS_QUERY = "rights_query"
    SCENARIO_ANALYSIS = "scenario_analysis"


@dataclass
class QueryIntent:
    """Represents the parsed intent from a user query"""
    intent_type: IntentType
    entities: List[str]
    section_numbers: List[str]
    legal_terms: List[str]
    confidence: float
    original_query: str
    temporal_context: Optional[str] = None


class QueryParser:
    """Parse natural language queries to extract legal intent and entities."""
    
    def __init__(self):
        """Initialize the query parser with pattern matching rules."""
        self._init_patterns()
        self._init_legal_terms()
        self._init_section_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for intent classification."""
        self.intent_patterns = {
            IntentType.DEFINITION_LOOKUP: [
                r'\b(?:what\s+is|define|definition\s+of|meaning\s+of|explain)\b.*?\b(?:consumer|trader|defect|deficiency|unfair\s+trade|advertisement)\b',
                r'\b(?:consumer|trader|defect|deficiency|unfair\s+trade|advertisement)\b.*?\b(?:means?|definition|defined\s+as)\b',
                r'\b(?:term|word)\b.*?\b(?:consumer|trader|defect|deficiency|unfair\s+trade|advertisement)\b'
            ],
            IntentType.SECTION_RETRIEVAL: [
                r'\bsection\s+\d+\b',
                r'\bs\.\s*\d+\b',
                r'\bsec\.\s*\d+\b',
                r'\b(?:show|tell|find|get)\b.*?\bsection\b',
                r'\b(?:chapter|part)\s+\d+\b'
            ],
            IntentType.RIGHTS_QUERY: [
                r'\b(?:rights?|entitle[dm]?|protection)\b.*?\b(?:consumer|buyer|customer)\b',
                r'\b(?:consumer|buyer|customer)\b.*?\b(?:rights?|entitle[dm]?|protection)\b',
                r'\b(?:what\s+can|how\s+can)\b.*?\b(?:consumer|buyer|customer)\b.*?\b(?:do|claim|get)\b',
                r'\b(?:remedies|redressal|compensation)\b'
            ],
            IntentType.SCENARIO_ANALYSIS: [
                r'\b(?:if|suppose|what\s+happens|scenario|case|situation)\b',
                r'\b(?:can\s+i|should\s+i|may\s+i)\b.*?\b(?:file|complain|sue|claim)\b',
                r'\b(?:defective|faulty|damaged)\b.*?\b(?:product|goods|service)\b',
                r'\b(?:unfair|misleading|false)\b.*?\b(?:advertisement|practice|contract)\b'
            ]
        }
    
    def _init_legal_terms(self):
        """Initialize common legal terms for entity extraction."""
        self.legal_terms = {
            'consumer', 'trader', 'manufacturer', 'service provider', 'complainant',
            'defect', 'deficiency', 'unfair trade practice', 'restrictive trade practice',
            'misleading advertisement', 'false advertisement', 'consumer rights',
            'product liability', 'compensation', 'redressal', 'complaint',
            'district commission', 'state commission', 'national commission',
            'central authority', 'consumer protection', 'goods', 'services',
            'warranty', 'guarantee', 'endorsement', 'e-commerce', 'direct selling'
        }
        
        # Create variations for better matching
        self.term_variations = {}
        for term in self.legal_terms:
            variations = [term, term.replace(' ', '_'), term.replace(' ', '')]
            self.term_variations[term] = variations
    
    def _init_section_patterns(self):
        """Initialize patterns for section number extraction."""
        self.section_patterns = [
            r'\bsection\s+(\d+(?:\.\d+)*)\b',
            r'\bs\.\s*(\d+(?:\.\d+)*)\b',
            r'\bsec\.\s*(\d+(?:\.\d+)*)\b',
            r'\b(\d+)\s*(?:of|under)\s+(?:cpa|consumer\s+protection\s+act)\b'
        ]
    
    def parse_query(self, query: str, language: str = "en") -> QueryIntent:
        """
        Extract legal intent from user query.
        
        Args:
            query: User's natural language query
            language: Language of the query (default: "en")
            
        Returns:
            QueryIntent with extracted intent type, entities, and confidence score
        """
        query_lower = query.lower().strip()
        
        # Extract entities first
        entities = self._extract_entities(query_lower)
        section_numbers = self._extract_section_numbers(query_lower)
        legal_terms = self._extract_legal_terms(query_lower)
        
        # Classify intent
        intent_type, confidence = self._classify_intent(query_lower)
        
        # Extract temporal context if present
        temporal_context = self._extract_temporal_context(query_lower)
        
        return QueryIntent(
            intent_type=intent_type,
            entities=entities,
            section_numbers=section_numbers,
            legal_terms=legal_terms,
            confidence=confidence,
            original_query=query,
            temporal_context=temporal_context
        )
    
    def _classify_intent(self, query: str) -> tuple[IntentType, float]:
        """
        Classify the intent of the query using pattern matching.
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (intent_type, confidence_score)
        """
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matches += 1
                    score += 1
            
            if matches > 0:
                # Normalize score by number of patterns
                intent_scores[intent_type] = score / len(patterns)
        
        if not intent_scores:
            # Default to scenario analysis for unmatched queries
            return IntentType.SCENARIO_ANALYSIS, 0.3
        
        # Return intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], min(best_intent[1], 1.0)
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract general entities from the query.
        
        Args:
            query: Lowercase query string
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract quoted terms
        quoted_terms = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted_terms)
        
        # Extract capitalized terms (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        entities.extend(capitalized)
        
        return list(set(entities))
    
    def _extract_section_numbers(self, query: str) -> List[str]:
        """
        Extract section numbers from the query.
        
        Args:
            query: Lowercase query string
            
        Returns:
            List of section numbers found in the query
        """
        section_numbers = []
        
        for pattern in self.section_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            section_numbers.extend(matches)
        
        return list(set(section_numbers))
    
    def _extract_legal_terms(self, query: str) -> List[str]:
        """
        Extract legal terms from the query.
        
        Args:
            query: Lowercase query string
            
        Returns:
            List of legal terms found in the query
        """
        found_terms = []
        
        for term in self.legal_terms:
            # Check exact match and variations
            variations = self.term_variations.get(term, [term])
            
            for variation in variations:
                pattern = r'\b' + re.escape(variation.lower()) + r'\b'
                if re.search(pattern, query):
                    found_terms.append(term)
                    break
        
        return list(set(found_terms))
    
    def _extract_temporal_context(self, query: str) -> Optional[str]:
        """
        Extract temporal context from the query (for amendment tracking).
        
        Args:
            query: Lowercase query string
            
        Returns:
            Temporal context string if found, None otherwise
        """
        temporal_patterns = [
            r'\b(?:in|during|as\s+of|before|after)\s+(\d{4})\b',
            r'\b(\d{4})\s+(?:version|amendment|act)\b',
            r'\b(?:current|latest|present|now)\b'
        ]
        
        for pattern in temporal_patterns:
            match = re.search(pattern, query)
            if match:
                if 'current' in query or 'latest' in query or 'present' in query or 'now' in query:
                    return 'current'
                return match.group(1) if match.groups() else match.group(0)
        
        return None
    
    def get_query_complexity(self, intent: QueryIntent) -> str:
        """
        Assess the complexity of the query for routing decisions.
        
        Args:
            intent: Parsed query intent
            
        Returns:
            Complexity level: 'simple', 'moderate', or 'complex'
        """
        complexity_score = 0
        
        # Multiple entities increase complexity
        if len(intent.entities) > 2:
            complexity_score += 1
        
        # Multiple legal terms increase complexity
        if len(intent.legal_terms) > 3:
            complexity_score += 1
        
        # Scenario analysis is inherently more complex
        if intent.intent_type == IntentType.SCENARIO_ANALYSIS:
            complexity_score += 2
        
        # Temporal queries are more complex
        if intent.temporal_context:
            complexity_score += 1
        
        # Low confidence suggests complex/ambiguous query
        if intent.confidence < 0.6:
            complexity_score += 1
        
        if complexity_score <= 1:
            return 'simple'
        elif complexity_score <= 3:
            return 'moderate'
        else:
            return 'complex'