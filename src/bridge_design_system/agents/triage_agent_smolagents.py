"""
Simplified Triage Agent using native smolagents ManagedAgent pattern.

This module provides a factory function that creates a triage system
following smolagents best practices, using native agent delegation
instead of custom coordination code.
"""

import logging
from typing import List, Optional, Any, Dict
from pathlib import Path

from smolagents import CodeAgent, tool, PromptTemplates
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
    
    # Create specialized agents using the wrapper pattern for proper MCP lifecycle
    geometry_agent_wrapper = create_geometry_agent(
        custom_tools=_create_registry_tools(component_registry) if component_registry else None,
        component_registry=component_registry
    )
    
    # Create a tool that delegates to the geometry agent wrapper
    @tool
    def geometry_agent(task: str) -> str:
        """
        Delegate geometry tasks to the specialized geometry agent.
        
        Args:
            task: Detailed description of the geometry task to perform
            
        Returns:
            Result from the geometry agent execution
        """
        try:
            result = geometry_agent_wrapper.run(task)
            return str(result)
        except Exception as e:
            return f"Geometry agent error: {e}"
    
    # Note: Material and Structural agents would be created here when available
    # For now, we'll add placeholder tools that indicate these agents are coming
    material_tool = create_material_placeholder()
    structural_tool = create_structural_placeholder()
    
    # Coordination tools for the manager
    coordination_tools = [geometry_agent, material_tool, structural_tool] + _create_coordination_tools()
    
    # Create manager agent with tool-based delegation (smolagents pattern)
    manager = CodeAgent(
        tools=coordination_tools,  # All delegation via tools
        model=model,
        name="triage_agent", 
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=kwargs.get('max_steps', 10),
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

Your primary responsibilities:
1. Receive and analyze human input carefully
2. Ask clarifying questions for ambiguous requests (prioritize the most critical question)
3. Delegate tasks to appropriate specialized agents
4. Monitor and report results back to the human

You coordinate these specialized agents:
- **geometry_agent**: Creates 3D geometry in Rhino Grasshopper via MCP tools
- **material_agent**: (Coming soon) Tracks construction materials  
- **structural_agent**: (Coming soon) Assesses structural integrity

When delegating:
- Use managed agents directly - they handle their own context
- Provide clear task descriptions
- Let agents use their specialized tools
- Report results back clearly

Remember: You coordinate, you don't execute specialized tasks yourself.
"""


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
    
    def handle_design_request(self, request: str) -> Dict[str, Any]:
        """
        Handle design request using smolagents manager.
        
        Args:
            request: Human designer's request
            
        Returns:
            Response dictionary for backward compatibility
        """
        try:
            # Use native smolagents execution
            result = self.manager.run(request)
            
            return {
                "success": True,
                "message": str(result),
                "data": result if isinstance(result, dict) else {"result": result}
            }
            
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": type(e).__name__
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the triage system."""
        return {
            "triage": {
                "initialized": True,
                "type": "smolagents_manager",
                "managed_agents": len(self.manager.managed_agents),
                "max_steps": self.manager.max_steps
            },
            "geometry_agent": {
                "initialized": True,
                "type": "ToolCallingAgent",
                "mcp_integration": True
            }
        }