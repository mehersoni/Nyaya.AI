"""
Demonstration of the Confidence Scoring System

This script demonstrates the ConfidenceScorer implementation with various
scenarios to show how it calculates confidence scores based on graph coverage,
citation density, and reasoning chain metrics.
"""

from llm_integration.confidence_scorer import ConfidenceScorer, ConfidenceLevel
from llm_integration.validation import ResponseValidator
from query_engine.query_parser import QueryIntent, IntentType
from query_engine.graph_traversal import GraphContext, GraphNode
from query_engine.context_builder import LLMContext
from llm_integration.prompt_templates import CitationConstraints, CitationFormat
from unittest.mock import Mock

def create_mock_data():
    """Create mock data for demonstration."""
    
    # Create query intent
    query_intent = Mock()
    query_intent.intent_type = IntentType.SCENARIO_ANALYSIS
    query_intent.legal_terms = ["consumer", "unfair trade practice", "complaint"]
    query_intent.section_numbers = ["2", "10"]
    query_intent.confidence = 0.8
    
    # Create graph context with multiple nodes
    graph_context = Mock()
    graph_context.confidence = 0.9
    
    # Section node
    section_node = Mock()
    section_node.node_type = 'section'
    section_node.content = {
        'section_number': '2',
        'act': 'Consumer Protection Act, 2019',
        'text': 'This section defines consumer, unfair trade practice, and related terms'
    }
    section_node.get_text.return_value = section_node.content['text']
    
    # Another section node
    section_node_2 = Mock()
    section_node_2.node_type = 'section'
    section_node_2.content = {
        'section_number': '10',
        'act': 'Consumer Protection Act, 2019',
        'text': 'This section deals with complaint procedures and remedies'
    }
    section_node_2.get_text.return_value = section_node_2.content['text']
    
    # Definition node
    definition_node = Mock()
    definition_node.node_type = 'definition'
    definition_node.content = {
        'term': 'consumer',
        'definition': 'A person who buys goods or services for consideration'
    }
    definition_node.get_text.return_value = definition_node.content['definition']
    
    # Rights node
    rights_node = Mock()
    rights_node.node_type = 'right'
    rights_node.content = {
        'right_id': 'RIGHT_001',
        'description': 'Right to be protected against unfair trade practices',
        'right_type': 'consumer_right'
    }
    rights_node.get_text.return_value = rights_node.content['description']
    
    graph_context.nodes = [section_node, section_node_2, definition_node, rights_node]
    
    # Create LLM context
    llm_context = Mock()
    llm_context.formatted_text = """
    === PRIMARY LEGAL PROVISIONS ===
    Section 2: Definitions - This section defines consumer, unfair trade practice, and related terms
    Section 10: Complaint Procedures - This section deals with complaint procedures and remedies
    
    === LEGAL DEFINITIONS ===
    CONSUMER: A person who buys goods or services for consideration
    
    === CONSUMER RIGHTS ===
    Right to be protected against unfair trade practices
    """
    llm_context.citations = {
        "Citation-1": "Section 2, Consumer Protection Act, 2019",
        "Citation-2": "Section 10, Consumer Protection Act, 2019",
        "Citation-3": "Definition of Consumer, Section 2, CPA 2019"
    }
    llm_context.primary_provisions = ["Section 2", "Section 10"]
    llm_context.related_provisions = []
    llm_context.definitions = ["consumer"]
    llm_context.hierarchical_context = ["Chapter I"]
    
    return query_intent, graph_context, llm_context

def demonstrate_confidence_scoring():
    """Demonstrate confidence scoring with various response scenarios."""
    
    print("=" * 80)
    print("CONFIDENCE SCORING SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Initialize scorer
    scorer = ConfidenceScorer()
    
    # Create mock data
    query_intent, graph_context, llm_context = create_mock_data()
    
    # Test scenarios
    scenarios = [
        {
            "name": "HIGH QUALITY RESPONSE",
            "response": """
Based on Section 2 of the Consumer Protection Act, 2019, a consumer is defined as a person who buys goods or services for consideration [Citation: Section 2, CPA 2019].

Unfair trade practices are prohibited under the Act and include misleading advertisements, defective products, and false claims about goods or services. According to Section 10, consumers have the right to file complaints with consumer forums when they encounter such practices [Citation: Section 10, CPA 2019].

The complaint process involves the following steps:
1. Filing a complaint with the appropriate consumer forum
2. Providing evidence of the unfair trade practice
3. Seeking remedies such as compensation or replacement

Therefore, if you encounter unfair trade practices, you should gather evidence and file a complaint with the consumer forum in your jurisdiction. The law provides strong protection for consumer rights [Citation: Consumer Rights, Section 2, CPA 2019].

Disclaimer: This information is provided for educational purposes only and does not constitute legal advice. Please consult a qualified lawyer for advice specific to your situation.
            """,
            "audience": "citizen"
        },
        {
            "name": "MEDIUM QUALITY RESPONSE",
            "response": """
Section 2 defines consumer and unfair trade practices [Citation: Section 2, CPA 2019]. 

Consumers can file complaints under Section 10 when they face unfair trade practices. The process involves filing with consumer forums.

This is for information only and not legal advice.
            """,
            "audience": "citizen"
        },
        {
            "name": "LOW QUALITY RESPONSE",
            "response": """
Consumers have rights. They can complain about unfair practices. The law protects them.
            """,
            "audience": "citizen"
        },
        {
            "name": "LAWYER-FOCUSED RESPONSE",
            "response": """
Pursuant to Section 2 of the Consumer Protection Act, 2019, the definition of "consumer" encompasses any person who purchases goods or services for consideration [Citation: Section 2, CPA 2019]. The Act further defines "unfair trade practice" to include various deceptive commercial practices [Citation: Section 2, CPA 2019].

Under Section 10, the statutory framework provides for complaint mechanisms through consumer forums at district, state, and national levels [Citation: Section 10, CPA 2019]. The jurisdiction is determined by the value of goods/services and geographical considerations.

Legal remedies available include:
- Compensation for damages
- Replacement or repair of defective goods
- Refund of consideration paid
- Punitive damages in cases of deliberate negligence

Cross-reference: See also provisions under Section 15 for penalty structures and Section 20 for appeal procedures.

The burden of proof lies with the complainant to establish the unfair trade practice, though the Act provides for certain presumptions in favor of consumers in specific circumstances.
            """,
            "audience": "lawyer"
        },
        {
            "name": "NO CITATIONS RESPONSE",
            "response": """
Section 2 states that consumers are people who buy goods or services. Unfair trade practices include misleading advertisements and defective products.

Section 10 allows consumers to file complaints with consumer forums. The process involves submitting evidence and seeking remedies.

Consumers have strong legal protection under the Consumer Protection Act.
            """,
            "audience": "citizen"
        }
    ]
    
    # Test each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'-' * 60}")
        print(f"SCENARIO {i}: {scenario['name']}")
        print(f"{'-' * 60}")
        
        score = scorer.score_response(
            query_intent,
            graph_context,
            llm_context,
            scenario['response'],
            audience=scenario['audience']
        )
        
        print(f"Overall Confidence Score: {score.overall_score:.3f}")
        print(f"Confidence Level: {score.confidence_level.value.upper()}")
        print(f"Requires Human Review: {'YES' if score.requires_human_review else 'NO'}")
        print(f"Should Block Display: {'YES' if score.should_block_display() else 'NO'}")
        
        print(f"\nComponent Breakdown:")
        print(f"  Graph Coverage:        {score.components.graph_coverage:.3f}")
        print(f"  Citation Density:      {score.components.citation_density:.3f}")
        print(f"  Reasoning Chain:       {score.components.reasoning_chain_score:.3f}")
        print(f"  Response Quality:      {score.components.response_quality:.3f}")
        print(f"  Temporal Validity:     {score.components.temporal_validity:.3f}")
        print(f"  Audience Appropriate:  {score.components.audience_appropriateness:.3f}")
        
        if score.review_reasons:
            print(f"\nReview Reasons:")
            for reason in score.review_reasons:
                print(f"  - {reason}")
        
        print(f"\nUser Display Message:")
        print(f"  {score.get_display_message()}")
        
        print(f"\nMetadata:")
        print(f"  Citation Count: {score.metadata['citation_count']}")
        print(f"  Response Length: {score.metadata['response_length']} characters")
        print(f"  Graph Nodes: {score.metadata['graph_nodes_count']}")

def demonstrate_audience_differences():
    """Demonstrate how scoring differs by audience."""
    
    print(f"\n{'=' * 80}")
    print("AUDIENCE-SPECIFIC SCORING DEMONSTRATION")
    print(f"{'=' * 80}")
    
    scorer = ConfidenceScorer()
    query_intent, graph_context, llm_context = create_mock_data()
    
    # Same response tested for different audiences
    response = """
Based on Section 2 of the Consumer Protection Act, 2019, consumers have rights [Citation: Section 2, CPA 2019]. 
The Act provides remedies through consumer forums [Citation: Section 10, CPA 2019].
    """
    
    audiences = ['citizen', 'lawyer', 'judge']
    
    print(f"\nTesting same response for different audiences:")
    print(f"Response: {response.strip()}")
    
    for audience in audiences:
        print(f"\n{'-' * 40}")
        print(f"AUDIENCE: {audience.upper()}")
        print(f"{'-' * 40}")
        
        score = scorer.score_response(
            query_intent, graph_context, llm_context, response, audience=audience
        )
        
        print(f"Confidence Score: {score.overall_score:.3f}")
        print(f"Confidence Level: {score.confidence_level.value}")
        print(f"Requires Review: {'YES' if score.requires_human_review else 'NO'}")
        
        # Show citation requirements for this audience
        requirements = scorer.citation_requirements[audience]
        print(f"Citation Requirements:")
        print(f"  Min Citations: {requirements['min_citations']}")
        print(f"  Max Claims per Citation: {requirements['claims_per_citation']}")
        
        # Show weights used
        weights = scorer.audience_weights[audience]
        print(f"Component Weights:")
        for component, weight in weights.items():
            if weight > 0:
                print(f"  {component}: {weight:.2f}")

def demonstrate_threshold_calibration():
    """Demonstrate threshold calibration functionality."""
    
    print(f"\n{'=' * 80}")
    print("THRESHOLD CALIBRATION DEMONSTRATION")
    print(f"{'=' * 80}")
    
    scorer = ConfidenceScorer()
    
    print("Current Thresholds:")
    for level, threshold in scorer.confidence_thresholds.items():
        print(f"  {level.value.upper()}: {threshold}")
    
    print(f"\nTesting threshold updates...")
    
    # Update thresholds
    new_thresholds = {
        ConfidenceLevel.HIGH: 0.75,  # Lower threshold for human review
        ConfidenceLevel.MEDIUM: 0.65
    }
    
    scorer.update_thresholds(new_thresholds)
    
    print("Updated Thresholds:")
    for level, threshold in scorer.confidence_thresholds.items():
        print(f"  {level.value.upper()}: {threshold}")
    
    # Get calibration stats
    stats = scorer.get_calibration_stats()
    print(f"\nCalibration Statistics Available:")
    for key in stats.keys():
        print(f"  - {key}")

def demonstrate_integration_with_validator():
    """Demonstrate integration with the existing validation system."""
    
    print(f"\n{'=' * 80}")
    print("INTEGRATION WITH VALIDATION SYSTEM")
    print(f"{'=' * 80}")
    
    # Initialize validator (which now includes confidence scorer)
    validator = ResponseValidator()
    
    query_intent, graph_context, llm_context = create_mock_data()
    
    # Create citation constraints
    citation_constraints = CitationConstraints(
        format_type=CitationFormat.STANDARD,
        require_all_claims=True,
        allow_inference=False
    )
    
    response = """
    Based on Section 2 of the Consumer Protection Act, 2019, consumers are protected [Citation: Section 2, CPA 2019].
    The Act provides various remedies for unfair trade practices [Citation: Section 10, CPA 2019].
    
    This information is for educational purposes only and does not constitute legal advice.
    """
    
    print("Testing integrated validation with confidence scoring...")
    
    # Validate response (now includes confidence scoring)
    validation_result = validator.validate_response(
        response=response,
        context=llm_context,
        graph_context=graph_context,
        citation_constraints=citation_constraints,
        query_intent=query_intent,
        audience="citizen"
    )
    
    print(f"\nValidation Results:")
    print(f"  Is Valid: {validation_result.is_valid}")
    print(f"  Confidence Score: {validation_result.confidence_score:.3f}")
    print(f"  Requires Review: {validation_result.requires_human_review}")
    print(f"  Citation Count: {validation_result.citation_count}")
    print(f"  Issues Found: {len(validation_result.issues)}")
    
    if validation_result.issues:
        print(f"\n  Issues:")
        for issue in validation_result.issues:
            print(f"    - {issue.severity.value.upper()}: {issue.message}")

if __name__ == "__main__":
    demonstrate_confidence_scoring()
    demonstrate_audience_differences()
    demonstrate_threshold_calibration()
    demonstrate_integration_with_validator()
    
    print(f"\n{'=' * 80}")
    print("CONFIDENCE SCORING DEMONSTRATION COMPLETED")
    print(f"{'=' * 80}")
    print("\nKey Features Demonstrated:")
    print("✓ Multi-factor confidence scoring (graph coverage, citations, reasoning, quality)")
    print("✓ Audience-specific scoring weights and requirements")
    print("✓ Empirically calibrated thresholds (0.8 for human review)")
    print("✓ Human review flagging based on confidence levels")
    print("✓ Integration with existing validation system")
    print("✓ Threshold calibration and updates")
    print("✓ Detailed component breakdown and metadata")