"""Agent Factory for creating specialized agents following smolagents best practices.

This module provides factory methods for creating agents with proper configuration,
security settings, and monitoring integration. It replaces complex inheritance
hierarchies with clean factory patterns.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import (
    AgentError,
    AgentExecutionError,
    CodeAgent,
    Tool,
    ToolCallingAgent,
)

from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..tools.memory_tools import clear_memory, recall, remember, search_memory

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents following smolagents patterns.
    
    This factory replaces the BaseAgent inheritance pattern with composition
    and factory methods. It ensures consistent configuration, security settings,
    and monitoring across all agent types.
    """
    
    @staticmethod
    def create_geometry_agent(
        custom_tools: Optional[List[Tool]] = None,
        model_name: str = "geometry",
        component_registry = None,
        **kwargs
    ) -> ToolCallingAgent:
        """Create ToolCallingAgent for MCP geometry operations.
        
        Args:
            custom_tools: Additional custom tools to include
            model_name: Model configuration name from settings
            component_registry: Registry for tracking components across agents
            **kwargs: Additional configuration options
            
        Returns:
            Configured ToolCallingAgent for geometry operations
            
        Raises:
            AgentError: If agent creation fails
        """
        try:
            logger.info(f"Creating geometry agent with model: {model_name}")
            
            # Get model with precise temperature for geometry tasks
            model = ModelProvider.get_model(model_name, temperature=0.1)
            
            # Prepare custom tools and memory tools
            all_custom_tools = (custom_tools or []) + [remember, recall, search_memory, clear_memory]
            
            # Get MCP connection parameters
            stdio_params = settings.get_mcp_connection_fallback_params()
            
            # Create agent with MCP tools integrated
            def create_agent_with_mcp():
                """Create agent with live MCP connection."""
                try:
                    with MCPAdapt(stdio_params, SmolAgentsAdapter()) as mcp_tools:
                        # Combine MCP tools with custom tools
                        all_tools = list(mcp_tools) + all_custom_tools
                        
                        logger.info(f"Connected to MCP with {len(mcp_tools)} tools")
                        
                        # Create ToolCallingAgent with security settings
                        agent = ToolCallingAgent(
                            tools=all_tools,
                            model=model,
                            max_steps=kwargs.get('max_steps', settings.max_agent_steps)
                        )
                        
                        logger.info("✅ Geometry agent created with ToolCallingAgent")
                        return agent
                        
                except Exception as e:
                    logger.warning(f"MCP connection failed: {e}")
                    raise AgentExecutionError(f"Failed to connect to MCP: {e}")
            
            return create_agent_with_mcp()
            
        except Exception as e:
            logger.error(f"Failed to create geometry agent: {e}")
            raise AgentError(f"Geometry agent creation failed: {e}")
    
    @staticmethod
    def create_material_agent(
        tools: List[Tool],
        model_name: str = "material",
        **kwargs
    ) -> CodeAgent:
        """Create CodeAgent for material management and analysis.
        
        Args:
            tools: Material management tools
            model_name: Model configuration name from settings
            **kwargs: Additional configuration options
            
        Returns:
            Configured CodeAgent for material operations
            
        Raises:
            AgentError: If agent creation fails
        """
        try:
            logger.info(f"Creating material agent with model: {model_name}")
            
            # Get model configuration
            model = ModelProvider.get_model(model_name)
            
            # Add memory tools to material tools
            all_tools = tools + [remember, recall, search_memory, clear_memory]
            
            # Get security configuration
            security_config = AgentFactory._get_security_config("material")
            
            # Create CodeAgent with security settings
            agent = CodeAgent(
                tools=all_tools,
                model=model,
                max_steps=kwargs.get('max_steps', settings.max_agent_steps),
                additional_authorized_imports=security_config["authorized_imports"]
            )
            
            logger.info("✅ Material agent created with CodeAgent")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create material agent: {e}")
            raise AgentError(f"Material agent creation failed: {e}")
    
    @staticmethod
    def create_structural_agent(
        tools: List[Tool],
        model_name: str = "structural",
        **kwargs
    ) -> CodeAgent:
        """Create CodeAgent for structural analysis and calculations.
        
        Args:
            tools: Structural analysis tools
            model_name: Model configuration name from settings
            **kwargs: Additional configuration options
            
        Returns:
            Configured CodeAgent for structural operations
            
        Raises:
            AgentError: If agent creation fails
        """
        try:
            logger.info(f"Creating structural agent with model: {model_name}")
            
            # Get model configuration
            model = ModelProvider.get_model(model_name)
            
            # Add memory tools to structural tools
            all_tools = tools + [remember, recall, search_memory, clear_memory]
            
            # Get security configuration for structural analysis
            security_config = AgentFactory._get_security_config("structural")
            
            # Create CodeAgent with enhanced security for calculations
            agent = CodeAgent(
                tools=all_tools,
                model=model,
                max_steps=kwargs.get('max_steps', settings.max_agent_steps),
                additional_authorized_imports=security_config["authorized_imports"]
            )
            
            logger.info("✅ Structural agent created with CodeAgent")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create structural agent: {e}")
            raise AgentError(f"Structural agent creation failed: {e}")
    
    @staticmethod
    def create_triage_agent(
        coordination_tools: List[Tool],
        managed_agents: List[Union[CodeAgent, ToolCallingAgent]],
        model_name: str = "triage",
        **kwargs
    ) -> CodeAgent:
        """Create CodeAgent for task coordination and delegation.
        
        Args:
            coordination_tools: Tools for task coordination
            managed_agents: List of specialized agents to manage
            model_name: Model configuration name from settings
            **kwargs: Additional configuration options
            
        Returns:
            Configured CodeAgent for coordination operations
            
        Raises:
            AgentError: If agent creation fails
        """
        try:
            logger.info(f"Creating triage agent with model: {model_name}")
            
            # Get model configuration
            model = ModelProvider.get_model(model_name)
            
            # Add memory tools for conversation persistence
            all_tools = coordination_tools + [remember, recall, search_memory, clear_memory]
            
            # Get security configuration
            security_config = AgentFactory._get_security_config("triage")
            
            # Create CodeAgent with managed agents for delegation
            agent = CodeAgent(
                tools=all_tools,
                model=model,
                managed_agents=managed_agents,
                max_steps=kwargs.get('max_steps', settings.max_agent_steps),
                additional_authorized_imports=security_config["authorized_imports"]
            )
            
            logger.info(f"✅ Triage agent created with {len(managed_agents)} managed agents")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create triage agent: {e}")
            raise AgentError(f"Triage agent creation failed: {e}")
    
    @staticmethod
    def create_agent(
        agent_type: str,
        tools: List[Tool],
        model_name: Optional[str] = None,
        **kwargs
    ) -> Union[CodeAgent, ToolCallingAgent]:
        """Generic agent creation method.
        
        Args:
            agent_type: Type of agent (code, tool_calling, geometry, material, structural, triage)
            tools: List of tools for the agent
            model_name: Model configuration name (defaults to agent_type)
            **kwargs: Additional configuration options
            
        Returns:
            Configured agent instance
            
        Raises:
            AgentError: If agent type is unknown or creation fails
        """
        if model_name is None:
            model_name = agent_type
        
        # Route to specialized factory methods
        if agent_type == "geometry" or agent_type == "tool_calling":
            return AgentFactory.create_geometry_agent(
                custom_tools=tools,
                model_name=model_name,
                **kwargs
            )
        
        elif agent_type == "material":
            return AgentFactory.create_material_agent(
                tools=tools,
                model_name=model_name,
                **kwargs
            )
        
        elif agent_type == "structural":
            return AgentFactory.create_structural_agent(
                tools=tools,
                model_name=model_name,
                **kwargs
            )
        
        elif agent_type == "triage":
            managed_agents = kwargs.pop("managed_agents", [])
            return AgentFactory.create_triage_agent(
                coordination_tools=tools,
                managed_agents=managed_agents,
                model_name=model_name,
                **kwargs
            )
        
        elif agent_type == "code":
            # Generic CodeAgent creation
            model = ModelProvider.get_model(model_name)
            security_config = AgentFactory._get_security_config("generic")
            
            return CodeAgent(
                tools=tools + [remember, recall, search_memory, clear_memory],
                model=model,
                max_steps=kwargs.get('max_steps', settings.max_agent_steps),
                additional_authorized_imports=security_config["authorized_imports"]
            )
        
        else:
            from smolagents import AgentLogger
            raise AgentError(f"Unknown agent type: {agent_type}", AgentLogger())
    
    @staticmethod
    def _get_security_config(agent_type: str) -> Dict[str, List[str]]:
        """Get security configuration for agent type.
        
        Args:
            agent_type: Type of agent (geometry, material, structural, triage, generic)
            
        Returns:
            Dictionary with security configuration
        """
        # Base authorized imports for all agents
        base_imports = [
            "json", "datetime", "pathlib", "typing", "dataclasses", "enum",
            "re", "collections", "functools", "operator", "itertools", "math"
        ]
        
        # Agent-specific imports
        if agent_type == "structural":
            # Structural analysis needs numerical libraries
            additional_imports = ["numpy", "scipy", "pandas", "matplotlib"]
        
        elif agent_type == "material":
            # Material management needs data handling
            additional_imports = ["sqlite3", "csv", "pandas"]
        
        elif agent_type == "geometry":
            # Geometry agent doesn't need additional imports (uses MCP tools)
            additional_imports = []
        
        elif agent_type == "triage":
            # Triage agent needs coordination capabilities
            additional_imports = ["asyncio", "concurrent.futures"]
        
        else:
            # Generic/fallback configuration
            additional_imports = []
        
        return {
            "authorized_imports": base_imports + additional_imports
        }
    
    @staticmethod
    def validate_agent_creation(agent_type: str) -> Dict[str, Any]:
        """Validate that an agent can be created successfully.
        
        Args:
            agent_type: Type of agent to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Test model configuration
            model_name = agent_type
            model_info = ModelProvider.get_model_info(model_name)
            
            # Test MCP connection for geometry agents
            mcp_status = None
            if agent_type == "geometry":
                try:
                    stdio_params = settings.get_mcp_connection_fallback_params()
                    with MCPAdapt(stdio_params, SmolAgentsAdapter()) as mcp_tools:
                        mcp_status = {
                            "connected": True,
                            "tool_count": len(mcp_tools)
                        }
                except Exception as e:
                    mcp_status = {
                        "connected": False,
                        "error": str(e)
                    }
            
            return {
                "agent_type": agent_type,
                "valid": True,
                "model_info": model_info,
                "mcp_status": mcp_status,
                "security_config": AgentFactory._get_security_config(agent_type)
            }
            
        except Exception as e:
            return {
                "agent_type": agent_type,
                "valid": False,
                "error": str(e)
            }