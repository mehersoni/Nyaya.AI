"""
Confidence Scoring System for LLM Responses

This module implements the ConfidenceScorer class that calculates confidence scores
for LLM responses based on multiple factors including graph coverage, citation density,
and reasoning chain metrics.

Key components:
- ConfidenceScorer: Main scorer that calculates overall confidence
- ConfidenceComponents: Detailed breakdown of confidence factors
- ConfidenceThresholds: Empirically calibrated thresholds for human review

The confidence scoring system ensures:
1. Graph coverage assessment based on knowledge graph completeness
2. Citation density evaluation appropriate for target audience
3. Reasoning chain complexity analysis
4. Response quality metrics
5. Human review flagging based on calibrated thresholds
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from query_engine.context_builder import LLMContext
from query_engine.graph_traversal import GraphContext
from query_engine.query_parser import QueryIntent, IntentType


logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for response classification"""
    VERY_HIGH = "very_high"  # 0.9-1.0: Auto-display without review
    HIGH = "high"            # 0.8-0.9: Display with minimal review
    MEDIUM = "medium"        # 0.7-0.8: Display with caution notice
    LOW = "low"              # 0.5-0.7: Flag for expert review
    VERY_LOW = "very_low"    # 0.0-0.5: Block display, require review


@dataclass
class ConfidenceComponents:
    """Detailed breakdown of confidence score calculation"""
    graph_coverage: float          # 0.0-1.0: % of query entities found in graph
    citation_density: float        # 0.0-1.0: Citations per legal claim ratio
    reasoning_chain_score: float   # 0.0-1.0: Multi-hop reasoning quality
    response_quality: float        # 0.0-1.0: Overall response quality
    temporal_validity: float       # 0.0-1.0: Data freshness and validity
    audience_appropriateness: float # 0.0-1.0: Language/complexity for audience
    
    def get_weighted_average(self, weights: Dict[str, float]) -> float:
        """Calculate weighted average of components"""
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        
        weighted_sum = (
            self.graph_coverage * weights.get('graph_coverage', 0.3) +
            self.citation_density * weights.get('citation_density', 0.25) +
            self.reasoning_chain_score * weights.get('reasoning_chain', 0.2) +
            self.response_quality * weights.get('response_quality', 0.15) +
            self.temporal_validity * weights.get('temporal_validity', 0.05) +
            self.audience_appropriateness * weights.get('audience_appropriateness', 0.05)
        )
        
        return weighted_sum / total_weight


@dataclass
class ConfidenceScore:
    """Complete confidence score with metadata"""
    overall_score: float
    confidence_level: ConfidenceLevel
    components: ConfidenceComponents
    requires_human_review: bool
    review_reasons: List[str]
    metadata: Dict[str, Any]
    
    def should_block_display(self) -> bool:
        """Determine if response should be blocked from display"""
        return self.confidence_level == ConfidenceLevel.VERY_LOW
    
    def get_display_message(self) -> str:
        """Get user-facing confidence message"""
        if self.confidence_level == ConfidenceLevel.VERY_HIGH:
            return "High confidence response based on comprehensive legal sources."
        elif self.confidence_level == ConfidenceLevel.HIGH:
            return "Response based on available legal sources with good coverage."
        elif self.confidence_level == ConfidenceLevel.MEDIUM:
            return "Response based on limited legal sources. Please verify independently."
        elif self.confidence_level == ConfidenceLevel.LOW:
            return "Limited confidence due to incomplete information. Expert review recommended."
        else:
            return "Very limited confidence. This response requires expert validation."


class ConfidenceScorer:
    """Assign confidence scores to responses based on multiple factors."""
    
    def __init__(self):
        """Initialize confidence scorer with empirically calibrated thresholds."""
        
        # Empirically calibrated thresholds (based on requirements)
        self.confidence_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.9,
            ConfidenceLevel.HIGH: 0.8,      # Human review threshold from requirements
            ConfidenceLevel.MEDIUM: 0.7,
            ConfidenceLevel.LOW: 0.5,
            ConfidenceLevel.VERY_LOW: 0.0
        }
        
        # Audience-specific weights for confidence components
        self.audience_weights = {
            'citizen': {
                'graph_coverage': 0.25,
                'citation_density': 0.20,
                'reasoning_chain': 0.15,
                'response_quality': 0.25,
                'temporal_validity': 0.10,
                'audience_appropriateness': 0.05
            },
            'lawyer': {
                'graph_coverage': 0.30,
                'citation_density': 0.30,
                'reasoning_chain': 0.20,
                'response_quality': 0.15,
                'temporal_validity': 0.05,
                'audience_appropriateness': 0.00
            },
            'judge': {
                'graph_coverage': 0.35,
                'citation_density': 0.35,
                'reasoning_chain': 0.25,
                'response_quality': 0.05,
                'temporal_validity': 0.00,
                'audience_appropriateness': 0.00
            }
        }
        
        # Citation requirements by audience (from validation layer)
        self.citation_requirements = {
            'citizen': {'min_citations': 1, 'claims_per_citation': 3},
            'lawyer': {'min_citations': 2, 'claims_per_citation': 2},
            'judge': {'min_citations': 3, 'claims_per_citation': 1}
        }
        
        logger.info("Initialized confidence scorer with empirically calibrated thresholds")
    
    def score_response(self, query_intent: QueryIntent, 
                      graph_context: GraphContext,
                      llm_context: LLMContext,
                      llm_response: str,
                      audience: str = "citizen") -> ConfidenceScore:
        """
        Calculate comprehensive confidence score for LLM response.
        
        Args:
            query_intent: Original query intent from parser
            graph_context: Knowledge graph context used for retrieval
            llm_context: Formatted context provided to LLM
            llm_response: Generated LLM response
            audience: Target audience (citizen, lawyer, judge)
            
        Returns:
            ConfidenceScore with detailed breakdown and metadata
        """
        
        # Calculate individual confidence components
        components = self._calculate_confidence_components(
            query_intent, graph_context, llm_context, llm_response, audience
        )
        
        # Get audience-specific weights
        weights = self.audience_weights.get(audience, self.audience_weights['citizen'])
        
        # Calculate weighted overall score
        overall_score = components.get_weighted_average(weights)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(overall_score)
        
        # Determine if human review is required
        requires_review, review_reasons = self._requires_human_review(
            overall_score, components, audience, query_intent
        )
        
        # Collect metadata
        metadata = {
            'audience': audience,
            'intent_type': query_intent.intent_type.value,
            'graph_nodes_count': len(graph_context.nodes),
            'citation_count': self._count_citations(llm_response),
            'response_length': len(llm_response),
            'weights_used': weights
        }
        
        confidence_score = ConfidenceScore(
            overall_score=overall_score,
            confidence_level=confidence_level,
            components=components,
            requires_human_review=requires_review,
            review_reasons=review_reasons,
            metadata=metadata
        )
        
        logger.info(f"Calculated confidence score: {overall_score:.3f} ({confidence_level.value}) "
                   f"for {audience} audience, review_required={requires_review}")
        
        return confidence_score
    
    def _calculate_confidence_components(self, query_intent: QueryIntent,
                                       graph_context: GraphContext,
                                       llm_context: LLMContext,
                                       llm_response: str,
                                       audience: str) -> ConfidenceComponents:
        """Calculate individual confidence components."""
        
        # 1. Graph Coverage Score
        graph_coverage = self._calculate_graph_coverage(query_intent, graph_context)
        
        # 2. Citation Density Score
        citation_density = self._calculate_citation_density(llm_response, audience)
        
        # 3. Reasoning Chain Score
        reasoning_chain_score = self._calculate_reasoning_chain_score(
            query_intent, graph_context, llm_response
        )
        
        # 4. Response Quality Score
        response_quality = self._calculate_response_quality(llm_response, audience)
        
        # 5. Temporal Validity Score
        temporal_validity = self._calculate_temporal_validity(graph_context)
        
        # 6. Audience Appropriateness Score
        audience_appropriateness = self._calculate_audience_appropriateness(
            llm_response, audience
        )
        
        return ConfidenceComponents(
            graph_coverage=graph_coverage,
            citation_density=citation_density,
            reasoning_chain_score=reasoning_chain_score,
            response_quality=response_quality,
            temporal_validity=temporal_validity,
            audience_appropriateness=audience_appropriateness
        )
    
    def _calculate_graph_coverage(self, query_intent: QueryIntent, 
                                 graph_context: GraphContext) -> float:
        """
        Calculate graph coverage score based on how well the knowledge graph
        covers the entities and concepts in the query.
        """
        if not graph_context.nodes:
            return 0.0
        
        # Count query entities that were found in graph
        total_entities = len(query_intent.legal_terms) + len(query_intent.section_numbers)
        if total_entities == 0:
            # If no specific entities requested, base on graph confidence
            return graph_context.confidence
        
        found_entities = 0
        
        # Check if legal terms are covered
        for term in query_intent.legal_terms:
            term_lower = term.lower()
            for node in graph_context.nodes:
                if node.node_type == 'definition':
                    if term_lower in node.content.get('term', '').lower():
                        found_entities += 1
                        break
                elif term_lower in node.get_text().lower():
                    found_entities += 1
                    break
        
        # Check if section numbers are covered
        for section_num in query_intent.section_numbers:
            for node in graph_context.nodes:
                if node.node_type == 'section':
                    if section_num == node.content.get('section_number', ''):
                        found_entities += 1
                        break
        
        coverage_ratio = found_entities / total_entities
        
        # Boost score based on graph traversal quality
        traversal_boost = min(len(graph_context.nodes) / 10.0, 0.3)  # Max 0.3 boost
        
        return min(1.0, coverage_ratio + traversal_boost)
    
    def _calculate_citation_density(self, llm_response: str, audience: str) -> float:
        """
        Calculate citation density score based on citations per legal claim
        and audience requirements.
        """
        # Count citations in response
        citation_count = self._count_citations(llm_response)
        
        # Count legal claims that require citations
        legal_claims = self._count_legal_claims(llm_response)
        
        if legal_claims == 0:
            # No legal claims, no citations needed
            return 1.0 if citation_count == 0 else 0.9  # Slight penalty for unnecessary citations
        
        if citation_count == 0:
            # Has legal claims but no citations
            return 0.1
        
        # Get audience requirements
        requirements = self.citation_requirements.get(
            audience, self.citation_requirements['citizen']
        )
        
        # Calculate citation density
        claims_per_citation = legal_claims / citation_count
        max_claims_per_citation = requirements['claims_per_citation']
        
        # Score based on how well it meets requirements
        if claims_per_citation <= max_claims_per_citation:
            density_score = 1.0
        else:
            # Penalty for too few citations
            density_score = max(0.2, max_claims_per_citation / claims_per_citation)
        
        # Check minimum citation requirement
        min_citations = requirements['min_citations']
        if citation_count < min_citations:
            min_citation_penalty = citation_count / min_citations
            density_score *= min_citation_penalty
        
        return min(1.0, density_score)
    
    def _calculate_reasoning_chain_score(self, query_intent: QueryIntent,
                                       graph_context: GraphContext,
                                       llm_response: str) -> float:
        """
        Calculate reasoning chain score based on multi-hop reasoning complexity
        and logical coherence.
        """
        base_score = 0.7  # Base score for any response
        
        # Boost for complex intent types that require reasoning
        if query_intent.intent_type == IntentType.SCENARIO_ANALYSIS:
            base_score += 0.1
        elif query_intent.intent_type == IntentType.RIGHTS_QUERY:
            base_score += 0.05
        
        # Boost for multi-hop graph traversal
        if len(graph_context.nodes) > 3:
            multi_hop_boost = min((len(graph_context.nodes) - 3) * 0.05, 0.2)
            base_score += multi_hop_boost
        
        # Boost for cross-references in response
        cross_ref_count = len(re.findall(r'\b(?:see also|refer to|as per|according to)\b', 
                                       llm_response, re.IGNORECASE))
        if cross_ref_count > 0:
            base_score += min(cross_ref_count * 0.03, 0.1)
        
        # Boost for logical structure indicators
        structure_indicators = [
            r'\b(?:therefore|thus|consequently|as a result)\b',
            r'\b(?:because|since|due to|given that)\b',
            r'\b(?:however|but|although|while)\b',
            r'\b(?:first|second|third|finally)\b'
        ]
        
        logical_structure_count = 0
        for pattern in structure_indicators:
            logical_structure_count += len(re.findall(pattern, llm_response, re.IGNORECASE))
        
        if logical_structure_count > 0:
            base_score += min(logical_structure_count * 0.02, 0.1)
        
        # Penalty for contradictory statements
        contradictory_patterns = [
            (r'\ballowed\b', r'\bprohibited\b'),
            (r'\brequired\b', r'\boptional\b'),
            (r'\bmust\b', r'\bmay\b')
        ]
        
        for positive_pattern, negative_pattern in contradictory_patterns:
            if (re.search(positive_pattern, llm_response, re.IGNORECASE) and 
                re.search(negative_pattern, llm_response, re.IGNORECASE)):
                base_score -= 0.2
                break
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_response_quality(self, llm_response: str, audience: str) -> float:
        """
        Calculate response quality score based on length, structure,
        readability, and completeness.
        """
        quality_score = 0.8  # Base quality score
        
        # Length appropriateness
        length = len(llm_response)
        
        if audience == 'citizen':
            # Citizens prefer concise but complete responses
            if 150 <= length <= 1500:
                quality_score += 0.1
            elif length < 100:
                quality_score -= 0.3  # Too brief
            elif length > 2500:
                quality_score -= 0.2  # Too verbose
        elif audience == 'lawyer':
            # Lawyers prefer detailed responses
            if 300 <= length <= 3000:
                quality_score += 0.1
            elif length < 200:
                quality_score -= 0.2
        elif audience == 'judge':
            # Judges prefer comprehensive responses
            if 400 <= length <= 4000:
                quality_score += 0.1
            elif length < 300:
                quality_score -= 0.2
        
        # Structure and formatting
        has_structure = bool(re.search(r'(?:^|\n)(?:\d+\.|•|\*|\-)\s+', 
                                     llm_response, re.MULTILINE))
        has_headers = bool(re.search(r'(?:^|\n)(?:\*\*|##).*(?:\*\*|##)', llm_response))
        
        if (has_structure or has_headers) and length > 300:
            quality_score += 0.1
        
        # Readability (sentence length analysis)
        sentences = re.split(r'[.!?]+', llm_response)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if sentences:
            words = llm_response.split()
            avg_sentence_length = len(words) / len(sentences)
            
            if audience == 'citizen':
                # Citizens prefer shorter sentences
                if avg_sentence_length <= 20:
                    quality_score += 0.05
                elif avg_sentence_length > 30:
                    quality_score -= 0.1
            elif audience in ['lawyer', 'judge']:
                # Legal professionals can handle longer sentences
                if 15 <= avg_sentence_length <= 35:
                    quality_score += 0.05
        
        # Completeness indicators
        completeness_indicators = [
            r'\bin conclusion\b',
            r'\bto summarize\b',
            r'\btherefore\b',
            r'\bdisclaimer\b'
        ]
        
        completeness_count = 0
        for pattern in completeness_indicators:
            if re.search(pattern, llm_response, re.IGNORECASE):
                completeness_count += 1
        
        if completeness_count > 0:
            quality_score += min(completeness_count * 0.03, 0.1)
        
        # Penalty for repetitive content
        if len(sentences) > 3:
            unique_sentences = set(s.lower().strip() for s in sentences)
            repetition_ratio = 1 - (len(unique_sentences) / len(sentences))
            
            if repetition_ratio > 0.3:
                quality_score -= 0.2
        
        return max(0.0, min(1.0, quality_score))
    
    def _calculate_temporal_validity(self, graph_context: GraphContext) -> float:
        """
        Calculate temporal validity score based on data freshness
        and amendment tracking.
        """
        # For Phase 1, assume all data is current (CPA 2019)
        # In future phases, this would check amendment dates
        
        if not graph_context.nodes:
            return 0.5  # Neutral score for no data
        
        # Check if we have recent data
        has_current_data = any(
            'Consumer Protection Act, 2019' in node.content.get('act', '')
            for node in graph_context.nodes
            if node.node_type == 'section'
        )
        
        if has_current_data:
            return 1.0
        else:
            return 0.8  # Slight penalty for potentially outdated data
    
    def _calculate_audience_appropriateness(self, llm_response: str, audience: str) -> float:
        """
        Calculate audience appropriateness score based on language complexity
        and technical detail level.
        """
        appropriateness_score = 0.8  # Base score
        
        # Count technical legal terms
        technical_terms = [
            r'\bpursuant to\b', r'\bwhereas\b', r'\bnotwithstanding\b',
            r'\bhereinafter\b', r'\baforesaid\b', r'\bthereof\b',
            r'\binter alia\b', r'\bviz\b', r'\bqua\b'
        ]
        
        technical_count = 0
        for pattern in technical_terms:
            technical_count += len(re.findall(pattern, llm_response, re.IGNORECASE))
        
        # Count simple explanatory phrases
        simple_phrases = [
            r'\bin simple terms\b', r'\bthis means\b', r'\bfor example\b',
            r'\bin other words\b', r'\bto put it simply\b'
        ]
        
        simple_count = 0
        for pattern in simple_phrases:
            simple_count += len(re.findall(pattern, llm_response, re.IGNORECASE))
        
        if audience == 'citizen':
            # Citizens prefer simple language
            if technical_count > 3:
                appropriateness_score -= 0.3
            if simple_count > 0:
                appropriateness_score += 0.2
        elif audience == 'lawyer':
            # Lawyers expect some technical language
            if technical_count > 0:
                appropriateness_score += 0.1
            if technical_count > 10:
                appropriateness_score -= 0.1  # Too technical even for lawyers
        elif audience == 'judge':
            # Judges expect precise legal language
            if technical_count > 0:
                appropriateness_score += 0.2
        
        return max(0.0, min(1.0, appropriateness_score))
    
    def _count_citations(self, response: str) -> int:
        """Count citations in response."""
        citation_patterns = [
            r'\[Citation: [^\]]+\]',
            r'\[Ref: [^\]]+\]',
            r'\(Section\s+\d+[^)]*\)',
            r'\(CPA\s+2019[^)]*\)'
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            total_citations += len(re.findall(pattern, response, re.IGNORECASE))
        
        return total_citations
    
    def _count_legal_claims(self, response: str) -> int:
        """Count legal claims that require citations."""
        legal_claim_patterns = [
            r'\bsection\s+\d+\s+(?:states|provides|requires|prohibits|defines|establishes)',
            r'\bthe\s+(?:consumer protection\s+)?act\s+(?:states|provides|requires|establishes)',
            r'\bconsumers?\s+(?:have the right|are entitled|can|must|shall)',
            r'\b(?:according to|under|pursuant to|as per)\s+(?:section|clause|the act)',
            r'\b(?:unfair trade practice|consumer right|complaint procedure)\s+(?:is|means|includes)',
            r'\b(?:the law|statute|provision)\s+(?:states|requires|provides|prohibits)'
        ]
        
        total_claims = 0
        for pattern in legal_claim_patterns:
            total_claims += len(re.findall(pattern, response, re.IGNORECASE))
        
        return total_claims
    
    def _determine_confidence_level(self, overall_score: float) -> ConfidenceLevel:
        """Determine confidence level based on overall score."""
        if overall_score >= self.confidence_thresholds[ConfidenceLevel.VERY_HIGH]:
            return ConfidenceLevel.VERY_HIGH
        elif overall_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif overall_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif overall_score >= self.confidence_thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _requires_human_review(self, overall_score: float, 
                              components: ConfidenceComponents,
                              audience: str,
                              query_intent: QueryIntent) -> Tuple[bool, List[str]]:
        """
        Determine if response requires human review based on confidence score
        and other factors.
        """
        review_reasons = []
        
        # Always review if below threshold (0.8 from requirements)
        if overall_score < self.confidence_thresholds[ConfidenceLevel.HIGH]:
            review_reasons.append(f"Overall confidence score {overall_score:.2f} below threshold 0.8")
        
        # Always review for judge audience if not very high confidence
        if audience == 'judge' and overall_score < self.confidence_thresholds[ConfidenceLevel.VERY_HIGH]:
            review_reasons.append("Judge audience requires very high confidence")
        
        # Review if graph coverage is very low
        if components.graph_coverage < 0.3:
            review_reasons.append(f"Low graph coverage: {components.graph_coverage:.2f}")
        
        # Review if citation density is very low
        if components.citation_density < 0.4:
            review_reasons.append(f"Low citation density: {components.citation_density:.2f}")
        
        # Review for complex queries with low reasoning score
        if (query_intent.intent_type == IntentType.SCENARIO_ANALYSIS and 
            components.reasoning_chain_score < 0.6):
            review_reasons.append("Complex scenario analysis with low reasoning score")
        
        # Review if response quality is very low
        if components.response_quality < 0.5:
            review_reasons.append(f"Low response quality: {components.response_quality:.2f}")
        
        requires_review = len(review_reasons) > 0
        
        return requires_review, review_reasons
    
    def update_thresholds(self, new_thresholds: Dict[ConfidenceLevel, float]):
        """
        Update confidence thresholds based on empirical calibration.
        
        Args:
            new_thresholds: Updated threshold values
        """
        for level, threshold in new_thresholds.items():
            if 0.0 <= threshold <= 1.0:
                self.confidence_thresholds[level] = threshold
                logger.info(f"Updated {level.value} threshold to {threshold}")
            else:
                logger.warning(f"Invalid threshold value {threshold} for {level.value}")
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get current calibration statistics and thresholds."""
        return {
            'thresholds': {level.value: threshold for level, threshold in self.confidence_thresholds.items()},
            'audience_weights': self.audience_weights,
            'citation_requirements': self.citation_requirements
        }