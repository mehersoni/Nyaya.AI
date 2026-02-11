# LLM Integration Layer

The LLM Integration Layer provides a robust, multi-provider interface for generating legal responses with proper citation constraints and validation. This layer is designed specifically for the Nyayamrit judicial assistant system.

## 🏗️ Architecture

The LLM integration layer consists of four main components:

### 1. **Providers** (`providers.py`)
- **LLMProvider**: Abstract base class for all LLM providers
- **OpenAIProvider**: OpenAI GPT-4 integration with structured prompts
- **AnthropicProvider**: Anthropic Claude integration
- **LocalLLMProvider**: Placeholder for future local model support

### 2. **Prompt Templates** (`prompt_templates.py`)
- **PromptTemplateManager**: Manages structured prompts for different scenarios
- **CitationConstraints**: Defines citation formatting and validation rules
- Audience-specific templates (citizen, lawyer, judge)
- Intent-specific templates (definition lookup, section retrieval, etc.)

### 3. **LLM Manager** (`llm_manager.py`)
- **LLMManager**: Coordinates multiple providers with intelligent fallback
- **FallbackStrategy**: Different strategies for provider selection
- Load balancing, cost optimization, and performance monitoring
- Rate limiting and health checks

### 4. **Validation** (`validation.py`)
- **ResponseValidator**: Validates LLM responses against knowledge graph
- **CitationValidator**: Ensures proper citation format and existence
- **ContentValidator**: Detects hallucinations and prohibited language

## 🚀 Quick Start

### Installation

```bash
# Install core dependencies
pip install -r llm_integration/requirements.txt

# Install LLM provider libraries (optional)
pip install openai anthropic
```

### Basic Usage

```python
from llm_integration import LLMManager, OpenAIProvider, CitationFormat
from query_engine.graphrag_engine import GraphRAGEngine

# Initialize GraphRAG engine
graphrag = GraphRAGEngine("knowledge_graph")

# Setup LLM manager with providers
llm_manager = LLMManager()

# Add OpenAI provider (requires API key)
openai_provider = OpenAIProvider(api_key="your-openai-key")
llm_manager.add_provider("openai", openai_provider, priority=1)

# Process a query
graphrag_response = graphrag.process_query("What is a consumer?", audience="citizen")

# Generate LLM response
llm_response = llm_manager.generate_response(
    query="What is a consumer?",
    context=graphrag_response.llm_context,
    audience="citizen",
    citation_format=CitationFormat.STANDARD
)

print(llm_response.content)
```

### Complete Integration Example

```python
from llm_integration.example_usage import NyayamritLLMService

# Initialize complete service
service = NyayamritLLMService()

# Process legal query
result = service.process_legal_query(
    query="What are my rights as a consumer?",
    audience="citizen",
    citation_format="standard"
)

if result["success"]:
    print("Response:", result["response"])
    print("Valid:", result["validation"]["is_valid"])
    print("Confidence:", result["validation"]["confidence_score"])
else:
    print("Error:", result["error"])
```

## 🔧 Configuration

### Environment Variables

Set these environment variables to enable LLM providers:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Provider Configuration

```python
# Configure OpenAI provider
openai_provider = OpenAIProvider(
    api_key="your-key",
    model="gpt-4",
    temperature=0.1,        # Low temperature for legal accuracy
    max_tokens=2000,
    timeout=30
)

# Configure Anthropic provider
anthropic_provider = AnthropicProvider(
    api_key="your-key",
    model="claude-3-sonnet-20240229",
    temperature=0.1,
    max_tokens=2000
)

# Add to manager with priorities and cost settings
llm_manager.add_provider("openai", openai_provider, 
                        priority=2, cost_per_token=0.00003)
llm_manager.add_provider("anthropic", anthropic_provider, 
                        priority=1, cost_per_token=0.000015)
```

## 📋 Features

### Multi-Provider Fallback

The system supports intelligent fallback between multiple LLM providers:

```python
# Different fallback strategies
manager = LLMManager(FallbackStrategy.PERFORMANCE_OPTIMIZED)  # Fastest first
manager = LLMManager(FallbackStrategy.COST_OPTIMIZED)        # Cheapest first
manager = LLMManager(FallbackStrategy.SEQUENTIAL)            # Priority order
```

### Citation Constraints

Enforce strict citation requirements:

```python
from llm_integration import CitationConstraints, CitationFormat

constraints = CitationConstraints(
    format_type=CitationFormat.STANDARD,
    require_all_claims=True,      # Every legal claim must be cited
    allow_inference=False,        # No inferences beyond context
    max_unsupported_claims=0      # Zero tolerance for unsupported claims
)
```

### Audience-Specific Responses

Generate responses tailored to different audiences:

- **Citizens**: Simple language, practical guidance
- **Lawyers**: Technical details, cross-references
- **Judges**: Formal language, analytical framework

### Response Validation

Comprehensive validation ensures response quality:

```python
validator = ResponseValidator()
result = validator.validate_response(response, context, graph_context, constraints)

print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence_score}")
print(f"Issues: {len(result.issues)}")
```

## 🎯 Citation Formats

The system supports multiple citation formats:

### Standard Format
```
[Citation: Section 2]
[Citation: Definition of Consumer]
```

### Detailed Format
```
[Citation: Section 2, Clause 7 of Consumer Protection Act, 2019]
```

### Bluebook Format
```
Consumer Protection Act § 2 (India 2019)
```

### Indian Citation Manual Format
```
Section 2, Consumer Protection Act, 2019
```

## 🔍 Validation Rules

The validation layer enforces several critical rules:

### Citation Validation
- All citations must exist in the knowledge graph context
- Legal claims must have supporting citations
- Citation format must match specified requirements

### Content Validation
- No predictive language about case outcomes
- No fabricated section numbers or legal provisions
- Required disclaimers about non-binding nature
- Appropriate audience-level language

### Prohibited Language
The system blocks responses containing:
- "I predict", "I believe", "likely outcome"
- "Judge will rule", "court will find"
- Case outcome predictions

## 📊 Monitoring and Statistics

Track system performance and usage:

```python
# Get provider statistics
stats = llm_manager.get_provider_stats()
print(f"Success rate: {stats['manager_stats']['success_rate']:.2%}")
print(f"Total cost: ${stats['manager_stats']['total_cost']:.4f}")

# Health check all providers
health = llm_manager.health_check_all_providers()
print(f"Healthy providers: {sum(health.values())}/{len(health)}")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest llm_integration/test_llm_integration.py -v

# Run specific test categories
python -m pytest llm_integration/test_llm_integration.py::TestPromptTemplateManager -v
python -m pytest llm_integration/test_llm_integration.py::TestLLMManager -v
python -m pytest llm_integration/test_llm_integration.py::TestResponseValidator -v

# Run integration tests
python llm_integration/test_llm_integration.py
```

## 🔒 Security Considerations

### API Key Management
- Store API keys in environment variables, never in code
- Use different keys for development and production
- Implement key rotation policies

### Rate Limiting
- Built-in rate limiting prevents API abuse
- Configurable limits per provider
- Automatic backoff on rate limit errors

### Content Validation
- All responses validated against knowledge graph
- Prohibited language detection
- No case outcome predictions allowed

## 💰 Cost Management

### Cost Tracking
```python
# Estimate cost before processing
estimated_cost = llm_manager.estimate_cost(query, context, "openai")
print(f"Estimated cost: ${estimated_cost:.4f}")

# Track actual costs
response = llm_manager.generate_response(...)
actual_cost = response.get_cost_estimate()
print(f"Actual cost: ${actual_cost:.4f}")
```

### Cost Optimization
- Use cost-optimized fallback strategy
- Configure cheaper providers as fallbacks
- Monitor and alert on cost thresholds

## 🚨 Error Handling

The system provides robust error handling:

```python
from llm_integration import LLMError

try:
    response = llm_manager.generate_response(...)
except LLMError as e:
    print(f"Provider: {e.provider}")
    print(f"Error type: {e.error_type}")
    print(f"Message: {e}")
    
    # Handle specific error types
    if e.error_type == "rate_limit":
        # Wait and retry
        pass
    elif e.error_type == "api_error":
        # Try different provider
        pass
```

## 📈 Performance Optimization

### Caching
- Response caching for common queries
- Context caching to reduce processing time
- Provider health status caching

### Async Support
Future versions will support async processing for better performance.

## 🔮 Future Enhancements

### Planned Features
- Local LLM support (Llama, Mistral)
- Async/await support for better performance
- Advanced caching strategies
- Real-time cost monitoring dashboard
- A/B testing for prompt optimization

### Integration Roadmap
- Integration with Bhashini API for multilingual support
- Advanced reasoning chains for complex queries
- Precedent analysis for judge features (Phase 4)

## 📚 API Reference

### Core Classes

#### LLMProvider
Abstract base class for all LLM providers.

```python
class LLMProvider(ABC):
    def generate_response(self, prompt: str, context: LLMContext, 
                         constraints: Dict[str, Any]) -> LLMResponse
    def is_available(self) -> bool
    def get_stats(self) -> Dict[str, Any]
```

#### LLMManager
Manages multiple providers with fallback strategies.

```python
class LLMManager:
    def add_provider(self, name: str, provider: LLMProvider, ...)
    def generate_response(self, query: str, context: LLMContext, ...)
    def get_provider_stats(self) -> Dict[str, Any]
    def health_check_all_providers(self) -> Dict[str, bool]
```

#### ResponseValidator
Validates LLM responses for accuracy and compliance.

```python
class ResponseValidator:
    def validate_response(self, response: str, context: LLMContext, 
                         graph_context: GraphContext, 
                         citation_constraints: CitationConstraints) -> ValidationResult
```

## 🤝 Contributing

When contributing to the LLM integration layer:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all validation rules are maintained
5. Test with multiple LLM providers

## 📄 License

This LLM integration layer is part of the Nyayamrit project and follows the same licensing terms.