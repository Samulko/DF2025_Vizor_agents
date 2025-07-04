"""
Simplified Triage Agent using native smolagents ManagedAgent pattern.

This module provides a factory function that creates a triage system
following smolagents best practices, using native agent delegation
instead of custom coordination code.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..memory import track_design_changes
from ..monitoring.workshop_logging import add_workshop_logging
from .category_smolagent import create_category_agent
from .design_agent_smolagents import create_design_agent
from .surface_agent import create_surface_agent

# NOTE: Voice capabilities moved to bridge_chat_agent.py (chat-supervisor pattern)
# The triage agent is now purely for bridge design coordination without voice/chat handling

# OLD FILE-BASED MEMORY TOOLS - COMMENTED OUT, USING NATIVE MEMORY INSTEAD
# from ..tools.memory_tools import clear_memory, recall, remember, search_memory

logger = get_logger(__name__)


def create_triage_system(
    component_registry: Optional[Any] = None,
    model_name: str = "triage",
    monitoring_callback: Optional[Any] = None,
    **kwargs,
) -> CodeAgent:
    """
    Create triage system using smolagents ManagedAgent pattern.

    This replaces the 600+ line TriageAgent class with native smolagents
    delegation. The manager agent automatically handles task routing and
    context management between specialized agents.

    Args:
        component_registry: Registry for tracking components across agents
        model_name: Model configuration name from settings
        monitoring_callback: Optional callback for real-time monitoring
        **kwargs: Additional arguments passed to CodeAgent

    Returns:
        CodeAgent configured as manager with specialized agents
    """
    # Get model
    model = ModelProvider.get_model(model_name)

    # Focus on surface and category agents only

    # Create surface agent for surface generation and adjustment
    surface_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            surface_monitor = monitoring_callback("surface_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            surface_monitor = create_monitor_callback("surface_agent", monitoring_callback)

    surface_agent = create_surface_agent(monitoring_callback=surface_monitor)

    # Create category agent for categorization and recommendations
    category_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            category_monitor = monitoring_callback("category_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            category_monitor = create_monitor_callback("category_agent", monitoring_callback)

    category_agent = create_category_agent(monitoring_callback=category_monitor)

    # Create design agent for interactive 3D form exploration
    design_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            design_monitor = monitoring_callback("design_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            design_monitor = create_monitor_callback("design_agent", monitoring_callback)

    design_agent = create_design_agent(monitoring_callback=design_monitor)

    # Note: Material and structural analysis can be added as separate agents if needed

    # Create manager agent first (without old file-based memory tools)
    # OLD FILE-BASED MEMORY TOOLS - COMMENTED OUT, USING NATIVE MEMORY INSTEAD
    # memory_tools = [remember, recall, search_memory, clear_memory]
    memory_tools = []  # Using native smolagents memory via geometry memory tools instead
    basic_coordination_tools = _create_coordination_tools()

    # SIMPLIFIED: Manager tools without placeholder tools - delegate to specialized agents
    manager_tools = basic_coordination_tools + memory_tools

    # Create manager agent with managed_agents pattern (smolagents best practice)
    # Extract max_steps from kwargs to avoid duplicate parameter error
    max_steps = kwargs.pop(
        "max_steps", 6
    )  # Increased to allow proper task completion and error handling

    # Prepare step_callbacks for triage agent monitoring
    # Add native smolagents memory tracking callback for design coordination
    step_callbacks = kwargs.pop("step_callbacks", [])
    step_callbacks.append(track_design_changes)

    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            triage_monitor = monitoring_callback("triage_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            triage_monitor = create_monitor_callback("triage_agent", monitoring_callback)
        step_callbacks.append(triage_monitor)

    manager = CodeAgent(
        tools=manager_tools,  # Coordination tools only
        model=model,
        name="triage_agent",
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=max_steps,
        step_callbacks=step_callbacks,
        additional_authorized_imports=["typing", "json", "datetime"],
        managed_agents=[
            surface_agent,
            category_agent,
            design_agent,
        ],  # Pass ManagedAgent instances
        **kwargs,
    )

    # REFACTORED: Removed geometry memory tools - geometry agent is now autonomous
    # The geometry agent handles its own context resolution and memory management

    # Append our custom system prompt to the default one
    custom_prompt = get_triage_system_prompt()
    manager.prompt_templates["system_prompt"] = (
        manager.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    )

    # Note: Workshop logging will be added by the wrapper class to avoid duplicates
    logger.info("Created triage system with native smolagents delegation")
    return manager


def get_triage_system_prompt() -> str:
    """Get custom system prompt for triage agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "triage_agent.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")




def _create_coordination_tools() -> List:
    """Create tools for coordination and state management."""

    # Import the CORRECTED context-based recall tools from memory_tools
    from ..tools.memory_tools import create_two_step_delegation_task, delegate_element_history_query

    @tool
    def reset_agent_memories() -> str:
        """
        Reset all agent conversation memories to start fresh.

        Use this when the user explicitly wants to start a completely new design
        or when there are memory-related issues that need clearing.

        Returns:
            Confirmation message about the reset
        """
        try:
            # This is a placeholder - actual reset happens at the wrapper level
            # when the user types 'reset' in the CLI
            return (
                "To reset agent memories, please type 'reset' in the command line interface. "
                "This will clear all conversation history and component registry for a fresh start."
            )
        except Exception as e:
            return f"Reset information: {e}"

    @tool
    def check_design_state() -> dict:
        """
        Check current bridge design state and progress.

        Returns:
            Current design state dictionary
        """
        # State is tracked via native smolagents memory
        # This is a placeholder that would integrate with actual state tracking
        return {
            "status": "Design state tracking via native smolagents memory",
            "note": "Use surface and category agents to manage design decisions",
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
        # Phase updates are automatically tracked in smolagents conversation memory
        logger.info(f"Design phase updated to: {phase}. Details: {details}")
        return f"Design phase updated to '{phase}'"

    @tool
    def debug_component_tracking() -> str:
        """
        Debug tool to show current managed agents state.

        Returns:
            Debug information about managed agents
        """
        try:
            debug_info = []
            debug_info.append("=== MANAGED AGENTS DEBUG ===")
            debug_info.append("Active agents: surface_agent, category_agent, design_agent")
            debug_info.append("Coordination: Native smolagents delegation")
            debug_info.append("\\n=== END DEBUG ===")

            result = "\\n".join(debug_info)
            logger.info("🐛 Managed agents debug info requested")
            return result

        except Exception as e:
            logger.error(f"❌ Error in debug tool: {e}")
            return f"Debug tool error: {e}"

    # CRITICAL: Return CORRECTED context-based recall tools for true smol-agents native solution
    return [
        reset_agent_memories,
        check_design_state,
        update_design_phase,
        debug_component_tracking,
        # CORRECTED: True smol-agents delegation tools (no manual memory parsing)
        delegate_element_history_query,
        create_two_step_delegation_task,
    ]


# Focused on surface and category agents only


def _create_registry_tools(component_registry: Any) -> List:
    """
    Create tools for component registry integration.

    NOTE: The component registry is orthogonal to the autonomous agent architecture.
    It serves as a cross-agent communication mechanism and external component tracking,
    while the geometry agent's internal_component_cache handles autonomous context resolution.

    This separation allows:
    - Autonomous operation: Agent resolves context internally
    - Cross-agent communication: Registry enables material/structural agents to access geometry
    - External integration: Registry provides API for external tools/monitoring
    """

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
            data={"type": component_type, "id": component_id, **data},
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
            filtered = {k: v for k, v in all_components.items() if v.get("type") == component_type}
            return filtered

        return all_components

    return [register_bridge_component, list_bridge_components]


# Material and structural analysis agents can be added here if needed


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
        if hasattr(result, "text"):
            self.message = result.text
        elif isinstance(result, dict):
            self.message = result.get("message", str(result))
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

    def __init__(
        self, component_registry: Optional[Any] = None, monitoring_callback: Optional[Any] = None
    ):
        """Initialize wrapper with smolagents manager and ManagedAgent instances."""
        # Create the triage manager with proper managed_agents
        model = ModelProvider.get_model("triage")

        # Create coordination tools
        basic_coordination_tools = _create_coordination_tools()
        manager_tools = basic_coordination_tools

        # Create managed agents using factory functions
        surface_monitor = None
        category_monitor = None
        design_monitor = None

        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                surface_monitor = monitoring_callback("surface_agent")
                category_monitor = monitoring_callback("category_agent")
                design_monitor = monitoring_callback("design_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback

                surface_monitor = create_monitor_callback("surface_agent", monitoring_callback)
                category_monitor = create_monitor_callback("category_agent", monitoring_callback)
                design_monitor = create_monitor_callback("design_agent", monitoring_callback)

        # Create agents using the updated factory functions (returns agents directly)
        self.surface_agent = create_surface_agent(monitoring_callback=surface_monitor)
        self.category_agent = create_category_agent(monitoring_callback=category_monitor)
        self.design_agent = create_design_agent(monitoring_callback=design_monitor)

        # Create triage manager with managed_agents and memory tracking
        manager_step_callbacks = [track_design_changes]
        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                triage_monitor = monitoring_callback("triage_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback

                triage_monitor = create_monitor_callback("triage_agent", monitoring_callback)
            manager_step_callbacks.append(triage_monitor)

        self.manager = CodeAgent(
            tools=manager_tools,
            model=model,
            name="triage_agent",
            description="Coordinates bridge design tasks by delegating to specialized agents",
            max_steps=6,
            step_callbacks=manager_step_callbacks,
            additional_authorized_imports=["typing", "json", "datetime"],
            managed_agents=[
                self.surface_agent,
                self.category_agent,
                self.design_agent,
            ],
        )

        self.component_registry = component_registry
        self.logger = logger

        # Add modular workshop logging - just 1 line!
        add_workshop_logging(self.manager, "triage_agent")

        logger.info("✅ Created TriageSystemWrapper with proper managed_agents pattern")

    def handle_design_request(
        self, request: str, gaze_id: Optional[str] = None
    ) -> ResponseCompatibilityWrapper:
        """
        Handle design request using native smolagents delegation.

        Args:
            request: Human designer's request
            gaze_id: Optional gaze context from VizorListener (e.g., "dynamic_003")

        Returns:
            ResponseCompatibilityWrapper for backward compatibility
        """
        try:
            # Use the manager agent for coordinated multi-agent workflow
            logger.info("🤖 Using manager agent for coordinated design workflow")

            # Add gaze context to the request if available
            enhanced_request = request
            if gaze_id and self._validate_gaze_id(gaze_id):
                enhanced_request = f"{request}\n\nGaze context: focusing on object {gaze_id}"

            # Let smolagents handle the coordination automatically
            result = self.manager.run(enhanced_request)

            logger.info("✅ Smolagents coordination completed successfully")
            return ResponseCompatibilityWrapper(result, success=True)

        except Exception as e:
            logger.error(f"Manager coordination failed: {e}")
            error_result = {
                "error": str(e),
                "workflow_status": "failed",
                "error_type": type(e).__name__,
            }
            return ResponseCompatibilityWrapper(
                error_result, success=False, error_type=type(e).__name__
            )

    def _validate_gaze_id(self, gaze_id: str) -> bool:
        """
        Validate gaze ID follows expected dynamic_XXX format.

        Args:
            gaze_id: Gaze ID string from VizorListener

        Returns:
            True if valid format, False otherwise
        """
        import re

        return bool(re.match(r"^dynamic_\d{3}$", gaze_id))

    def get_status(self) -> Dict[str, Any]:
        """Get status of the triage system."""
        return {
            "triage": {
                "initialized": True,
                "type": "smolagents_managed_agents",
                "managed_agents": 3,  # managed_surface + managed_category + managed_design
                "max_steps": self.manager.max_steps,
            },
            "surface_agent": {
                "initialized": hasattr(self, "surface_agent") and self.surface_agent is not None,
                "type": (
                    type(self.surface_agent).__name__
                    if hasattr(self, "surface_agent")
                    else "Unknown"
                ),
                "name": "surface_agent",
                "surface_generation": "enabled",
            },
            "category_agent": {
                "initialized": hasattr(self, "category_agent") and self.category_agent is not None,
                "type": (
                    type(self.category_agent).__name__
                    if hasattr(self, "category_agent")
                    else "Unknown"
                ),
                "name": "category_agent",
                "categorization": "enabled",
            },
            "design_agent": {
                "initialized": hasattr(self, "design_agent") and self.design_agent is not None,
                "type": (
                    type(self.design_agent).__name__
                    if hasattr(self, "design_agent")
                    else "Unknown"
                ),
                "name": "design_agent",
                "design_exploration": "enabled",
            },
        }

    def reset_all_agents(self) -> None:
        """Reset all agents by clearing their conversation memory."""
        try:
            # Reset the main triage agent memory
            if hasattr(self.manager, "memory") and hasattr(self.manager.memory, "steps"):
                steps_cleared = len(self.manager.memory.steps)
                self.manager.memory.steps.clear()
                logger.info(f"✅ Cleared {steps_cleared} triage agent memory steps")

            # Reset managed agents memory
            if hasattr(self.manager, "managed_agents") and self.manager.managed_agents:
                for i, agent in enumerate(self.manager.managed_agents):
                    agent_name = getattr(agent, "name", f"agent_{i}")

                    # Reset agent memory directly
                    if hasattr(agent, "memory") and hasattr(agent.memory, "steps"):
                        steps_cleared = len(agent.memory.steps)
                        agent.memory.steps.clear()
                        logger.info(f"✅ Cleared {steps_cleared} {agent_name} memory steps")

                    # Special handling for geometry agent's internal component cache
                    if hasattr(agent, "_wrapper"):
                        wrapper = agent._wrapper
                        if hasattr(wrapper, "internal_component_cache"):
                            cache_cleared = len(wrapper.internal_component_cache)
                            wrapper.internal_component_cache.clear()
                            logger.info(
                                f"✅ Cleared {cache_cleared} {agent_name} component cache entries"
                            )

            logger.info("🔄 All agent memories have been reset - starting fresh session")

        except Exception as e:
            logger.warning(f"⚠️ Error during agent reset: {e}")
            logger.info("🔄 Reset completed with warnings")



    def get_design_history_summary(self) -> Dict[str, Any]:
        """
        Get design history summary from managed agents.

        Provides overview of surface and category agent activity.

        Returns:
            Dictionary with design history summary and statistics
        """
        try:
            logger.debug("📊 Generating design history summary")

            summary = {
                "triage_agent": {"agent_role": "coordination", "managed_agents": 3},
                "surface_agent": {"agent_role": "surface_management"},
                "category_agent": {"agent_role": "material_categorization"},
                "design_agent": {"agent_role": "interactive_design_exploration"},
                "overall_statistics": {
                    "active_agents": 3,
                    "system_health": "active",
                },
            }

            logger.info("📊 Design history summary: Surface and category agents active")
            return summary

        except Exception as e:
            logger.error(f"❌ Error generating design history summary: {e}")
            return {"error": str(e)}


# NOTE: Voice capabilities moved to bridge_chat_agent.py using chat-supervisor pattern
# This file now focuses purely on bridge design coordination without voice/chat handling


# CLI entry point (voice moved to bridge_chat_agent.py)
if __name__ == "__main__":

    print("🌉 Bridge Design Triage Agent (Supervisor)")
    print("=" * 50)
    print("NOTE: This is the pure bridge design supervisor.")
    print("For voice/chat interface, use:")
    print("  python launch_voice_agent.py           # Chat-supervisor pattern")
    print("  python launch_voice_agent.py text      # Text interface")
    print()
    print("This module provides:")
    print("  - BridgeDesignSupervisor: Pure coordination logic")
    print("  - TriageSystemWrapper: Backward compatibility")
    print("  - Factory functions for supervisor creation")
    print()
    print("Architecture: Chat-Supervisor Pattern")
    print("  💬 Chat: bridge_chat_agent.py (Gemini Live API)")
    print("  🔧 Supervisor: triage_agent_smolagents.py (Bridge design)")
    print("  🎯 Integration: Tools connect chat to supervisor")
