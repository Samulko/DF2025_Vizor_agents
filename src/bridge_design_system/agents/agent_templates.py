"""Agent configuration templates for production-ready deployments.

This module provides standardized configuration templates for different
agent types, including security settings, monitoring, and production
optimizations following smolagents best practices.
"""
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionEnvironment(Enum):
    """Supported execution environments for agent security."""
    LOCAL = "local"              # Local execution with import restrictions
    DOCKER = "docker"            # Docker containerization
    E2B = "e2b"                 # E2B remote sandboxing (production)


class SecurityLevel(Enum):
    """Security levels for different deployment scenarios."""
    DEVELOPMENT = "development"  # Minimal restrictions for development
    STAGING = "staging"         # Moderate restrictions for testing
    PRODUCTION = "production"   # Maximum security for production


@dataclass
class SecurityConfig:
    """Security configuration for agent execution."""
    execution_environment: ExecutionEnvironment
    security_level: SecurityLevel
    authorized_imports: List[str]
    executor_kwargs: Dict[str, Any]
    max_steps: int
    rate_limit_requests: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent initialization."""
        config = asdict(self)
        config["execution_environment"] = self.execution_environment.value
        config["security_level"] = self.security_level.value
        return config


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enable_logging: bool
    log_level: str
    stream_outputs: bool
    enable_metrics: bool
    enable_tracing: bool
    performance_monitoring: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring setup."""
        return asdict(self)


@dataclass
class AgentTemplate:
    """Complete agent configuration template."""
    agent_type: str
    security_config: SecurityConfig
    monitoring_config: MonitoringConfig
    model_temperature: Optional[float]
    max_context_tokens: int
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent factory."""
        return {
            "agent_type": self.agent_type,
            "security": self.security_config.to_dict(),
            "monitoring": self.monitoring_config.to_dict(),
            "model_temperature": self.model_temperature,
            "max_context_tokens": self.max_context_tokens,
            "description": self.description
        }


class AgentTemplates:
    """Factory for agent configuration templates."""
    
    @staticmethod
    def get_geometry_template(
        environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL,
        security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    ) -> AgentTemplate:
        """Get configuration template for geometry agents.
        
        Args:
            environment: Execution environment for security
            security_level: Security level for deployment
            
        Returns:
            AgentTemplate configured for geometry operations
        """
        # Geometry-specific imports (minimal since it uses MCP tools)
        base_imports = [
            "json", "datetime", "pathlib", "typing", "dataclasses", "enum",
            "re", "collections", "functools", "math"
        ]
        
        # Security configuration
        security_config = SecurityConfig(
            execution_environment=environment,
            security_level=security_level,
            authorized_imports=base_imports,
            executor_kwargs=AgentTemplates._get_executor_kwargs(environment),
            max_steps=10,  # Lower for MCP operations
            rate_limit_requests=60 if security_level == SecurityLevel.PRODUCTION else None
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enable_logging=True,
            log_level="INFO" if security_level != SecurityLevel.PRODUCTION else "WARNING",
            stream_outputs=security_level == SecurityLevel.DEVELOPMENT,
            enable_metrics=security_level == SecurityLevel.PRODUCTION,
            enable_tracing=security_level == SecurityLevel.PRODUCTION,
            performance_monitoring=True
        )
        
        return AgentTemplate(
            agent_type="geometry",
            security_config=security_config,
            monitoring_config=monitoring_config,
            model_temperature=0.1,  # Precise for geometry operations
            max_context_tokens=8000,
            description="Creates 3D geometry in Rhino Grasshopper via MCP integration"
        )
    
    @staticmethod
    def get_material_template(
        environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL,
        security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    ) -> AgentTemplate:
        """Get configuration template for material agents.
        
        Args:
            environment: Execution environment for security
            security_level: Security level for deployment
            
        Returns:
            AgentTemplate configured for material management
        """
        # Material management imports
        base_imports = [
            "json", "datetime", "pathlib", "typing", "dataclasses", "enum",
            "re", "collections", "functools", "math", "sqlite3", "csv"
        ]
        
        # Add data analysis libraries for production
        if security_level == SecurityLevel.PRODUCTION:
            base_imports.extend(["pandas", "numpy"])
        
        # Security configuration
        security_config = SecurityConfig(
            execution_environment=environment,
            security_level=security_level,
            authorized_imports=base_imports,
            executor_kwargs=AgentTemplates._get_executor_kwargs(environment),
            max_steps=15,  # More steps for optimization algorithms
            rate_limit_requests=100 if security_level == SecurityLevel.PRODUCTION else None
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enable_logging=True,
            log_level="INFO",
            stream_outputs=security_level == SecurityLevel.DEVELOPMENT,
            enable_metrics=True,  # Important for inventory tracking
            enable_tracing=security_level == SecurityLevel.PRODUCTION,
            performance_monitoring=True
        )
        
        return AgentTemplate(
            agent_type="material",
            security_config=security_config,
            monitoring_config=monitoring_config,
            model_temperature=0.3,  # Balance between creativity and precision
            max_context_tokens=10000,
            description="Manages construction material inventory and optimization"
        )
    
    @staticmethod
    def get_structural_template(
        environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL,
        security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    ) -> AgentTemplate:
        """Get configuration template for structural agents.
        
        Args:
            environment: Execution environment for security
            security_level: Security level for deployment
            
        Returns:
            AgentTemplate configured for structural analysis
        """
        # Structural analysis imports
        base_imports = [
            "json", "datetime", "pathlib", "typing", "dataclasses", "enum",
            "re", "collections", "functools", "math", "numpy", "scipy"
        ]
        
        # Add visualization for development
        if security_level == SecurityLevel.DEVELOPMENT:
            base_imports.extend(["matplotlib", "plotly"])
        
        # Security configuration
        security_config = SecurityConfig(
            execution_environment=environment,
            security_level=security_level,
            authorized_imports=base_imports,
            executor_kwargs=AgentTemplates._get_executor_kwargs(environment),
            max_steps=20,  # More steps for complex calculations
            rate_limit_requests=50 if security_level == SecurityLevel.PRODUCTION else None
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enable_logging=True,
            log_level="INFO",
            stream_outputs=security_level == SecurityLevel.DEVELOPMENT,
            enable_metrics=True,  # Critical for safety calculations
            enable_tracing=True,   # Always trace structural calculations
            performance_monitoring=True
        )
        
        return AgentTemplate(
            agent_type="structural",
            security_config=security_config,
            monitoring_config=monitoring_config,
            model_temperature=0.2,  # Low temperature for safety calculations
            max_context_tokens=12000,  # More context for complex analysis
            description="Performs structural analysis and safety calculations"
        )
    
    @staticmethod
    def get_triage_template(
        environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL,
        security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    ) -> AgentTemplate:
        """Get configuration template for triage/coordination agents.
        
        Args:
            environment: Execution environment for security
            security_level: Security level for deployment
            
        Returns:
            AgentTemplate configured for task coordination
        """
        # Coordination and async processing imports
        base_imports = [
            "json", "datetime", "pathlib", "typing", "dataclasses", "enum",
            "re", "collections", "functools", "math", "asyncio", "concurrent.futures"
        ]
        
        # Security configuration
        security_config = SecurityConfig(
            execution_environment=environment,
            security_level=security_level,
            authorized_imports=base_imports,
            executor_kwargs=AgentTemplates._get_executor_kwargs(environment),
            max_steps=25,  # More steps for coordination
            rate_limit_requests=200 if security_level == SecurityLevel.PRODUCTION else None
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enable_logging=True,
            log_level="INFO",
            stream_outputs=security_level == SecurityLevel.DEVELOPMENT,
            enable_metrics=True,  # Important for coordination metrics
            enable_tracing=True,   # Always trace delegation decisions
            performance_monitoring=True
        )
        
        return AgentTemplate(
            agent_type="triage",
            security_config=security_config,
            monitoring_config=monitoring_config,
            model_temperature=0.4,  # Higher for coordination reasoning
            max_context_tokens=15000,  # Large context for multi-agent coordination
            description="Coordinates tasks and delegates to specialized agents"
        )
    
    @staticmethod
    def get_production_template(agent_type: str) -> AgentTemplate:
        """Get production-ready template for any agent type.
        
        Args:
            agent_type: Type of agent (geometry, material, structural, triage)
            
        Returns:
            AgentTemplate configured for production deployment
        """
        template_map = {
            "geometry": AgentTemplates.get_geometry_template,
            "material": AgentTemplates.get_material_template,
            "structural": AgentTemplates.get_structural_template,
            "triage": AgentTemplates.get_triage_template
        }
        
        if agent_type not in template_map:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get production template with E2B sandboxing
        return template_map[agent_type](
            environment=ExecutionEnvironment.E2B,
            security_level=SecurityLevel.PRODUCTION
        )
    
    @staticmethod
    def get_development_template(agent_type: str) -> AgentTemplate:
        """Get development template for any agent type.
        
        Args:
            agent_type: Type of agent (geometry, material, structural, triage)
            
        Returns:
            AgentTemplate configured for development
        """
        template_map = {
            "geometry": AgentTemplates.get_geometry_template,
            "material": AgentTemplates.get_material_template,
            "structural": AgentTemplates.get_structural_template,
            "triage": AgentTemplates.get_triage_template
        }
        
        if agent_type not in template_map:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get development template with local execution
        return template_map[agent_type](
            environment=ExecutionEnvironment.LOCAL,
            security_level=SecurityLevel.DEVELOPMENT
        )
    
    @staticmethod
    def _get_executor_kwargs(environment: ExecutionEnvironment) -> Dict[str, Any]:
        """Get executor configuration for environment.
        
        Args:
            environment: Execution environment
            
        Returns:
            Dictionary with executor configuration
        """
        if environment == ExecutionEnvironment.E2B:
            # E2B remote sandboxing for production
            api_key = os.environ.get("E2B_API_KEY")
            if not api_key:
                logger.warning("E2B_API_KEY not found, falling back to local execution")
                return {}
            
            return {
                "api_key": api_key,
                "timeout": 30
            }
        
        elif environment == ExecutionEnvironment.DOCKER:
            # Docker containerization
            return {
                "image": "python:3.11-slim",
                "timeout": 60
            }
        
        else:
            # Local execution (default)
            return {}
    
    @staticmethod
    def validate_template(template: AgentTemplate) -> Dict[str, Any]:
        """Validate that a template configuration is valid.
        
        Args:
            template: Agent template to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Validate security configuration
        if template.security_config.max_steps > 50:
            issues.append("max_steps too high (>50), may cause timeouts")
        
        if not template.security_config.authorized_imports:
            issues.append("No authorized imports specified")
        
        # Validate monitoring configuration
        if template.monitoring_config.enable_tracing and not template.monitoring_config.enable_metrics:
            issues.append("Tracing enabled without metrics may cause overhead")
        
        # Validate model configuration
        if template.model_temperature and (template.model_temperature < 0 or template.model_temperature > 1):
            issues.append("Invalid temperature (must be 0-1)")
        
        if template.max_context_tokens > 32000:
            issues.append("Context tokens too high (>32000), may cause API errors")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "template_type": template.agent_type
        }


class ProductionConfig:
    """Production-ready configurations for the bridge design system."""
    
    @staticmethod
    def get_bridge_system_config() -> Dict[str, AgentTemplate]:
        """Get complete system configuration for production deployment.
        
        Returns:
            Dictionary mapping agent names to production templates
        """
        return {
            "triage": AgentTemplates.get_production_template("triage"),
            "geometry": AgentTemplates.get_production_template("geometry"),
            "material": AgentTemplates.get_production_template("material"),
            "structural": AgentTemplates.get_production_template("structural")
        }
    
    @staticmethod
    def get_development_config() -> Dict[str, AgentTemplate]:
        """Get complete system configuration for development.
        
        Returns:
            Dictionary mapping agent names to development templates
        """
        return {
            "triage": AgentTemplates.get_development_template("triage"),
            "geometry": AgentTemplates.get_development_template("geometry"),
            "material": AgentTemplates.get_development_template("material"),
            "structural": AgentTemplates.get_development_template("structural")
        }
    
    @staticmethod
    def validate_system_config(config: Dict[str, AgentTemplate]) -> Dict[str, Any]:
        """Validate complete system configuration.
        
        Args:
            config: Dictionary of agent templates
            
        Returns:
            Dictionary with validation results
        """
        results = {}
        overall_valid = True
        
        for agent_name, template in config.items():
            validation = AgentTemplates.validate_template(template)
            results[agent_name] = validation
            if not validation["valid"]:
                overall_valid = False
        
        return {
            "overall_valid": overall_valid,
            "agent_results": results,
            "total_agents": len(config)
        }