"""Settings management for the bridge design system using Pydantic."""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    
    # Agent Model Configuration
    triage_agent_provider: str = "deepseek"
    triage_agent_model: str = "deepseek-chat"
    geometry_agent_provider: str = "anthropic"
    geometry_agent_model: str = "claude-3-5-sonnet-latest"
    material_agent_provider: str = "anthropic"
    material_agent_model: str = "claude-3-5-sonnet-latest"
    structural_agent_provider: str = "anthropic"
    structural_agent_model: str = "claude-3-5-sonnet-latest"
    
    # Paths
    grasshopper_mcp_path: str = ""
    material_db_path: str = "materials.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/bridge_design_system.log"
    
    # Agent Configuration
    max_agent_steps: int = 20
    max_context_tokens: int = 8000
    
    # Development Settings
    debug: bool = False
    enable_profiling: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider.
        
        Args:
            provider: Provider name (openai, anthropic, deepseek, together, hf)
            
        Returns:
            API key if available, None otherwise
        """
        key_mapping = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "deepseek": self.deepseek_api_key,
            "together": self.together_api_key,
            "hf": self.hf_token,
        }
        return key_mapping.get(provider.lower())
    
    def validate_required_keys(self, required_providers: list[str]) -> list[str]:
        """Validate that required API keys are present.
        
        Args:
            required_providers: List of provider names that need API keys
            
        Returns:
            List of missing providers
        """
        missing = []
        for provider in required_providers:
            if not self.get_api_key(provider):
                missing.append(provider)
        return missing
    
    @property
    def log_file_path(self) -> Path:
        """Get log file path as Path object."""
        return Path(self.log_file)
    
    @property
    def material_db_file_path(self) -> Path:
        """Get material database path as Path object."""
        return Path(self.material_db_path)


# Global settings instance
settings = Settings()