"""Model provider configuration for multi-LLM support."""
import logging
from typing import Any, Optional

from smolagents import InferenceClientModel, LiteLLMModel, OpenAIServerModel

from ..config.settings import settings

logger = logging.getLogger(__name__)


class ModelProvider:
    """Manages LLM model initialization based on environment configuration."""
    
    @staticmethod
    def get_model(agent_name: str) -> Any:
        """Get configured model for specific agent.
        
        Args:
            agent_name: Name of the agent (triage, geometry, material, structural)
            
        Returns:
            Configured model instance
            
        Raises:
            ValueError: If provider is unknown or API key is missing
        """
        # Get provider and model from settings
        provider = getattr(settings, f"{agent_name.lower()}_agent_provider", "openai")
        model_name = getattr(settings, f"{agent_name.lower()}_agent_model", "gpt-4")
        
        logger.info(f"Initializing {agent_name} agent with {provider}/{model_name}")
        
        # Get API key
        api_key = settings.get_api_key(provider)
        if not api_key and provider != "hf":  # HF can work without token for some models
            raise ValueError(
                f"Missing API key for {provider}. "
                f"Please set {provider.upper()}_API_KEY in your .env file"
            )
        
        # Initialize model based on provider
        if provider == "openai":
            return LiteLLMModel(
                model_id=model_name,
                api_key=api_key
            )
        
        elif provider == "anthropic":
            # LiteLLM requires anthropic/ prefix for Claude models
            return LiteLLMModel(
                model_id=f"anthropic/{model_name}",
                api_key=api_key
            )
        
        elif provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API via OpenAIServerModel
            return OpenAIServerModel(
                model_id=model_name,
                api_base="https://api.deepseek.com/v1",
                api_key=api_key
            )
        
        elif provider == "gemini":
            # Google Gemini via OpenAI-compatible API
            return OpenAIServerModel(
                model_id=model_name,
                api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=api_key
            )
        
        elif provider == "together":
            # Together AI via LiteLLM
            return LiteLLMModel(
                model_id=f"together/{model_name}",
                api_key=api_key
            )
        
        elif provider == "hf":
            # HuggingFace Inference API
            return InferenceClientModel(
                model_id=model_name,
                token=api_key
            )
        
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: openai, anthropic, deepseek, gemini, together, hf"
            )
    
    @staticmethod
    def validate_all_models() -> dict[str, bool]:
        """Validate that all configured models can be initialized.
        
        Returns:
            Dictionary mapping agent names to validation status
        """
        agents = ["triage", "geometry", "material", "structural"]
        results = {}
        
        for agent in agents:
            try:
                ModelProvider.get_model(agent)
                results[agent] = True
                logger.info(f"{agent} agent model validated successfully")
            except Exception as e:
                results[agent] = False
                logger.error(f"{agent} agent model validation failed: {e}")
        
        return results
    
    @staticmethod
    def get_model_info(agent_name: str) -> dict[str, str]:
        """Get model configuration info for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with provider and model information
        """
        provider = getattr(settings, f"{agent_name.lower()}_agent_provider", "unknown")
        model = getattr(settings, f"{agent_name.lower()}_agent_model", "unknown")
        
        return {
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "has_api_key": bool(settings.get_api_key(provider))
        }