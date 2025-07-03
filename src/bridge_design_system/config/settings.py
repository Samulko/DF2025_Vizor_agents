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
    gemini_api_key: Optional[str] = None
    hf_token: Optional[str] = None

    # Agent Model Configuration - defaults can be overridden by .env
    triage_agent_provider: str = "gemini"
    triage_agent_model: str = "gemini-2.5-flash-preview-05-20"
    geometry_agent_provider: str = "gemini"
    geometry_agent_model: str = "gemini-2.5-flash-preview-05-20"
    material_agent_provider: str = "gemini"
    material_agent_model: str = "gemini-2.5-flash-preview-05-20"
    structural_agent_provider: str = "gemini"
    structural_agent_model: str = "gemini-2.5-flash-preview-05-20"
    syslogic_agent_provider: str = "gemini"
    syslogic_agent_model: str = "gemini-2.5-flash-preview-05-20"
    rational_agent_provider: str = "gemini"
    rational_agent_model: str = "gemini-2.5-flash-preview-05-20"
    category_agent_provider: str = "gemini"
    category_agent_model: str = "gemini-2.5-flash-preview-05-20"

    # MCP Configuration
    mcp_transport_mode: str = "http"  # "http" or "stdio"
    mcp_http_url: str = "http://127.0.0.1:8081/mcp"  # Use 127.0.0.1 for WSL-to-Windows communication
    mcp_http_timeout: int = 30
    mcp_stdio_command: str = "uv"
    mcp_stdio_args: str = "run,python,-m,grasshopper_mcp.bridge"

    # Paths
    grasshopper_mcp_path: str = ""
    material_db_path: str = "materials.db"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/bridge_design_system.log"

    # Agent Configuration
    max_agent_steps: int = 20
    max_context_tokens: int = 8000

    # MCP Server Configuration
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8001

    # Development Settings
    debug: bool = False
    enable_profiling: bool = False

    # OpenTelemetry Configuration
    otel_backend: str = "hybrid"  # none, console, langfuse, phoenix, hybrid
    otel_enabled: bool = True
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"  # EU region default
    phoenix_host: str = "http://localhost"
    phoenix_port: int = 6006
    
    # Monitoring Configuration
    disable_custom_monitoring: bool = False
    monitoring_host: str = "0.0.0.0"
    monitoring_port: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider.

        Args:
            provider: Provider name (openai, anthropic, deepseek, together, gemini, hf)

        Returns:
            API key if available, None otherwise
        """
        key_mapping = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "deepseek": self.deepseek_api_key,
            "together": self.together_api_key,
            "gemini": self.gemini_api_key,
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

    def get_mcp_server_params(self) -> dict:
        """Get MCP server parameters based on transport mode.

        Returns:
            Dictionary with server parameters for MCPAdapt
        """
        if self.mcp_transport_mode.lower() == "http":
            return {"url": self.mcp_http_url, "transport": "streamable-http"}
        else:
            # STDIO mode
            from mcp import StdioServerParameters

            args = self.mcp_stdio_args.split(",")
            return StdioServerParameters(command=self.mcp_stdio_command, args=args, env=None)

    def get_mcp_connection_fallback_params(self) -> dict:
        """Get fallback MCP parameters when HTTP fails.

        Returns:
            STDIO parameters for fallback
        """
        from mcp import StdioServerParameters

        args = self.mcp_stdio_args.split(",")
        return StdioServerParameters(command=self.mcp_stdio_command, args=args, env=None)

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
