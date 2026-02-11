"""
Response Validation Layer

This module implements comprehensive response validation to verify that LLM responses
are grounded in the knowledge graph and follow citation constraints.

Key components:
- ResponseValidator: Main validator coordinating all validation checks
- CitationValidator: Validates citation format and existence in knowledge graph
- ContentValidator: Validates content for hallucinations and accuracy
- FormatValidator: Validates response format and structure
- ConfidenceScorer: Calculates confidence scores based on validation results

The validation layer ensures:
1. All citations exist in the knowledge graph context
2. No unsupported legal claims or fabricated information
3. Proper response format and structure
4. Required disclaimers and appropriate language
5. Confidence scoring for human review thresholds
"""

import re
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from query_engine.context_builder import LLMContext
from query_engine.graph_traversal import GraphContext, GraphNode
from query_engine.query_parser import QueryIntent
from .prompt_templates import CitationConstraints, CitationFormat
from .confidence_scorer import ConfidenceScorer, ConfidenceScore


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Critical issues that should block response
    WARNING = "warning"  # Issues that should be flagged but not block
    INFO = "info"       # Informational notices


@dataclass
class ValidationIssue:
    """Represents a validation issue found in response"""
    severity: ValidationSeverity
    issue_type: str
    message: str
    location: Optional[str] = None  # Location in response where issue was found
    suggestion: Optional[str] = None  # Suggested fix
    confidence_impact: float = 0.0  # Impact on confidence score (-1.0 to 1.0)


@dataclass
class ValidationResult:
    """Result of comprehensive response validation"""
    is_valid: bool
    confidence_score: float
    issues: List[ValidationIssue]
    citation_count: int
    unsupported_claims: List[str]
    fabricated_references: List[str] = field(default_factory=list)
    missing_disclaimers: List[str] = field(default_factory=list)
    format_violations: List[str] = field(default_factory=list)
    corrected_response: Optional[str] = None
    requires_human_review: bool = False
    
    def has_errors(self) -> bool:
        """Check if validation found any errors"""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if validation found any warnings"""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues of specific severity"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_type(self, issue_type: str) -> List[ValidationIssue]:
        """Get issues of specific type"""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
    
    def should_block_response(self) -> bool:
        """Determine if response should be blocked from display"""
        return self.has_errors() or self.confidence_score < 0.5 or len(self.fabricated_references) > 0


class CitationValidator:
    """Validates citations in LLM responses against knowledge graph"""
    
    def __init__(self, knowledge_graph_path: str = "knowledge_graph"):
        """Initialize citation validator with knowledge graph access"""
        self.kg_path = Path(knowledge_graph_path)
        self._load_knowledge_graph_index()
        
        self.citation_patterns = {
            CitationFormat.STANDARD: r'\[Citation: ([^\]]+)\]',
            CitationFormat.DETAILED: r'\[Citation: ([^\]]+)\]',
            CitationFormat.BLUEBOOK: r'Consumer Protection Act § (\d+(?:\([^)]+\))?) \(India \d{4}\)',
            CitationFormat.INDIAN: r'Section (\d+(?:\([^)]+\))?), Consumer Protection Act, \d{4}'
        }
        
        # Legal claim patterns that require citations
        self.legal_claim_patterns = [
            r'\bsection\s+(\d+(?:\([^)]+\))?)\s+(?:states|provides|requires|prohibits|defines|establishes)',
            r'\bclause\s+\([^)]+\)\s+(?:states|provides|requires|prohibits)',
            r'\bthe\s+(?:consumer protection\s+)?act\s+(?:states|provides|requires|establishes)',
            r'\b(?:according to|under|pursuant to|as per)\s+(?:section|clause|the act)',
            r'\bconsumers?\s+(?:have the right|are entitled|can|must|shall)',
            r'\b(?:unfair trade practice|consumer right|complaint procedure)\b',
            r'\b(?:the law|statute|provision)\s+(?:states|requires|provides|prohibits)'
        ]
    
    def _load_knowledge_graph_index(self):
        """Load knowledge graph index for citation validation"""
        try:
            # Load all node types to build citation index
            self.valid_sections = set()
            self.valid_clauses = set()
            self.valid_definitions = set()
            self.valid_rights = set()
            
            # Load sections
            sections_file = self.kg_path / "nodes" / "sections.data.json"
            if sections_file.exists():
                with open(sections_file, 'r', encoding='utf-8') as f:
                    sections = json.load(f)
                    for section in sections:
                        section_num = section.get('section_number', '')
                        if section_num:
                            self.valid_sections.add(section_num)
                            self.valid_sections.add(f"Section {section_num}")
            
            # Load clauses
            clauses_file = self.kg_path / "nodes" / "clauses.data.json"
            if clauses_file.exists():
                with open(clauses_file, 'r', encoding='utf-8') as f:
                    clauses = json.load(f)
                    for clause in clauses:
                        clause_id = clause.get('clause_id', '')
                        parent = clause.get('parent_section', '')
                        label = clause.get('label', '')
                        if clause_id:
                            self.valid_clauses.add(clause_id)
                        if parent and label:
                            self.valid_clauses.add(f"{parent}, Clause {label}")
            
            # Load definitions
            definitions_file = self.kg_path / "nodes" / "definitions.data.json"
            if definitions_file.exists():
                with open(definitions_file, 'r', encoding='utf-8') as f:
                    definitions = json.load(f)
                    for definition in definitions:
                        term = definition.get('term', '')
                        if term:
                            self.valid_definitions.add(term.lower())
                            self.valid_definitions.add(f"Definition of {term}")
            
            # Load rights
            rights_file = self.kg_path / "nodes" / "rights.data.json"
            if rights_file.exists():
                with open(rights_file, 'r', encoding='utf-8') as f:
                    rights = json.load(f)
                    for right in rights:
                        right_id = right.get('right_id', '')
                        if right_id:
                            self.valid_rights.add(right_id)
            
            logger.info(f"Loaded citation index: {len(self.valid_sections)} sections, "
                       f"{len(self.valid_clauses)} clauses, {len(self.valid_definitions)} definitions, "
                       f"{len(self.valid_rights)} rights")
                       
        except Exception as e:
            logger.error(f"Failed to load knowledge graph index: {e}")
            # Initialize empty sets as fallback
            self.valid_sections = set()
            self.valid_clauses = set()
            self.valid_definitions = set()
            self.valid_rights = set()
    
    def validate_citations(self, response: str, context: LLMContext,
                          citation_format: CitationFormat) -> List[ValidationIssue]:
        """
        Validate citations in response against available context and knowledge graph.
        
        Args:
            response: LLM response to validate
            context: Available context with citations
            citation_format: Expected citation format
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Extract citations from response
        pattern = self.citation_patterns.get(citation_format, self.citation_patterns[CitationFormat.STANDARD])
        found_citations = re.findall(pattern, response)
        
        # Check if citations exist in context
        available_citations = set(context.citations.keys()) if context.citations else set()
        
        # Validate each citation
        for citation in found_citations:
            citation_key = citation.strip()
            
            # Check if citation exists in provided context
            if citation_key not in available_citations:
                # Check if it's a valid reference to knowledge graph
                if not self._is_valid_knowledge_graph_reference(citation_key):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        issue_type="invalid_citation",
                        message=f"Citation '{citation_key}' not found in available context or knowledge graph",
                        location=f"Citation: {citation_key}",
                        suggestion="Use only citations provided in the context or valid knowledge graph references",
                        confidence_impact=-0.3
                    ))
        
        # Check for legal claims without citations
        uncited_claims = self._find_uncited_legal_claims(response)
        for claim_text, claim_location in uncited_claims:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="uncited_claim",
                message=f"Legal claim '{claim_text}' may need citation",
                location=f"Position {claim_location}",
                suggestion="Add appropriate citation for legal claims",
                confidence_impact=-0.1
            ))
        
        # Check for fabricated section numbers
        fabricated_sections = self._find_fabricated_sections(response)
        for section_ref in fabricated_sections:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                issue_type="fabricated_section",
                message=f"Response mentions {section_ref} which does not exist in knowledge base",
                suggestion="Only reference sections that exist in the Consumer Protection Act, 2019",
                confidence_impact=-0.4
            ))
        
        return issues
    
    def _is_valid_knowledge_graph_reference(self, citation: str) -> bool:
        """Check if citation refers to valid knowledge graph entity"""
        citation_lower = citation.lower()
        
        # Check section references
        section_match = re.search(r'section\s+(\d+)', citation_lower)
        if section_match:
            section_num = section_match.group(1)
            return section_num in self.valid_sections or f"Section {section_num}" in self.valid_sections
        
        # Check definition references
        if "definition" in citation_lower:
            for term in self.valid_definitions:
                if term in citation_lower:
                    return True
        
        # Check clause references
        clause_match = re.search(r'clause\s+\([^)]+\)', citation_lower)
        if clause_match:
            return True  # More complex validation could be added
        
        return False
    
    def _find_uncited_legal_claims(self, response: str) -> List[Tuple[str, str]]:
        """Find legal claims in response that lack supporting citations"""
        uncited_claims = []
        
        for pattern in self.legal_claim_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                claim_text = match.group()
                claim_start = match.start()
                claim_end = match.end()
                
                # Check if there's a citation within 150 characters
                search_start = max(0, claim_start - 75)
                search_end = min(len(response), claim_end + 75)
                nearby_text = response[search_start:search_end]
                
                has_nearby_citation = bool(re.search(r'\[Citation: [^\]]+\]', nearby_text))
                
                if not has_nearby_citation:
                    location = f"{claim_start}-{claim_end}"
                    uncited_claims.append((claim_text.strip(), location))
        
        return uncited_claims
    
    def _find_fabricated_sections(self, response: str) -> List[str]:
        """Find references to sections that don't exist in knowledge graph"""
        fabricated = []
        
        # Find all section references
        section_patterns = [
            r'\bsection\s+(\d+(?:\([^)]+\))?)',
            r'\bsec\.\s*(\d+(?:\([^)]+\))?)',
            r'§\s*(\d+(?:\([^)]+\))?)'
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                section_ref = match.group(1)
                full_match = match.group(0)
                
                # Check if this section exists in our knowledge graph
                if (section_ref not in self.valid_sections and 
                    f"Section {section_ref}" not in self.valid_sections):
                    fabricated.append(full_match)
        
        return fabricated
    
    def extract_citation_references(self, response: str, 
                                  citation_format: CitationFormat) -> List[str]:
        """Extract all citation references from response"""
        pattern = self.citation_patterns.get(citation_format, self.citation_patterns[CitationFormat.STANDARD])
        return re.findall(pattern, response)


class ContentValidator:
    """Validates content for hallucinations, accuracy, and appropriate language"""
    
    def __init__(self):
        """Initialize content validator"""
        # Prohibited predictive language patterns
        self.prohibited_phrases = [
            r'\bi\s+(?:predict|believe|think|assume|guess)',
            r'\bin\s+my\s+opinion',
            r'\b(?:probably|likely|presumably)\s+(?:the\s+)?(?:court|judge|outcome)',
            r'\b(?:case\s+will\s+be\s+decided|judge\s+will\s+rule|court\s+will\s+find)',
            r'\b(?:you\s+will\s+win|you\s+will\s+lose|outcome\s+will\s+be)',
            r'\b(?:chances\s+are|odds\s+are|it\'s\s+likely\s+that)',
            r'\bprediction\b.*\b(?:case|outcome|decision)\b'
        ]
        
        # Required disclaimer patterns
        self.required_disclaimers = [
            r'\bnot\s+legal\s+advice\b',
            r'\binformation\s+only\b',
            r'\bconsult.*(?:lawyer|attorney|legal\s+professional)\b',
            r'\bdisclaimer\b',
            r'\beducational\s+purposes?\b',
            r'\bnon-binding\b'
        ]
        
        # Patterns indicating hallucinated legal content
        self.hallucination_patterns = [
            r'\bsection\s+(\d+)\s+of\s+(?!consumer\s+protection\s+act)',  # Wrong act references
            r'\b(?:supreme\s+court|high\s+court)\s+(?:ruled|decided|held)\b',  # Case law claims
            r'\b(?:landmark|precedent|judgment)\s+(?:case|decision)\b',  # Case law references
            r'\b(?:amendment|notification|gazette)\s+(?:dated|published)\b',  # Specific amendments
            r'\bunder\s+(?:article|section)\s+\d+\s+of\s+(?:constitution|ipc|crpc)\b'  # Other acts
        ]
        
        # Format requirements
        self.format_requirements = [
            ('legal_text_quotes', r'"[^"]*"'),  # Legal text should be quoted
            ('proper_structure', r'(?:^|\n)(?:\d+\.|•|\*|\-)\s+'),  # Structured format
            ('clear_sections', r'(?:^|\n)(?:\*\*|##|===).*(?:\*\*|##|===)')  # Section headers
        ]
    
    def validate_content(self, response: str, context: LLMContext,
                        graph_context: GraphContext) -> List[ValidationIssue]:
        """
        Validate response content for accuracy, appropriateness, and format.
        
        Args:
            response: LLM response to validate
            context: LLM context used for generation
            graph_context: Original graph context
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check for prohibited predictive language
        issues.extend(self._check_prohibited_language(response))
        
        # Check for required disclaimers
        issues.extend(self._check_disclaimers(response))
        
        # Check for hallucinated content
        issues.extend(self._check_hallucinations(response, context, graph_context))
        
        # Check response format and structure
        issues.extend(self._check_format_requirements(response))
        
        # Check for "information not available" appropriateness
        issues.extend(self._check_information_availability(response, context))
        
        # Check response completeness and quality
        issues.extend(self._check_response_quality(response))
        
        return issues
    
    def _check_prohibited_language(self, response: str) -> List[ValidationIssue]:
        """Check for prohibited predictive or opinion language"""
        issues = []
        
        for pattern in self.prohibited_phrases:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                phrase = match.group()
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    issue_type="predictive_language",
                    message=f"Response contains prohibited predictive language: '{phrase}'",
                    location=f"Position {match.start()}-{match.end()}",
                    suggestion="Remove predictions and focus on factual legal information",
                    confidence_impact=-0.4
                ))
        
        return issues
    
    def _check_disclaimers(self, response: str) -> List[ValidationIssue]:
        """Check for required disclaimers"""
        issues = []
        
        has_disclaimer = any(re.search(pattern, response, re.IGNORECASE) 
                           for pattern in self.required_disclaimers)
        
        if not has_disclaimer:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="missing_disclaimer",
                message="Response should include appropriate disclaimer about non-binding nature",
                suggestion="Add disclaimer: 'This information is for educational purposes only and does not constitute legal advice'",
                confidence_impact=-0.1
            ))
        
        return issues
    
    def _check_hallucinations(self, response: str, context: LLMContext, 
                             graph_context: GraphContext) -> List[ValidationIssue]:
        """Check for hallucinated legal content not in knowledge graph"""
        issues = []
        
        # Check for references to other acts or legal systems
        for pattern in self.hallucination_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                hallucination = match.group()
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    issue_type="hallucinated_content",
                    message=f"Response contains reference outside knowledge base: '{hallucination}'",
                    location=f"Position {match.start()}-{match.end()}",
                    suggestion="Only reference Consumer Protection Act, 2019 provisions available in knowledge base",
                    confidence_impact=-0.5
                ))
        
        # Check for fabricated definitions
        definition_claims = re.finditer(r'(?:defines?|means?|refers? to)\s+"([^"]+)"', response, re.IGNORECASE)
        for match in definition_claims:
            claimed_definition = match.group(1)
            if not self._is_definition_in_context(claimed_definition, context):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="unverified_definition",
                    message=f"Definition claim may not be supported: '{claimed_definition}'",
                    suggestion="Verify definition against knowledge graph",
                    confidence_impact=-0.2
                ))
        
        return issues
    
    def _check_format_requirements(self, response: str) -> List[ValidationIssue]:
        """Check response format and structure requirements"""
        issues = []
        
        # Check minimum length
        if len(response.strip()) < 50:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="insufficient_response",
                message="Response appears too brief to be helpful",
                suggestion="Provide more comprehensive information",
                confidence_impact=-0.1
            ))
        
        # Check maximum length (avoid overly verbose responses)
        if len(response) > 5000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="excessive_length",
                message="Response may be too lengthy",
                suggestion="Consider condensing to key information",
                confidence_impact=-0.05
            ))
        
        # Check for proper structure (should have clear sections or points)
        has_structure = bool(re.search(r'(?:^|\n)(?:\d+\.|•|\*|\-)\s+', response, re.MULTILINE))
        if not has_structure and len(response) > 500:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                issue_type="structure_suggestion",
                message="Long response could benefit from structured formatting",
                suggestion="Use bullet points or numbered lists for clarity"
            ))
        
        return issues
    
    def _check_information_availability(self, response: str, context: LLMContext) -> List[ValidationIssue]:
        """Check appropriateness of 'information not available' responses"""
        issues = []
        
        has_info_not_available = "information not available" in response.lower()
        has_limited_context = len(context.primary_provisions) == 0
        
        if has_limited_context and not has_info_not_available:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="missing_limitation_notice",
                message="Response should indicate when information is not available in knowledge base",
                suggestion="Include 'Information not available in current knowledge base' when context is insufficient",
                confidence_impact=-0.2
            ))
        
        if has_info_not_available and not has_limited_context:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="unnecessary_limitation",
                message="Response claims information not available but context contains relevant provisions",
                suggestion="Use available context to provide helpful information"
            ))
        
        return issues
    
    def _check_response_quality(self, response: str) -> List[ValidationIssue]:
        """Check overall response quality indicators"""
        issues = []
        
        # Check for repetitive content
        sentences = re.split(r'[.!?]+', response)
        if len(sentences) > 3:
            unique_sentences = set(s.strip().lower() for s in sentences if len(s.strip()) > 10)
            repetition_ratio = 1 - (len(unique_sentences) / len([s for s in sentences if len(s.strip()) > 10]))
            
            if repetition_ratio > 0.3:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="repetitive_content",
                    message="Response contains repetitive content",
                    suggestion="Reduce redundancy and improve clarity",
                    confidence_impact=-0.1
                ))
        
        # Check for coherence (basic check for contradictory statements)
        contradictory_patterns = [
            (r'\ballowed\b', r'\bprohibited\b'),
            (r'\brequired\b', r'\boptional\b'),
            (r'\bmust\b', r'\bmay\b'),
            (r'\byes\b', r'\bno\b')
        ]
        
        for positive_pattern, negative_pattern in contradictory_patterns:
            if (re.search(positive_pattern, response, re.IGNORECASE) and 
                re.search(negative_pattern, response, re.IGNORECASE)):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="potential_contradiction",
                    message="Response may contain contradictory statements",
                    suggestion="Review for consistency and clarity"
                ))
                break
        
        return issues
    
    def _is_definition_in_context(self, definition_text: str, context: LLMContext) -> bool:
        """Check if a definition claim is supported by context"""
        if not context.formatted_text:
            return False
        
        # Simple check - more sophisticated semantic matching could be added
        definition_lower = definition_text.lower()
        context_lower = context.formatted_text.lower()
        
        # Check if key words from definition appear in context
        definition_words = set(re.findall(r'\b\w+\b', definition_lower))
        context_words = set(re.findall(r'\b\w+\b', context_lower))
        
        # If most definition words appear in context, likely supported
        if len(definition_words) > 0:
            overlap_ratio = len(definition_words.intersection(context_words)) / len(definition_words)
            return overlap_ratio > 0.7
        
        return False


class ResponseValidator:
    """Main response validator that coordinates all validation checks"""
    
    def __init__(self, knowledge_graph_path: str = "knowledge_graph"):
        """Initialize response validator"""
        self.citation_validator = CitationValidator(knowledge_graph_path)
        self.content_validator = ContentValidator()
        self.confidence_scorer = ConfidenceScorer()
        self.knowledge_graph_path = knowledge_graph_path
        
        # Enhanced validation thresholds
        self.confidence_thresholds = {
            'high': 0.9,      # Auto-display without review
            'medium': 0.8,    # Display with caution notice  
            'low': 0.7,       # Flag for expert review
            'very_low': 0.5   # Block display, require review
        }
        
        # Citation density requirements by audience
        self.citation_requirements = {
            'citizen': {'min_citations': 1, 'claims_per_citation': 3},
            'lawyer': {'min_citations': 2, 'claims_per_citation': 2}, 
            'judge': {'min_citations': 3, 'claims_per_citation': 1}
        }
        
        logger.info("Initialized enhanced response validator")
    
    def validate_response(self, response: str, context: LLMContext,
                         graph_context: GraphContext,
                         citation_constraints: CitationConstraints,
                         query_intent: QueryIntent = None,
                         audience: str = "citizen") -> ValidationResult:
        """
        Comprehensive validation of LLM response.
        
        Args:
            response: LLM response to validate
            context: LLM context used for generation
            graph_context: Original graph context
            citation_constraints: Citation requirements
            audience: Target audience (citizen, lawyer, judge)
            
        Returns:
            ValidationResult with all validation findings
        """
        all_issues = []
        
        # Validate citations against knowledge graph
        citation_issues = self.citation_validator.validate_citations(
            response, context, citation_constraints.format_type
        )
        all_issues.extend(citation_issues)
        
        # Validate content for hallucinations and accuracy
        content_issues = self.content_validator.validate_content(
            response, context, graph_context
        )
        all_issues.extend(content_issues)
        
        # Enhanced knowledge graph validation
        kg_issues = self.validate_against_knowledge_graph(response, graph_context)
        all_issues.extend(kg_issues)
        
        # Validate citation density for audience
        citation_density_issues = self._validate_citation_density(response, audience)
        all_issues.extend(citation_density_issues)
        
        # Validate response format and structure
        format_issues = self._validate_response_format(response, citation_constraints)
        all_issues.extend(format_issues)
        
        # Count citations
        citation_count = len(self.citation_validator.extract_citation_references(
            response, citation_constraints.format_type
        ))
        
        # Identify unsupported claims with enhanced detection
        unsupported_claims = self._identify_unsupported_claims_enhanced(response, context)
        
        # Identify fabricated references
        fabricated_references = self._identify_fabricated_references(response, graph_context)
        
        # Calculate enhanced confidence score using dedicated scorer
        if query_intent:
            confidence_score_result = self.confidence_scorer.score_response(
                query_intent, graph_context, context, response, audience
            )
            confidence_score = confidence_score_result.overall_score
            requires_human_review = confidence_score_result.requires_human_review
            
            # Add confidence-based issues
            if confidence_score_result.requires_human_review:
                for reason in confidence_score_result.review_reasons:
                    all_issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        issue_type="confidence_review",
                        message=f"Human review required: {reason}",
                        confidence_impact=0.0  # Already factored into confidence score
                    ))
        else:
            # Fallback to legacy confidence calculation
            confidence_score = self._calculate_enhanced_confidence_score(
                response, context, graph_context, all_issues, citation_count, audience
            )
            requires_human_review = self._requires_human_review(
                confidence_score, all_issues, audience
            )
        
        # Determine if response is valid
        is_valid = self._determine_validity(all_issues, confidence_score, fabricated_references)
        
        # Apply citation constraints
        if citation_constraints.require_all_claims and len(unsupported_claims) > 0:
            is_valid = False
            all_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                issue_type="unsupported_claims",
                message=f"Found {len(unsupported_claims)} unsupported legal claims",
                suggestion="Ensure all legal claims have supporting citations",
                confidence_impact=-0.4
            ))
        
        if len(unsupported_claims) > citation_constraints.max_unsupported_claims:
            is_valid = False
        
        # Generate corrected response if needed
        corrected_response = None
        if not is_valid and self._can_auto_correct(all_issues):
            corrected_response = self._attempt_auto_correction(response, all_issues)
        
        # Extract missing disclaimers and format violations for detailed reporting
        missing_disclaimers = [
            issue.message for issue in all_issues 
            if issue.issue_type == "missing_disclaimer"
        ]
        
        format_violations = [
            issue.message for issue in all_issues 
            if issue.issue_type in ["format_violation", "structure_issue"]
        ]
        
        logger.info(f"Enhanced validation complete: valid={is_valid}, confidence={confidence_score:.2f}, "
                   f"issues={len(all_issues)}, citations={citation_count}, "
                   f"unsupported_claims={len(unsupported_claims)}, fabricated={len(fabricated_references)}")
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            issues=all_issues,
            citation_count=citation_count,
            unsupported_claims=unsupported_claims,
            fabricated_references=fabricated_references,
            missing_disclaimers=missing_disclaimers,
            format_violations=format_violations,
            corrected_response=corrected_response,
            requires_human_review=requires_human_review
        )
    
    def _identify_unsupported_claims(self, response: str, context: LLMContext) -> List[str]:
        """Identify claims in response that lack supporting citations"""
        unsupported = []
        
        # Look for legal statements without nearby citations
        legal_patterns = [
            r'section \d+ (?:states|provides|requires|prohibits)[^.]*\.',
            r'the act (?:defines|establishes|requires)[^.]*\.',
            r'consumers (?:have the right|are entitled|can)[^.]*\.'
        ]
        
        for pattern in legal_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                claim = match.group()
                # Check if there's a citation within 100 characters
                start = max(0, match.start() - 50)
                end = min(len(response), match.end() + 50)
                nearby_text = response[start:end]
                
                if not re.search(r'\[Citation: [^\]]+\]', nearby_text):
                    unsupported.append(claim.strip())
        
        return unsupported
    
    def _calculate_confidence_score(self, response: str, context: LLMContext,
                                  issues: List[ValidationIssue], citation_count: int) -> float:
        """Calculate confidence score based on validation results"""
        base_score = 1.0
        
        # Penalize for errors and warnings
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                base_score -= 0.3
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1
        
        # Reward for citations
        if citation_count > 0:
            citation_bonus = min(0.2, citation_count * 0.05)
            base_score += citation_bonus
        
        # Penalize for lack of citations when legal claims are present
        legal_claim_count = len(re.findall(r'\b(?:section|act|law|provision)\b', response, re.IGNORECASE))
        if legal_claim_count > 0 and citation_count == 0:
            base_score -= 0.4
        
        # Context coverage bonus
        if len(context.primary_provisions) > 0:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _can_auto_correct(self, issues: List[ValidationIssue]) -> bool:
        """Check if issues can be automatically corrected"""
        correctable_types = {"missing_disclaimer", "formatting_issue"}
        
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR and issue.issue_type not in correctable_types:
                return False
        
        return True
    
    def _attempt_auto_correction(self, response: str, issues: List[ValidationIssue]) -> str:
        """Attempt to automatically correct minor issues"""
        corrected = response
        
        for issue in issues:
            if issue.issue_type == "missing_disclaimer":
                # Add disclaimer at the end
                disclaimer = "\n\nDisclaimer: This information is provided for educational purposes only and does not constitute legal advice. For legal advice specific to your situation, please consult a qualified lawyer."
                corrected += disclaimer
        
        return corrected
    
    def validate_against_knowledge_graph(self, response: str, 
                                       graph_context: GraphContext) -> List[ValidationIssue]:
        """
        Validate response against knowledge graph for factual accuracy.
        
        Args:
            response: Response to validate
            graph_context: Knowledge graph context
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Extract factual claims from response
        section_claims = re.findall(r'section (\d+) (?:states|provides|defines) ([^.]+)', 
                                  response, re.IGNORECASE)
        
        # Verify against knowledge graph
        available_sections = {}
        for node in graph_context.nodes:
            if node.node_type == 'section':
                section_num = node.content.get('section_number', '')
                section_text = node.content.get('text', '')
                available_sections[section_num] = section_text
        
        for section_num, claimed_content in section_claims:
            if section_num in available_sections:
                actual_content = available_sections[section_num].lower()
                claimed_content_lower = claimed_content.lower()
                
                # Simple semantic check (could be enhanced with NLP)
                key_words = claimed_content_lower.split()[:5]  # First 5 words
                if not any(word in actual_content for word in key_words if len(word) > 3):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        issue_type="content_mismatch",
                        message=f"Claimed content for Section {section_num} may not match actual text",
                        suggestion="Verify content against source text"
                    ))
        
        return issues
    
    def _validate_citation_density(self, response: str, audience: str) -> List[ValidationIssue]:
        """Validate citation density based on audience requirements"""
        issues = []
        
        requirements = self.citation_requirements.get(audience, self.citation_requirements['citizen'])
        
        # Count legal claims
        legal_claim_patterns = [
            r'\bsection\s+\d+\s+(?:states|provides|requires|prohibits|defines)',
            r'\bthe\s+(?:consumer protection\s+)?act\s+(?:states|provides|requires)',
            r'\bconsumers?\s+(?:have the right|are entitled|can|must|shall)',
            r'\b(?:according to|under|pursuant to|as per)\s+(?:section|clause|the act)',
            r'\b(?:unfair trade practice|consumer right|complaint procedure)\b'
        ]
        
        legal_claims = 0
        for pattern in legal_claim_patterns:
            legal_claims += len(re.findall(pattern, response, re.IGNORECASE))
        
        # Count citations
        citation_count = len(re.findall(r'\[Citation: [^\]]+\]', response))
        
        # Check minimum citations
        if citation_count < requirements['min_citations'] and legal_claims > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="insufficient_citations",
                message=f"Response has {citation_count} citations but {audience} audience requires minimum {requirements['min_citations']}",
                suggestion=f"Add more citations to meet {audience} requirements",
                confidence_impact=-0.2
            ))
        
        # Check citation density
        if legal_claims > 0:
            claims_per_citation = legal_claims / max(1, citation_count)
            if claims_per_citation > requirements['claims_per_citation']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="low_citation_density",
                    message=f"Citation density too low: {claims_per_citation:.1f} claims per citation (max: {requirements['claims_per_citation']})",
                    suggestion="Add more citations to support legal claims",
                    confidence_impact=-0.1
                ))
        
        return issues
    
    def _validate_response_format(self, response: str, citation_constraints: CitationConstraints) -> List[ValidationIssue]:
        """Validate response format and structure"""
        issues = []
        
        # Check for proper citation format
        expected_format = citation_constraints.format_type.value
        if expected_format == "standard":
            # Check for standard citation format
            invalid_citations = re.findall(r'\[(?:Ref|Reference|Source): [^\]]+\]', response)
            for invalid in invalid_citations:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="citation_format",
                    message=f"Non-standard citation format found: {invalid}",
                    suggestion="Use [Citation: ...] format",
                    confidence_impact=-0.05
                ))
        
        # Check for proper structure
        if len(response) > 500:  # Only check structure for longer responses
            has_structure = bool(re.search(r'(?:^|\n)(?:\d+\.|•|\*|\-)\s+', response, re.MULTILINE))
            has_headers = bool(re.search(r'(?:^|\n)(?:\*\*|##).*(?:\*\*|##)', response))
            
            if not has_structure and not has_headers:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    issue_type="structure_suggestion",
                    message="Long response could benefit from structured formatting",
                    suggestion="Use bullet points, numbered lists, or headers for clarity"
                ))
        
        # Check for legal text quotation
        legal_text_mentions = len(re.findall(r'\b(?:section|clause|provision)\s+\d+', response, re.IGNORECASE))
        quoted_text = len(re.findall(r'"[^"]{20,}"', response))  # Quotes with substantial content
        
        if legal_text_mentions > 2 and quoted_text == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                issue_type="missing_quotes",
                message="Consider quoting relevant legal text for clarity",
                suggestion="Quote key legal provisions to distinguish from explanations"
            ))
        
        return issues
    
    def _identify_unsupported_claims_enhanced(self, response: str, context: LLMContext) -> List[str]:
        """Enhanced identification of unsupported legal claims"""
        unsupported = []
        
        # Enhanced legal claim patterns
        enhanced_patterns = [
            r'section\s+\d+\s+(?:clearly\s+)?(?:states|provides|requires|prohibits|mandates|establishes)[^.]*\.',
            r'the\s+(?:consumer protection\s+)?act\s+(?:explicitly\s+)?(?:defines|requires|prohibits|allows)[^.]*\.',
            r'consumers?\s+(?:have\s+the\s+)?(?:right|entitlement)\s+to\s+[^.]*\.',
            r'(?:according\s+to|under|pursuant\s+to|as\s+per)\s+(?:section|clause|the\s+act)[^.]*\.',
            r'(?:the\s+law|statute|provision|regulation)\s+(?:clearly\s+)?(?:states|requires|prohibits)[^.]*\.',
            r'(?:unfair\s+trade\s+practice|consumer\s+right|complaint\s+procedure)\s+(?:is\s+defined|means|includes)[^.]*\.'
        ]
        
        for pattern in enhanced_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                claim = match.group()
                claim_start = match.start()
                claim_end = match.end()
                
                # Check for citations within 200 characters (expanded range)
                search_start = max(0, claim_start - 100)
                search_end = min(len(response), claim_end + 100)
                nearby_text = response[search_start:search_end]
                
                # Look for various citation formats
                citation_patterns = [
                    r'\[Citation: [^\]]+\]',
                    r'\[Ref: [^\]]+\]',
                    r'\(Section\s+\d+[^)]*\)',
                    r'\(CPA\s+2019[^)]*\)'
                ]
                
                has_nearby_citation = any(
                    re.search(pattern, nearby_text, re.IGNORECASE) 
                    for pattern in citation_patterns
                )
                
                if not has_nearby_citation:
                    # Check if claim is supported by context
                    if not self._is_claim_supported_by_context(claim, context):
                        unsupported.append(claim.strip())
        
        return unsupported
    
    def _identify_fabricated_references(self, response: str, graph_context: GraphContext) -> List[str]:
        """Identify references to legal provisions that don't exist in knowledge graph"""
        fabricated = []
        
        # Get available sections from graph context
        available_sections = set()
        available_clauses = set()
        
        for node in graph_context.nodes:
            if node.node_type == 'section':
                section_num = node.content.get('section_number', '')
                if section_num:
                    available_sections.add(section_num)
            elif node.node_type == 'clause':
                clause_id = node.content.get('clause_id', '')
                if clause_id:
                    available_clauses.add(clause_id)
        
        # Find section references in response
        section_patterns = [
            r'\bsection\s+(\d+(?:\([^)]+\))?)',
            r'\bsec\.\s*(\d+(?:\([^)]+\))?)',
            r'§\s*(\d+(?:\([^)]+\))?)'
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                section_ref = match.group(1)
                full_match = match.group(0)
                
                # Check if section exists in knowledge graph
                if section_ref not in available_sections:
                    # Also check without parenthetical parts
                    base_section = re.sub(r'\([^)]+\)', '', section_ref)
                    if base_section not in available_sections:
                        fabricated.append(full_match)
        
        # Find clause references
        clause_matches = re.finditer(r'\bclause\s+\([^)]+\)', response, re.IGNORECASE)
        for match in clause_matches:
            clause_ref = match.group(0)
            # Simple check - could be enhanced with more sophisticated matching
            if not any(clause_ref.lower() in clause_id.lower() for clause_id in available_clauses):
                fabricated.append(clause_ref)
        
        return list(set(fabricated))  # Remove duplicates
    
    def _calculate_enhanced_confidence_score(self, response: str, context: LLMContext,
                                           graph_context: GraphContext, issues: List[ValidationIssue], 
                                           citation_count: int, audience: str) -> float:
        """Calculate enhanced confidence score with multiple factors"""
        
        # Start with base score
        base_score = 1.0
        
        # Factor 1: Issue penalties (but not too harsh)
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                penalty = issue.confidence_impact if issue.confidence_impact else -0.2  # Reduced from -0.3
            elif issue.severity == ValidationSeverity.WARNING:
                penalty = issue.confidence_impact if issue.confidence_impact else -0.05  # Reduced from -0.1
            else:  # INFO
                penalty = -0.01
            base_score += penalty
        
        # Factor 2: Citation quality (40% weight)
        citation_score = self._calculate_citation_score(response, context, citation_count)
        
        # Factor 3: Graph coverage (30% weight)
        coverage_score = self._calculate_coverage_score(response, graph_context)
        
        # Factor 4: Response quality (20% weight)
        quality_score = self._calculate_quality_score(response, audience)
        
        # Factor 5: Temporal validity (10% weight)
        temporal_score = 1.0  # Placeholder - would check data freshness
        
        # Weighted combination (more generous)
        weighted_score = (
            0.3 * citation_score +
            0.2 * coverage_score +
            0.3 * quality_score +
            0.1 * temporal_score +
            0.1  # Base bonus for any response
        )
        
        # Combine with base score (penalties) - use average instead of min
        final_score = (base_score + weighted_score) / 2
        
        return max(0.0, min(1.0, final_score))
    
    def _calculate_citation_score(self, response: str, context: LLMContext, citation_count: int) -> float:
        """Calculate citation quality score"""
        if citation_count == 0:
            # Check if legal claims exist - if no claims, no citations needed
            legal_claims = len(re.findall(r'\b(?:section|act|law|provision|consumer|right)\b', response, re.IGNORECASE))
            if legal_claims == 0:
                return 1.0  # No claims, no citations needed - perfect score
            else:
                return 0.3  # Has claims but no citations - low but not zero
        
        # Count legal claims
        legal_claims = len(re.findall(r'\b(?:section|act|law|provision|consumer|right)\b', response, re.IGNORECASE))
        
        if legal_claims == 0:
            return 1.0  # No claims, citations present anyway - good
        
        # Citation density - more generous calculation
        citation_density = citation_count / max(1, legal_claims)
        density_score = min(1.0, citation_density + 0.3)  # Bonus for having any citations
        
        # Citation validity (check if citations exist in context)
        valid_citations = 0
        citation_refs = re.findall(r'\[Citation: ([^\]]+)\]', response)
        
        for citation in citation_refs:
            if context.citations and citation in context.citations:
                valid_citations += 1
        
        validity_score = valid_citations / max(1, len(citation_refs)) if citation_refs else 0.5
        
        return (density_score + validity_score) / 2
    
    def _calculate_coverage_score(self, response: str, graph_context: GraphContext) -> float:
        """Calculate knowledge graph coverage score"""
        if not graph_context.nodes:
            return 0.0
        
        # Count entities mentioned in response
        mentioned_entities = 0
        total_entities = len(graph_context.nodes)
        
        for node in graph_context.nodes:
            if node.node_type == 'section':
                section_num = node.content.get('section_number', '')
                if section_num and f"section {section_num}" in response.lower():
                    mentioned_entities += 1
            elif node.node_type == 'definition':
                term = node.content.get('term', '')
                if term and term.lower() in response.lower():
                    mentioned_entities += 1
        
        return mentioned_entities / max(1, total_entities)
    
    def _calculate_quality_score(self, response: str, audience: str) -> float:
        """Calculate response quality score"""
        quality_score = 1.0
        
        # Length appropriateness
        length = len(response)
        if audience == 'citizen':
            # Citizens prefer concise but complete responses
            if length < 100:
                quality_score -= 0.3  # Too brief
            elif length > 2000:
                quality_score -= 0.2  # Too verbose
        elif audience == 'lawyer':
            # Lawyers prefer detailed responses
            if length < 200:
                quality_score -= 0.2
        
        # Readability (simple heuristic)
        sentences = len(re.split(r'[.!?]+', response))
        words = len(response.split())
        avg_sentence_length = words / max(1, sentences)
        
        if audience == 'citizen' and avg_sentence_length > 25:
            quality_score -= 0.1  # Too complex for citizens
        
        # Structure bonus
        has_structure = bool(re.search(r'(?:^|\n)(?:\d+\.|•|\*|\-)\s+', response, re.MULTILINE))
        if has_structure and length > 300:
            quality_score += 0.1
        
        return max(0.0, min(1.0, quality_score))
    
    def _determine_validity(self, issues: List[ValidationIssue], confidence_score: float, 
                           fabricated_references: List[str]) -> bool:
        """Determine if response is valid for display"""
        
        # Block if there are fabricated references
        if fabricated_references:
            return False
        
        # Block if there are critical errors
        critical_errors = [
            issue for issue in issues 
            if issue.severity == ValidationSeverity.ERROR and 
            issue.issue_type in ['fabricated_section', 'hallucinated_content', 'predictive_language']
        ]
        
        if critical_errors:
            return False
        
        # Block if confidence is very low
        if confidence_score < self.confidence_thresholds['very_low']:
            return False
        
        return True
    
    def _requires_human_review(self, confidence_score: float, issues: List[ValidationIssue], 
                              audience: str) -> bool:
        """Determine if response requires human review"""
        
        # Always review for judge audience if confidence is not high
        if audience == 'judge' and confidence_score < self.confidence_thresholds['high']:
            return True
        
        # Review if confidence is below medium threshold
        if confidence_score < self.confidence_thresholds['medium']:
            return True
        
        # Review if there are specific issue types
        review_triggering_issues = [
            'content_mismatch', 'unverified_definition', 'potential_contradiction',
            'hallucinated_content', 'fabricated_section'
        ]
        
        for issue in issues:
            if issue.issue_type in review_triggering_issues:
                return True
        
        return False
    
    def _is_claim_supported_by_context(self, claim: str, context: LLMContext) -> bool:
        """Check if a legal claim is supported by the provided context"""
        if not context.formatted_text:
            return False
        
        # Extract key terms from claim
        claim_words = set(re.findall(r'\b\w{4,}\b', claim.lower()))  # Words with 4+ chars
        context_words = set(re.findall(r'\b\w{4,}\b', context.formatted_text.lower()))
        
        # Calculate overlap
        if len(claim_words) == 0:
            return False
        
        overlap_ratio = len(claim_words.intersection(context_words)) / len(claim_words)
        
        # Require at least 60% overlap for support
        return overlap_ratio >= 0.6