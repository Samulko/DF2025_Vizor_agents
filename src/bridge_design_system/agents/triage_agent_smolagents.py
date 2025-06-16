"""
Simplified Triage Agent using native smolagents ManagedAgent pattern.

This module provides a factory function that creates a triage system
following smolagents best practices, using native agent delegation
instead of custom coordination code.
"""

import logging
from typing import List, Optional, Any, Dict, Union
from pathlib import Path

from smolagents import CodeAgent, ToolCallingAgent, tool, PromptTemplates
from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings
from ..tools.memory_tools import remember, recall, search_memory, clear_memory
from .geometry_agent_smolagents import create_geometry_agent

logger = get_logger(__name__)


def create_triage_system(
    component_registry: Optional[Any] = None,
    model_name: str = "triage",
    **kwargs
) -> CodeAgent:
    """
    Create triage system using smolagents ManagedAgent pattern.
    
    This replaces the 600+ line TriageAgent class with native smolagents
    delegation. The manager agent automatically handles task routing and
    context management between specialized agents.
    
    Args:
        component_registry: Registry for tracking components across agents
        model_name: Model configuration name from settings
        **kwargs: Additional arguments passed to CodeAgent
        
    Returns:
        CodeAgent configured as manager with specialized agents
    """
    # Get model
    model = ModelProvider.get_model(model_name)
    
    # Create specialized geometry agent using working MCP wrapper approach
    geometry_agent = _create_mcp_enabled_geometry_agent(
        custom_tools=_create_registry_tools(component_registry) if component_registry else None,
        component_registry=component_registry
    )
    
    # Note: Material and Structural agents would be created here when available
    # For now, we only have geometry agent in managed_agents
    
    # Coordination tools for the manager (including memory tools)
    memory_tools = [remember, recall, search_memory, clear_memory]
    material_tool = create_material_placeholder()
    structural_tool = create_structural_placeholder()
    coordination_tools = [material_tool, structural_tool] + _create_coordination_tools() + memory_tools
    
    # Create manager agent with native managed_agents pattern (smolagents best practice)
    manager = CodeAgent(
        tools=coordination_tools,  # General coordination tools
        managed_agents=[geometry_agent],  # Native smolagents delegation
        model=model,
        name="triage_agent", 
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=kwargs.get('max_steps', 3),  # Reduced to prevent unnecessary loops
        additional_authorized_imports=["typing", "json", "datetime"],
        **kwargs
    )
    
    # Append our custom system prompt to the default one
    custom_prompt = get_triage_system_prompt()
    manager.prompt_templates["system_prompt"] = manager.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    
    logger.info("Created triage system with native smolagents delegation")
    return manager


def get_triage_system_prompt() -> str:
    """Get custom system prompt for triage agent from file."""
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        prompt_path = project_root / "system_prompts" / "triage_agent.md"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Failed to load triage system prompt from file: {e}")
    
    # Fallback to embedded prompt
    return """You are an expert AI Triage Agent coordinating bridge design tasks.

IMPORTANT RULES:
1. Be DIRECT and EFFICIENT - avoid unnecessary conversation loops
2. When delegating to geometry_agent, be SPECIFIC about what to create
3. After receiving results from agents, provide a clear summary and STOP
4. Don't ask follow-up questions unless the user asks something new

Your primary responsibilities:
1. Receive and analyze human input carefully
2. Delegate tasks to appropriate specialized agents WITH SPECIFIC INSTRUCTIONS
3. Report results back to the human in a clear, concise manner
4. STOP after reporting results - don't keep asking what to do next

You coordinate these specialized agents:
- **geometry_agent**: Creates 3D geometry in Rhino Grasshopper via MCP tools
- **material_agent**: (Coming soon) Tracks construction materials  
- **structural_agent**: (Coming soon) Assesses structural integrity

When delegating to geometry_agent:
- Provide COMPLETE specifications (coordinates, dimensions, etc.)
- Request consolidated scripts when possible
- Let the agent handle the technical implementation

Example delegation: "Create two points at (0,0,0) and (100,0,0) in a single script"

Remember: You coordinate efficiently, report results clearly, then STOP.
"""


def _create_mcp_enabled_geometry_agent(
    custom_tools: Optional[List] = None,
    component_registry: Optional[Any] = None
) -> ToolCallingAgent:
    """
    Create geometry agent that uses the working MCP wrapper for managed_agents pattern.
    
    This directly integrates the working SmolagentsGeometryAgent wrapper into
    the managed_agents pattern, ensuring real MCP functionality.
    
    Args:
        custom_tools: Additional tools to include
        component_registry: Registry for tracking components
        
    Returns:
        ToolCallingAgent that creates real geometry via MCP
    """
    from .geometry_agent_smolagents import create_geometry_agent
    
    # Create the working MCP wrapper that we know works
    geometry_wrapper = create_geometry_agent(
        custom_tools=custom_tools,
        component_registry=component_registry
    )
    
    # Create a tool that delegates directly to the working wrapper
    @tool
    def create_geometry_in_grasshopper(task_description: str) -> str:
        """
        Create actual geometry in Grasshopper using the working MCP wrapper.
        
        Args:
            task_description: Detailed description of the geometry to create
            
        Returns:
            Result from the MCP-enabled geometry agent (real geometry creation)
        """
        logger.info(f"🎯 Delegating to MCP geometry wrapper: {task_description[:100]}...")
        try:
            result = geometry_wrapper.run(task_description)
            logger.info("✅ MCP geometry wrapper executed successfully")
            return str(result)
        except Exception as e:
            logger.error(f"❌ MCP geometry wrapper failed: {e}")
            raise e  # Don't hide the error - let it bubble up
    
    # Get model and create tools
    model = ModelProvider.get_model("geometry", temperature=0.1)
    memory_tools = [remember, recall, search_memory, clear_memory]
    mcp_tools = [create_geometry_in_grasshopper]
    all_tools = mcp_tools + memory_tools + (custom_tools or [])
    
    # Create agent that uses the working MCP wrapper
    agent = ToolCallingAgent(
        tools=all_tools,
        model=model,
        max_steps=10,
        name="geometry_agent",
        description="Creates real 3D geometry in Grasshopper via MCP wrapper"
    )
    
    # Add system prompt emphasizing real geometry creation
    custom_prompt = """You are a Geometry Agent with DIRECT ACCESS to Grasshopper via MCP.

Your primary tool:
- create_geometry_in_grasshopper(): Creates REAL geometry that appears on Grasshopper canvas

IMPORTANT RULES:
1. COMBINE multiple geometry elements into ONE script when possible
2. Use create_geometry_in_grasshopper() ONCE per task, not multiple times
3. Create comprehensive Python scripts that handle all requested geometry
4. Assign ALL geometry to output variable 'a' as a list if multiple elements

Example for two points:
```python
import Rhino.Geometry as rg
start_point = rg.Point3d(0,0,0)
end_point = rg.Point3d(100,0,0)
a = [start_point, end_point]  # Both points in one output
```

You have REAL MCP connection - create efficient, consolidated geometry scripts!"""
    
    agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    
    return agent


def _create_coordination_tools() -> List:
    """Create tools for coordination and state management."""
    
    @tool
    def check_design_state() -> dict:
        """
        Check current bridge design state and progress.
        
        Returns:
            Current design state dictionary
        """
        # In the simplified version, state is tracked via memory tools
        # This is a placeholder that would integrate with actual state tracking
        return {
            "status": "Design state tracking via memory tools",
            "note": "Use recall() to check previous design decisions"
        }
    
    @tool
    def update_design_phase(phase: str, details: str) -> str:
        """
        Update the current design phase and log progress.
        
        Args:
            phase: Current phase name (e.g., "conceptual", "detailed", "structural")
            details: Details about the phase progress
            
        Returns:
            Confirmation message
        """
        # Store in memory for continuity
        remember(f"Design phase updated to: {phase}. Details: {details}")
        return f"Design phase updated to '{phase}'"
    
    return [check_design_state, update_design_phase]


def _create_registry_tools(component_registry: Any) -> List:
    """Create tools for component registry integration."""
    
    @tool
    def register_bridge_component(component_type: str, component_id: str, data: dict) -> str:
        """
        Register a bridge component in the cross-agent registry.
        
        Args:
            component_type: Type of component (e.g., "deck", "support", "cable")
            component_id: Unique identifier for the component
            data: Component data including geometry reference
            
        Returns:
            Registration confirmation
        """
        component_registry.register_component(
            name=f"{component_type}_{component_id}",
            data={
                "type": component_type,
                "id": component_id,
                **data
            }
        )
        return f"Registered {component_type} component: {component_id}"
    
    @tool
    def list_bridge_components(component_type: Optional[str] = None) -> dict:
        """
        List registered bridge components.
        
        Args:
            component_type: Optional filter by component type
            
        Returns:
            Dictionary of registered components
        """
        all_components = component_registry.get_all_components()
        
        if component_type:
            filtered = {
                k: v for k, v in all_components.items() 
                if v.get("type") == component_type
            }
            return filtered
        
        return all_components
    
    return [register_bridge_component, list_bridge_components]


def create_material_placeholder() -> Any:
    """Create placeholder tool for material agent (to be implemented)."""
    
    @tool
    def check_materials(material_type: str, quantity: float) -> dict:
        """
        Placeholder for material checking (Material Agent coming soon).
        
        Args:
            material_type: Type of material to check
            quantity: Required quantity
            
        Returns:
            Placeholder response
        """
        return {
            "status": "placeholder",
            "message": "Material Agent not yet implemented",
            "note": "This will check material availability once the Material Agent is integrated"
        }
    
    return check_materials


def create_structural_placeholder() -> Any:
    """Create placeholder tool for structural agent (to be implemented)."""
    
    @tool
    def analyze_structure(component_id: str, load_type: str = "standard") -> dict:
        """
        Placeholder for structural analysis (Structural Agent coming soon).
        
        Args:
            component_id: Component to analyze
            load_type: Type of load analysis
            
        Returns:
            Placeholder response
        """
        return {
            "status": "placeholder",
            "message": "Structural Agent not yet implemented",
            "note": "This will perform structural analysis once the Structural Agent is integrated"
        }
    
    return analyze_structure


class ResponseCompatibilityWrapper:
    """
    Wrapper to provide .success and .message attributes for backward compatibility.
    
    Smolagents agents return various types (AgentText, dict, str), but the existing
    interface expects response objects with .success and .message attributes.
    """
    
    def __init__(self, result: Any, success: bool = True, error_type: Optional[str] = None):
        """Initialize compatibility wrapper."""
        self.result = result
        self.success = success
        self.error = error_type
        
        # Extract message from various result types
        if hasattr(result, 'text'):
            self.message = result.text
        elif isinstance(result, dict):
            self.message = result.get('message', str(result))
        elif isinstance(result, str):
            self.message = result
        else:
            self.message = str(result)
        
        # Set data for backward compatibility
        self.data = result if isinstance(result, dict) else {"result": result}


# Optional: Create a wrapper for backward compatibility during transition
class TriageSystemWrapper:
    """
    Wrapper to provide backward compatibility during transition.
    
    This allows gradual migration from the old TriageAgent API to the new
    smolagents-native pattern.
    """
    
    def __init__(self, component_registry: Optional[Any] = None):
        """Initialize wrapper with smolagents manager."""
        self.manager = create_triage_system(component_registry=component_registry)
        self.component_registry = component_registry
        self.logger = logger
    
    def handle_design_request(self, request: str) -> ResponseCompatibilityWrapper:
        """
        Handle design request using smolagents manager.
        
        Args:
            request: Human designer's request
            
        Returns:
            ResponseCompatibilityWrapper for backward compatibility
        """
        try:
            # Use native smolagents execution
            result = self.manager.run(request)
            
            # Return compatibility wrapper
            return ResponseCompatibilityWrapper(result, success=True)
            
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            error_result = {
                "error": f"Error: {str(e)}",
                "error_type": type(e).__name__
            }
            return ResponseCompatibilityWrapper(error_result, success=False, error_type=type(e).__name__)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the triage system."""
        return {
            "triage": {
                "initialized": True,
                "type": "smolagents_manager",
                "managed_agents": len(self.manager.managed_agents) if hasattr(self.manager, 'managed_agents') else 0,
                "max_steps": self.manager.max_steps
            },
            "geometry_agent": {
                "initialized": True,
                "type": "ToolCallingAgent",
                "mcp_integration": "enabled"
            }
        }
    
    def reset_all_agents(self) -> None:
        """Reset all agents (smolagents doesn't need explicit reset)."""
        # Smolagents agents are stateless by design
        # Memory is handled via memory tools that can be cleared
        try:
            clear_memory()
            logger.info("Memory cleared for smolagents system")
        except Exception as e:
            logger.warning(f"Failed to clear memory: {e}")
        
        logger.info("Smolagents system reset completed")