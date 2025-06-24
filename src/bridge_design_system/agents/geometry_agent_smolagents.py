"""
Simplified Geometry Agent using native smolagents patterns.

This module provides a factory function that creates a geometry agent
following smolagents best practices, eliminating unnecessary wrappers
and custom abstractions.
"""

from pathlib import Path
from typing import Any, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings

logger = get_logger(__name__)


class SmolagentsGeometryAgent:
    """
    Geometry agent wrapper using smolagents patterns with persistent MCP connection.
    
    This maintains session continuity by establishing a persistent MCP connection
    during initialization instead of creating fresh connections per request.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry", 
                 component_registry: Optional[Any] = None, monitoring_callback: Optional[Any] = None):
        """Initialize the smolagents geometry agent with persistent MCP connection."""
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.component_registry = component_registry
        
        # Required attributes for smolagents managed_agents
        self.name = "geometry_agent"
        self.description = "Creates 3D geometry in Rhino Grasshopper via persistent MCP connection"
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # MCP server configuration (use working pattern from old implementation)
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )
        
        # Establish persistent MCP connection during initialization
        logger.info("🔗 Establishing persistent MCP connection for geometry agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"✅ Persistent MCP connection established with {len(self.mcp_tools)} tools")
            
            # Combine all tools for persistent agent
            all_tools = list(self.mcp_tools) + self.custom_tools
            
            # Create persistent ToolCallingAgent with sufficient steps for error detection/fixing
            step_callbacks = [monitoring_callback] if monitoring_callback else []
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=12,  # Increased to allow: check -> modify -> detect errors -> fix -> verify -> finalize
                name="geometry_agent",
                description="Creates 3D geometry in Rhino Grasshopper using persistent MCP connection",
                step_callbacks=step_callbacks
            )
            
            # Append custom system prompt to default smolagents prompt
            custom_prompt = get_geometry_system_prompt()
            self.agent.prompt_templates["system_prompt"] = self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            
            # TODO: VizorListener not available in current setup
            # self.listener = VizorListener()
            # self.transforms = self.listener.get_transforms()
            # self.current_element = self.listener.get_current_element()

            logger.info(f"🎯 Persistent geometry agent initialized successfully with model {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to establish persistent MCP connection: {e}")
            # Fallback to agent without MCP tools if connection fails
            step_callbacks = [monitoring_callback] if monitoring_callback else []
            self.agent = ToolCallingAgent(
                tools=self.custom_tools,
                model=self.model,
                max_steps=8,  # Increased to allow proper error handling even without MCP
                name="geometry_agent",
                description="Creates 3D geometry (MCP connection failed)",
                step_callbacks=step_callbacks
            )
            self.mcp_connection = None
            self.mcp_tools = []
    
    def run(self, task: str) -> Any:
        """
        Execute geometry task using persistent MCP connection and agent memory.
        
        This uses the persistent ToolCallingAgent that maintains context
        and memory across multiple requests for iterative design.
        """
        logger.info(f"🎯 Executing task with persistent smolagents geometry agent: {task[:100]}...")
        
        try:
            # Log memory state before execution
            if hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'steps'):
                logger.debug(f"📊 Starting task with {len(self.agent.memory.steps)} existing memory steps")
            
            # Use the persistent agent that maintains context and memory
            result = self.agent.run(task)
            
            # Log memory state after execution
            if hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'steps'):
                logger.debug(f"📊 Completed task with {len(self.agent.memory.steps)} total memory steps")
            
            # Register components if registry available
            if self.component_registry:
                self._extract_and_register_components(task, result)
            
            logger.info("✅ Task completed successfully with persistent smolagents geometry agent")
            return result
            
        except Exception as e:
            logger.error(f"❌ Persistent smolagents geometry agent execution failed: {e}")
            raise RuntimeError(f"Geometry agent requires active MCP connection: {e}")
    
    
    def _extract_and_register_components(self, task: str, result: Any) -> None:
        """Extract and register components (simplified from old implementation)."""
        try:
            # Simple component registration - could be enhanced
            if self.component_registry:
                # Component registration handled by triage agent level
                logger.info(f"📝 Component registration handled by triage agent: {task[:50]}...")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to register components: {e}")
    
    def __del__(self):
        """Cleanup persistent MCP connection on agent destruction."""
        try:
            if hasattr(self, 'mcp_connection') and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("🔌 Persistent MCP connection closed for geometry agent")
        except Exception as e:
            logger.warning(f"⚠️ Error closing MCP connection in geometry agent: {e}")


def create_geometry_agent(
    custom_tools: Optional[List] = None,
    model_name: str = "geometry",
    component_registry: Optional[Any] = None,
    monitoring_callback: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Factory for creating MCP-enabled geometry agent using smolagents patterns.
    
    This creates a wrapper that properly manages MCPAdapt lifecycle and returns
    the internal ToolCallingAgent for use with managed_agents pattern.
    
    Args:
        custom_tools: Additional tools to include
        model_name: Model configuration name from settings
        component_registry: Registry for tracking components
        monitoring_callback: Optional callback for real-time monitoring
        **kwargs: Additional arguments (for compatibility)
        
    Returns:
        ToolCallingAgent instance configured for managed_agents pattern
    """
    wrapper = SmolagentsGeometryAgent(
        custom_tools=custom_tools,
        model_name=model_name,
        component_registry=component_registry,
        monitoring_callback=monitoring_callback
    )
    
    # Return the internal ToolCallingAgent for managed_agents compatibility
    # The wrapper manages MCP lifecycle, but managed_agents needs the raw agent
    internal_agent = wrapper.agent
    
    # Ensure the internal agent has required attributes for managed_agents
    internal_agent.name = "geometry_agent"
    internal_agent.description = "Creates 3D geometry in Rhino Grasshopper via MCP connection"
    
    # Store reference to wrapper for cleanup purposes
    internal_agent._wrapper = wrapper
    
    logger.info("✅ Created geometry agent for managed_agents pattern")
    return internal_agent




def get_geometry_system_prompt() -> str:
    """Get custom system prompt for geometry agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "geometry_agent.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
    
    return prompt_path.read_text(encoding='utf-8')