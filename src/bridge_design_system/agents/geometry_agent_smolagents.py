"""
Simplified Geometry Agent using native smolagents patterns.

This module provides a factory function that creates a geometry agent
following smolagents best practices, eliminating unnecessary wrappers
and custom abstractions.
"""

import logging
from typing import List, Optional, Any
from pathlib import Path

from smolagents import ToolCallingAgent, tool, PromptTemplates
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings
from ..tools.memory_tools import remember, recall, search_memory, clear_memory

logger = get_logger(__name__)


class SmolagentsGeometryAgent:
    """
    Simplified geometry agent wrapper using smolagents patterns with proper MCP lifecycle.
    
    This maintains the working MCPAdapt pattern from GeometryAgentJSON but simplifies
    the implementation using smolagents best practices.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry", 
                 component_registry: Optional[Any] = None):
        """Initialize the smolagents geometry agent."""
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.component_registry = component_registry
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # Memory tools for persistent context
        self.memory_tools = [remember, recall, search_memory, clear_memory]
        
        # MCP server configuration (use working pattern from old implementation)
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )
        
        logger.info(f"Initialized smolagents geometry agent with model {model_name}")
    
    def run(self, task: str) -> Any:
        """
        Execute geometry task using proper MCPAdapt lifecycle management.
        
        This maintains the working pattern from GeometryAgentJSON but uses
        native smolagents ToolCallingAgent inside.
        """
        logger.info(f"🎯 Executing task with smolagents geometry agent: {task[:100]}...")
        
        try:
            # Use MCPAdapt with proper lifecycle (WORKING PATTERN from old implementation)
            with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
                logger.info(f"Connected to MCP via STDIO with {len(mcp_tools)} tools")
                
                # Combine all tools
                all_tools = list(mcp_tools) + self.custom_tools + self.memory_tools
                
                # Create ToolCallingAgent with fresh MCP tools
                agent = ToolCallingAgent(
                    tools=all_tools,
                    model=self.model,
                    max_steps=10,
                    name="geometry_agent",
                    description="Creates 3D geometry in Rhino Grasshopper using MCP tools"
                )
                
                # Append custom system prompt to default smolagents prompt
                custom_prompt = get_geometry_system_prompt()
                agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
                
                logger.info("Created ToolCallingAgent with live MCP tools")
                
                # Execute task
                result = agent.run(task)
                
                # Register components if registry available
                if self.component_registry:
                    self._extract_and_register_components(task, result)
                
                logger.info("✅ Task completed successfully with smolagents geometry agent")
                return result
                
        except Exception as e:
            logger.error(f"❌ Smolagents geometry agent execution failed: {e}")
            return self._run_with_fallback(task)
    
    def _run_with_fallback(self, task: str) -> Any:
        """Run with fallback tools when MCP unavailable."""
        logger.warning("🔄 Using fallback mode - MCP unavailable")
        
        try:
            # Create fallback tools
            fallback_tools = create_fallback_tools()
            all_tools = fallback_tools + self.memory_tools + self.custom_tools
            
            # Create fallback agent
            agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=10,
                name="geometry_agent_fallback",
                description="Creates geometry descriptions when MCP is unavailable"
            )
            
            # Append fallback prompt
            fallback_prompt = get_fallback_system_prompt()
            agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\n" + fallback_prompt
            
            # Add fallback context to task
            fallback_task = f"""
{task}

IMPORTANT: You are currently in fallback mode because the Grasshopper MCP connection is unavailable. 
You have access to basic geometry tools that return data structures instead of creating actual geometry.
Please inform the user that full Grasshopper functionality requires MCP connection restoration.
"""
            
            result = agent.run(fallback_task)
            logger.info("✅ Task completed in fallback mode")
            return result
            
        except Exception as e:
            logger.error(f"❌ Even fallback execution failed: {e}")
            return {
                "error": "Task execution failed",
                "message": f"Both MCP and fallback execution failed: {e}",
                "fallback_mode": True,
                "suggestion": "Check MCP server connection and try again"
            }
    
    def _extract_and_register_components(self, task: str, result: Any) -> None:
        """Extract and register components (simplified from old implementation)."""
        try:
            # Simple component registration - could be enhanced
            if self.component_registry:
                # Store result in memory for context
                remember("geometry", "last_task", task)
                remember("geometry", "last_result", str(result)[:200])
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to register components: {e}")


def create_geometry_agent(
    custom_tools: Optional[List] = None,
    model_name: str = "geometry",
    component_registry: Optional[Any] = None,
    **kwargs
) -> SmolagentsGeometryAgent:
    """
    Factory for creating MCP-enabled geometry agent using smolagents patterns.
    
    This creates a wrapper that properly manages MCPAdapt lifecycle while using
    native smolagents ToolCallingAgent internally.
    
    Args:
        custom_tools: Additional tools to include
        model_name: Model configuration name from settings
        component_registry: Registry for tracking components
        **kwargs: Additional arguments (for compatibility)
        
    Returns:
        SmolagentsGeometryAgent instance with proper MCP lifecycle management
    """
    return SmolagentsGeometryAgent(
        custom_tools=custom_tools,
        model_name=model_name,
        component_registry=component_registry
    )


def create_fallback_tools() -> List:
    """Create basic fallback tools for when MCP is unavailable."""
    
    @tool
    def describe_geometry(geometry_type: str, parameters: dict) -> dict:
        """
        Describe geometry creation when MCP is unavailable.
        
        Args:
            geometry_type: Type of geometry to create
            parameters: Parameters for the geometry
            
        Returns:
            Description of the geometry that would be created
        """
        return {
            "status": "fallback_mode",
            "geometry_type": geometry_type,
            "parameters": parameters,
            "description": f"Would create {geometry_type} with parameters: {parameters}",
            "note": "MCP connection required for actual geometry creation"
        }
    
    @tool
    def generate_python_script(code: str) -> dict:
        """
        Generate Python script for Grasshopper (execution requires MCP).
        
        Args:
            code: Python code for geometry creation
            
        Returns:
            Script information without execution
        """
        return {
            "status": "script_generated",
            "code": code,
            "note": "Script execution requires active MCP connection to Grasshopper"
        }
    
    return [describe_geometry, generate_python_script]


def get_geometry_system_prompt() -> str:
    """Get custom system prompt for geometry agent from file."""
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        prompt_path = project_root / "system_prompts" / "geometry_agent.md"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Failed to load geometry system prompt from file: {e}")
    
    # Fallback prompt if file not found
    return """You are a specialized Geometry Agent with direct access to Rhino Grasshopper via MCP tools.

Your role is to:
- Create precise 3D geometry using MCP tools
- Work with Rhino.Geometry library functions
- Assign geometry outputs to variable 'a' for Grasshopper output
- Follow instructions exactly and work step by step

Available MCP tools allow you to:
- Execute Python scripts in Grasshopper
- Create and manipulate geometry
- Access Rhino's full geometry API

Remember:
- Each tool call is executed sequentially
- Maintain context across steps using memory tools
- Always assign final geometry to variable 'a'
"""


def get_fallback_system_prompt() -> str:
    """Get system prompt for fallback mode."""
    return """You are a Geometry Agent in fallback mode (Grasshopper MCP connection unavailable).

You can:
- Describe geometry creation steps
- Provide Python code examples
- Use basic geometry tools that return data structures

Limitations:
- Cannot create actual geometry in Grasshopper
- Tools return descriptions instead of real geometry
- Full functionality requires MCP connection

Always inform the user about these limitations and suggest restoring MCP connection for full functionality.
"""


def create_fallback_tools() -> List:
    """Create basic fallback tools for when MCP is unavailable."""
    
    @tool
    def describe_geometry(geometry_type: str, parameters: dict) -> dict:
        """
        Describe geometry creation when MCP is unavailable.
        
        Args:
            geometry_type: Type of geometry to create
            parameters: Parameters for the geometry
            
        Returns:
            Description of the geometry that would be created
        """
        return {
            "status": "fallback_mode",
            "geometry_type": geometry_type,
            "parameters": parameters,
            "description": f"Would create {geometry_type} with parameters: {parameters}",
            "note": "MCP connection required for actual geometry creation"
        }
    
    @tool
    def generate_python_script(code: str) -> dict:
        """
        Generate Python script for Grasshopper (execution requires MCP).
        
        Args:
            code: Python code for geometry creation
            
        Returns:
            Script information without execution
        """
        return {
            "status": "script_generated",
            "code": code,
            "note": "Script execution requires active MCP connection to Grasshopper"
        }
    
    return [describe_geometry, generate_python_script]


# Optional: Convenience function for component registry integration
def create_geometry_agent_with_registry(
    component_registry: Any,
    **kwargs
) -> ToolCallingAgent:
    """
    Create geometry agent with component registry integration.
    
    This is a thin wrapper that adds registry-aware tools to the agent.
    
    Args:
        component_registry: Registry for tracking components
        **kwargs: Arguments passed to create_geometry_agent
        
    Returns:
        ToolCallingAgent with registry integration
    """
    # Create registry tools
    @tool
    def register_component(name: str, data: dict) -> str:
        """
        Register a component in the component registry.
        
        Args:
            name: Component name
            data: Component data
            
        Returns:
            Registration confirmation
        """
        component_registry.register_component(name, data)
        return f"Component '{name}' registered successfully"
    
    # Add registry tool to custom tools
    custom_tools = kwargs.get('custom_tools', [])
    custom_tools.append(register_component)
    kwargs['custom_tools'] = custom_tools
    
    return create_geometry_agent(**kwargs)