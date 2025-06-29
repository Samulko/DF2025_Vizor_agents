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

    # REFACTORED: Removed shared component tracking - geometry agent is now autonomous

    # Create autonomous geometry agent with full MCP access (proper smolagents pattern)
    geometry_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            geometry_monitor = monitoring_callback("geometry_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            geometry_monitor = create_monitor_callback("geometry_agent", monitoring_callback)

    geometry_agent = _create_mcp_enabled_geometry_agent(
        monitoring_callback=geometry_monitor,
    )


    # Create rational agent for level validation
    from .rational_smolagents import create_rational_agent

    rational_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if (
            callable(monitoring_callback)
            and hasattr(monitoring_callback, "__name__")
            and "create" in monitoring_callback.__name__
        ):
            # Remote monitoring factory - create callback for this agent
            rational_monitor = monitoring_callback("rational_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback

            rational_monitor = create_monitor_callback("rational_agent", monitoring_callback)

    rational_agent = create_rational_agent(monitoring_callback=rational_monitor)

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
        managed_agents=[geometry_agent, rational_agent],  # Pass ManagedAgent instances
        **kwargs,
    )

    # REFACTORED: Removed geometry memory tools - geometry agent is now autonomous
    # The geometry agent handles its own context resolution and memory management

    # Append our custom system prompt to the default one
    custom_prompt = get_triage_system_prompt()
    manager.prompt_templates["system_prompt"] = (
        manager.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    )

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


def _create_mcp_enabled_geometry_agent(
    monitoring_callback: Optional[Any] = None,
) -> Any:
    """
    Create geometry agent using existing standalone implementation.

    Following smolagents best practices, this imports and configures
    the standalone geometry agent for use in managed_agents.

    Args:
        monitoring_callback: Optional callback for real-time monitoring

    Returns:
        SmolagentsGeometryAgent instance configured for managed_agents
    """
    logger.info("Creating geometry agent using standalone implementation")

    from .geometry_agent_smolagents import create_geometry_agent

    return create_geometry_agent(
        monitoring_callback=monitoring_callback,
    )


def _create_coordination_tools() -> List:
    """Create tools for coordination and state management."""

    # Import the CORRECTED context-based recall tools from memory_tools
    from ..tools.memory_tools import delegate_element_history_query, create_two_step_delegation_task

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
            "note": "Use geometry memory tools to check previous design decisions",
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
        Debug tool to show autonomous geometry agent state.

        REFACTORED: Now shows the autonomous geometry agent's internal state
        instead of shared component tracking cache.

        Returns:
            Debug information about geometry agent state
        """
        try:
            debug_info = []
            debug_info.append("=== AUTONOMOUS GEOMETRY AGENT DEBUG ===")
            debug_info.append("Component tracking: Handled internally by geometry agent")

            # Note: We can't directly access the geometry agent's internal cache from here
            # because it's encapsulated. This is by design for the autonomous architecture.
            debug_info.append("\\nTo see component details, delegate a task to the geometry agent")
            debug_info.append("that asks it to report its internal component state.")

            debug_info.append("\\n=== END DEBUG ===")

            result = "\\n".join(debug_info)
            logger.info("🐛 Autonomous geometry agent debug info requested")
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


# REFACTORED: Removed _create_geometry_memory_tools function entirely
# The geometry agent is now autonomous and handles its own memory/context


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
        geometry_monitor = None
        rational_monitor = None

        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                geometry_monitor = monitoring_callback("geometry_agent")
                rational_monitor = monitoring_callback("rational_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback

                geometry_monitor = create_monitor_callback("geometry_agent", monitoring_callback)
                rational_monitor = create_monitor_callback("rational_agent", monitoring_callback)

        # Create agents using the updated factory functions (returns agents directly)
        self.geometry_agent = _create_mcp_enabled_geometry_agent(
            monitoring_callback=geometry_monitor,
        )

        from .rational_smolagents import create_rational_agent

        self.rational_agent = create_rational_agent(monitoring_callback=rational_monitor)

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
            managed_agents=[self.geometry_agent, self.rational_agent],
        )

        self.component_registry = component_registry
        self.logger = logger

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
                "managed_agents": 2,  # managed_geometry + managed_rational
                "max_steps": self.manager.max_steps,
            },
            "geometry_agent": {
                "initialized": hasattr(self, "geometry_agent") and self.geometry_agent is not None,
                "type": (
                    type(self.geometry_agent).__name__
                    if hasattr(self, "geometry_agent")
                    else "Unknown"
                ),
                "name": "geometry_agent",
                "mcp_integration": "enabled",
            },
            "rational_agent": {
                "initialized": hasattr(self, "rational_agent") and self.rational_agent is not None,
                "type": (
                    type(self.rational_agent).__name__
                    if hasattr(self, "rational_agent")
                    else "Unknown"
                ),
                "name": "rational_agent",
                "level_validation": "enabled",
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

    def transfer_geometry_memory(self, element_filter: Optional[str] = None) -> bool:
        """
        Transfer design memory from geometry agent to triage agent.

        Uses smolagents native memory.steps transfer pattern from documentation
        to share design history between agents for coordination purposes.

        Args:
            element_filter: Optional element ID to filter transfer

        Returns:
            True if transfer successful, False otherwise
        """
        try:
            from ..memory import transfer_agent_memory

            logger.info("🔄 Transferring geometry memory to triage agent")

            # Get the actual geometry agent from wrapper if needed
            geometry_agent = self.geometry_agent
            if hasattr(geometry_agent, "_wrapper"):
                source_agent = geometry_agent._wrapper.agent
            else:
                source_agent = geometry_agent

            # Transfer to triage manager
            success = transfer_agent_memory(
                source_agent=source_agent, target_agent=self.manager, element_filter=element_filter
            )

            if success:
                logger.info("✅ Geometry memory transfer completed successfully")
            else:
                logger.warning("⚠️ No geometry memory found to transfer")

            return success

        except Exception as e:
            logger.error(f"❌ Memory transfer failed: {e}")
            return False

    def query_element_original_state(self, element_id: str) -> Optional[Dict[str, Any]]:
        """
        Query original element state across all agents.

        Searches both triage and geometry agent memory for original element values.
        Solves the core use case: "What was element 002's original length?"

        Args:
            element_id: Element identifier to query

        Returns:
            Dictionary with original state information, or None if not found
        """
        try:
            from ..memory import get_original_element_state

            logger.debug(f"🔍 Querying original state for element {element_id}")

            # First check triage agent memory (may have transferred geometry memory)
            triage_result = get_original_element_state(self.manager, element_id)
            if triage_result:
                logger.info(f"✅ Found original state in triage agent memory")
                return triage_result

            # Then check geometry agent memory directly
            geometry_agent = self.geometry_agent
            if hasattr(geometry_agent, "_wrapper"):
                geometry_result = get_original_element_state(
                    geometry_agent._wrapper.agent, element_id
                )
            else:
                geometry_result = get_original_element_state(geometry_agent, element_id)

            if geometry_result:
                logger.info(f"✅ Found original state in geometry agent memory")
                return geometry_result

            logger.debug(f"🔍 No original state found for element {element_id}")
            return None

        except Exception as e:
            logger.error(f"❌ Error querying element original state: {e}")
            return None

    def get_design_history_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive design history summary from all agents.

        Provides overview of design activity, element modifications, and memory health
        across the entire triage system.

        Returns:
            Dictionary with design history summary and statistics
        """
        try:
            from ..memory import get_memory_statistics, get_element_changes_count

            logger.debug("📊 Generating design history summary")

            summary = {"triage_agent": {}, "geometry_agent": {}, "overall_statistics": {}}

            # Get triage agent statistics
            summary["triage_agent"] = get_memory_statistics(self.manager)
            summary["triage_agent"]["agent_role"] = "coordination"

            # Get geometry agent statistics
            geometry_agent = self.geometry_agent
            if hasattr(geometry_agent, "_wrapper"):
                summary["geometry_agent"] = get_memory_statistics(geometry_agent._wrapper.agent)
                geometry_changes = get_element_changes_count(geometry_agent._wrapper.agent)
            else:
                summary["geometry_agent"] = get_memory_statistics(geometry_agent)
                geometry_changes = get_element_changes_count(geometry_agent)

            summary["geometry_agent"]["agent_role"] = "execution"

            # Calculate overall statistics
            total_steps = summary["triage_agent"].get("total_steps", 0) + summary[
                "geometry_agent"
            ].get("total_steps", 0)

            total_design_changes = summary["triage_agent"].get("design_changes", 0) + summary[
                "geometry_agent"
            ].get("design_changes", 0)

            summary["overall_statistics"] = {
                "total_memory_steps": total_steps,
                "total_design_changes": total_design_changes,
                "elements_modified": geometry_changes,
                "system_health": {
                    "has_design_activity": total_design_changes > 0,
                    "memory_coordination": "active" if total_steps > 0 else "inactive",
                    "agents_with_memory": sum(
                        1
                        for stats in [summary["triage_agent"], summary["geometry_agent"]]
                        if stats.get("total_steps", 0) > 0
                    ),
                },
            }

            logger.info(
                f"📊 Design history summary: {total_design_changes} changes across {len(geometry_changes)} elements"
            )
            return summary

        except Exception as e:
            logger.error(f"❌ Error generating design history summary: {e}")
            return {"error": str(e)}
