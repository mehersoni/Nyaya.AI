"""
LLM Manager with Multi-Provider Fallback Strategy

This module implements the LLMManager class that coordinates multiple LLM providers
with intelligent fallback strategies, load balancing, and cost optimization.

Key features:
- Multi-provider support with automatic fallback
- Load balancing and cost optimization
- Request routing based on query complexity
- Performance monitoring and provider health checks
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random

from .providers import LLMProvider, LLMResponse, LLMError, LLMProviderType
from .prompt_templates import PromptTemplateManager, CitationConstraints, CitationFormat
from query_engine.context_builder import LLMContext
from query_engine.query_parser import IntentType


logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback strategies for provider failures"""
    SEQUENTIAL = "sequential"  # Try providers in order
    RANDOM = "random"         # Random selection from available providers
    COST_OPTIMIZED = "cost_optimized"  # Prefer lower-cost providers
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Prefer faster providers


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider"""
    provider: LLMProvider
    priority: int = 1  # Higher number = higher priority
    max_requests_per_minute: int = 60
    cost_per_token: float = 0.0
    enabled: bool = True
    health_check_interval: int = 300  # seconds
    
    def __post_init__(self):
        self.request_count = 0
        self.last_request_time = 0
        self.last_health_check = 0
        self.is_healthy = True
        self.avg_response_time = 0.0
        self.total_cost = 0.0


class LLMManager:
    """Manages multiple LLM providers with fallback strategies."""
    
    def __init__(self, fallback_strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL):
        """
        Initialize LLM manager.
        
        Args:
            fallback_strategy: Strategy for provider fallback
        """
        self.providers: Dict[str, ProviderConfig] = {}
        self.fallback_strategy = fallback_strategy
        self.prompt_manager = PromptTemplateManager()
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_cost = 0.0
        
        logger.info(f"Initialized LLM manager with {fallback_strategy.value} fallback strategy")
    
    def add_provider(self, name: str, provider: LLMProvider, 
                    priority: int = 1, max_requests_per_minute: int = 60,
                    cost_per_token: float = 0.0) -> None:
        """
        Add an LLM provider to the manager.
        
        Args:
            name: Unique name for the provider
            provider: LLMProvider instance
            priority: Provider priority (higher = preferred)
            max_requests_per_minute: Rate limit for this provider
            cost_per_token: Estimated cost per token
        """
        config = ProviderConfig(
            provider=provider,
            priority=priority,
            max_requests_per_minute=max_requests_per_minute,
            cost_per_token=cost_per_token
        )
        
        self.providers[name] = config
        logger.info(f"Added provider '{name}' with priority {priority}")
    
    def remove_provider(self, name: str) -> None:
        """Remove a provider from the manager."""
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Removed provider '{name}'")
    
    def generate_response(self, query: str, context: LLMContext,
                         audience: str = "citizen", intent_type: IntentType = IntentType.SCENARIO_ANALYSIS,
                         citation_format: CitationFormat = CitationFormat.STANDARD,
                         max_retries: int = 3) -> LLMResponse:
        """
        Generate response using the best available provider with fallback.
        
        Args:
            query: User query
            context: Structured context from knowledge graph
            audience: Target audience (citizen, lawyer, judge)
            intent_type: Type of query intent
            citation_format: Citation format to use
            max_retries: Maximum number of provider attempts
            
        Returns:
            LLMResponse from successful provider
            
        Raises:
            LLMError: If all providers fail
        """
        self.total_requests += 1
        start_time = time.time()
        
        # Build citation constraints
        citation_constraints = CitationConstraints(
            format_type=citation_format,
            require_all_claims=True,
            allow_inference=False
        )
        
        # Get ordered list of providers to try
        provider_order = self._get_provider_order(query, context, audience)
        
        last_error = None
        attempts = 0
        
        for provider_name in provider_order:
            if attempts >= max_retries:
                break
                
            provider_config = self.providers[provider_name]
            
            # Check if provider is available and healthy
            if not self._is_provider_available(provider_name):
                logger.warning(f"Provider '{provider_name}' not available, skipping")
                continue
            
            # Check rate limits
            if not self._check_rate_limit(provider_name):
                logger.warning(f"Provider '{provider_name}' rate limited, skipping")
                continue
            
            try:
                # Build prompts
                system_prompt = self.prompt_manager.build_system_prompt(
                    audience=audience,
                    intent_type=intent_type,
                    citation_constraints=citation_constraints
                )
                
                user_prompt = self.prompt_manager.build_user_prompt(
                    query=query,
                    context=context,
                    intent_type=intent_type,
                    audience=audience
                )
                
                # Prepare constraints for provider
                constraints = {
                    'audience': audience,
                    'citation_format': citation_format.value,
                    'intent_type': intent_type.value,
                    'system_prompt': system_prompt
                }
                
                # Generate response
                logger.info(f"Attempting response generation with provider '{provider_name}'")
                response = provider_config.provider.generate_response(
                    prompt=user_prompt,
                    context=context,
                    constraints=constraints
                )
                
                # Update provider statistics
                self._update_provider_stats(provider_name, response, start_time)
                
                # Update manager statistics
                self.successful_requests += 1
                self.total_cost += response.get_cost_estimate()
                
                logger.info(f"Successfully generated response with provider '{provider_name}' "
                           f"in {response.response_time:.2f}s")
                
                return response
                
            except LLMError as e:
                attempts += 1
                last_error = e
                
                # Update provider health based on error type
                self._handle_provider_error(provider_name, e)
                
                logger.warning(f"Provider '{provider_name}' failed: {e.error_type} - {e}")
                
                # For rate limits, mark provider as temporarily unavailable
                if e.error_type == "rate_limit":
                    self._mark_provider_rate_limited(provider_name)
                
                continue
            
            except Exception as e:
                attempts += 1
                last_error = LLMError(f"Unexpected error: {e}", provider_name, "unknown")
                
                logger.error(f"Unexpected error with provider '{provider_name}': {e}")
                continue
        
        # All providers failed
        self.failed_requests += 1
        
        if last_error:
            logger.error(f"All providers failed. Last error: {last_error}")
            raise last_error
        else:
            error_msg = "No available providers for request"
            logger.error(error_msg)
            raise LLMError(error_msg, "manager", "no_providers")
    
    def _get_provider_order(self, query: str, context: LLMContext, audience: str) -> List[str]:
        """
        Get ordered list of providers to try based on fallback strategy.
        
        Args:
            query: User query
            context: LLM context
            audience: Target audience
            
        Returns:
            List of provider names in order of preference
        """
        available_providers = [
            name for name, config in self.providers.items()
            if config.enabled and config.is_healthy
        ]
        
        if not available_providers:
            return []
        
        if self.fallback_strategy == FallbackStrategy.SEQUENTIAL:
            # Sort by priority (descending)
            return sorted(available_providers, 
                         key=lambda name: self.providers[name].priority, 
                         reverse=True)
        
        elif self.fallback_strategy == FallbackStrategy.RANDOM:
            # Random order
            random.shuffle(available_providers)
            return available_providers
        
        elif self.fallback_strategy == FallbackStrategy.COST_OPTIMIZED:
            # Sort by cost per token (ascending)
            return sorted(available_providers,
                         key=lambda name: self.providers[name].cost_per_token)
        
        elif self.fallback_strategy == FallbackStrategy.PERFORMANCE_OPTIMIZED:
            # Sort by average response time (ascending)
            return sorted(available_providers,
                         key=lambda name: self.providers[name].avg_response_time)
        
        else:
            # Default to priority-based
            return sorted(available_providers,
                         key=lambda name: self.providers[name].priority,
                         reverse=True)
    
    def _is_provider_available(self, provider_name: str) -> bool:
        """Check if provider is available and healthy."""
        if provider_name not in self.providers:
            return False
        
        config = self.providers[provider_name]
        
        if not config.enabled:
            return False
        
        # Perform health check if needed
        current_time = time.time()
        if current_time - config.last_health_check > config.health_check_interval:
            config.is_healthy = config.provider.is_available()
            config.last_health_check = current_time
            
            if config.is_healthy:
                logger.debug(f"Provider '{provider_name}' health check passed")
            else:
                logger.warning(f"Provider '{provider_name}' health check failed")
        
        return config.is_healthy
    
    def _check_rate_limit(self, provider_name: str) -> bool:
        """Check if provider is within rate limits."""
        config = self.providers[provider_name]
        current_time = time.time()
        
        # Simple rate limiting: check requests in last minute
        if current_time - config.last_request_time < 60:
            if config.request_count >= config.max_requests_per_minute:
                return False
        else:
            # Reset counter for new minute
            config.request_count = 0
        
        return True
    
    def _update_provider_stats(self, provider_name: str, response: LLMResponse, start_time: float):
        """Update provider statistics after successful request."""
        config = self.providers[provider_name]
        current_time = time.time()
        
        # Update request tracking
        config.request_count += 1
        config.last_request_time = current_time
        
        # Update average response time
        total_time = current_time - start_time
        if config.avg_response_time == 0:
            config.avg_response_time = total_time
        else:
            # Exponential moving average
            config.avg_response_time = 0.9 * config.avg_response_time + 0.1 * total_time
        
        # Update cost tracking
        config.total_cost += response.get_cost_estimate()
    
    def _handle_provider_error(self, provider_name: str, error: LLMError):
        """Handle provider error and update health status."""
        config = self.providers[provider_name]
        
        # Mark as unhealthy for certain error types
        if error.error_type in ["api_error", "timeout", "unknown"]:
            config.is_healthy = False
            logger.warning(f"Marked provider '{provider_name}' as unhealthy due to {error.error_type}")
    
    def _mark_provider_rate_limited(self, provider_name: str):
        """Mark provider as temporarily rate limited."""
        config = self.providers[provider_name]
        config.last_request_time = time.time()
        config.request_count = config.max_requests_per_minute
        logger.info(f"Provider '{provider_name}' marked as rate limited")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        stats = {
            'manager_stats': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': self.successful_requests / max(1, self.total_requests),
                'total_cost': self.total_cost,
                'fallback_strategy': self.fallback_strategy.value
            },
            'providers': {}
        }
        
        for name, config in self.providers.items():
            provider_stats = config.provider.get_stats()
            stats['providers'][name] = {
                **provider_stats,
                'priority': config.priority,
                'enabled': config.enabled,
                'is_healthy': config.is_healthy,
                'avg_response_time': config.avg_response_time,
                'total_cost': config.total_cost,
                'rate_limit': config.max_requests_per_minute
            }
        
        return stats
    
    def set_provider_enabled(self, provider_name: str, enabled: bool):
        """Enable or disable a provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = enabled
            logger.info(f"Provider '{provider_name}' {'enabled' if enabled else 'disabled'}")
    
    def set_fallback_strategy(self, strategy: FallbackStrategy):
        """Change the fallback strategy."""
        self.fallback_strategy = strategy
        logger.info(f"Changed fallback strategy to {strategy.value}")
    
    def health_check_all_providers(self) -> Dict[str, bool]:
        """Perform health check on all providers."""
        results = {}
        
        for name, config in self.providers.items():
            try:
                config.is_healthy = config.provider.is_available()
                config.last_health_check = time.time()
                results[name] = config.is_healthy
                
                logger.info(f"Provider '{name}' health check: {'PASS' if config.is_healthy else 'FAIL'}")
                
            except Exception as e:
                config.is_healthy = False
                results[name] = False
                logger.error(f"Provider '{name}' health check failed: {e}")
        
        return results
    
    def get_best_provider_for_query(self, query_complexity: str, audience: str) -> Optional[str]:
        """
        Get the best provider for a specific query type.
        
        Args:
            query_complexity: 'simple', 'moderate', or 'complex'
            audience: Target audience
            
        Returns:
            Name of best provider or None if none available
        """
        available_providers = [
            name for name, config in self.providers.items()
            if config.enabled and config.is_healthy and self._check_rate_limit(name)
        ]
        
        if not available_providers:
            return None
        
        # For complex queries or judge audience, prefer higher-capability models
        if query_complexity == 'complex' or audience == 'judge':
            # Prefer providers with higher priority (typically more capable models)
            return max(available_providers, 
                      key=lambda name: self.providers[name].priority)
        
        # For simple queries, prefer cost-optimized providers
        elif query_complexity == 'simple':
            return min(available_providers,
                      key=lambda name: self.providers[name].cost_per_token)
        
        # For moderate queries, balance cost and capability
        else:
            # Use performance-optimized selection
            return min(available_providers,
                      key=lambda name: self.providers[name].avg_response_time)
    
    def estimate_cost(self, query: str, context: LLMContext, provider_name: Optional[str] = None) -> float:
        """
        Estimate cost for processing a query.
        
        Args:
            query: User query
            context: LLM context
            provider_name: Specific provider to estimate for (optional)
            
        Returns:
            Estimated cost in USD
        """
        # Rough token estimation (actual tokenization would be more accurate)
        estimated_tokens = len(query.split()) + len(context.formatted_text.split())
        estimated_tokens = int(estimated_tokens * 1.3)  # Account for tokenization overhead
        
        if provider_name and provider_name in self.providers:
            cost_per_token = self.providers[provider_name].cost_per_token
            return estimated_tokens * cost_per_token
        
        # Return average cost across all providers
        if self.providers:
            avg_cost_per_token = sum(config.cost_per_token for config in self.providers.values()) / len(self.providers)
            return estimated_tokens * avg_cost_per_token
        
        return 0.0