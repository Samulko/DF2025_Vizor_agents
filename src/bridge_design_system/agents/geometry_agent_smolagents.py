"""
Simplified Geometry Agent using native smolagents patterns.

This module provides a factory function that creates a geometry agent
following smolagents best practices, eliminating unnecessary wrappers
and custom abstractions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..memory import track_design_changes

logger = get_logger(__name__)


class SmolagentsGeometryAgent:
    """
    Geometry agent wrapper using smolagents patterns with persistent MCP connection.

    This maintains session continuity by establishing a persistent MCP connection
    during initialization instead of creating fresh connections per request.
    """

    def __init__(
        self,
        model_name: str = "geometry",
        monitoring_callback: Optional[Any] = None,
    ):
        """Initialize the smolagents geometry agent with persistent MCP connection."""
        self.model_name = model_name

        # Required attributes for smolagents managed_agents
        self.name = "geometry_agent"
        self.description = "Creates 3D geometry in Rhino Grasshopper via MCP connection. Handles bridge components, structural elements, and geometric modeling tasks."

        # Get model configuration
        self.model = ModelProvider.get_model(model_name, temperature=0.1)

        # MCP server configuration (use working pattern from old implementation)
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command, args=settings.mcp_stdio_args.split(","), env=None
        )

        # Establish persistent MCP connection during initialization
        logger.info("🔗 Establishing persistent MCP connection for geometry agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(
                f"✅ Persistent MCP connection established with {len(self.mcp_tools)} tools"
            )

            # Use only MCP tools for persistent agent
            all_tools = list(self.mcp_tools)

            # Add self-history tool for smol-agents native context-based recall
            all_tools.append(self._create_self_history_tool())

            # Create persistent ToolCallingAgent with sufficient steps for error detection/fixing
            # Add native smolagents memory tracking callback for design state tracking
            step_callbacks = [track_design_changes]
            if monitoring_callback:
                step_callbacks.append(monitoring_callback)

            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=12,  # Increased to allow: check -> modify -> detect errors -> fix -> verify -> finalize
                name="geometry_agent",
                description="Creates 3D geometry in Rhino Grasshopper via MCP connection. Handles bridge components, structural elements, and geometric modeling tasks.",
                step_callbacks=step_callbacks,
            )

            # Append custom system prompt to default smolagents prompt
            custom_prompt = get_geometry_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )

            logger.info(
                f"🎯 Persistent geometry agent initialized successfully with model {model_name}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to establish persistent MCP connection: {e}")
            raise RuntimeError(f"Geometry agent requires active MCP connection: {e}")

    def run(self, task: str) -> Any:
        """
        Execute geometry task using persistent MCP connection and agent memory.

        This uses the persistent ToolCallingAgent that maintains context
        and memory across multiple requests for iterative design.
        """
        logger.info(f"🎯 Executing task with persistent smolagents geometry agent: {task[:100]}...")

        try:
            # Log memory state before execution
            if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "steps"):
                logger.debug(
                    f"📊 Starting task with {len(self.agent.memory.steps)} existing memory steps"
                )

            # Use the persistent agent that maintains context and memory
            result = self.agent.run(task)

            # Log memory state after execution
            if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "steps"):
                logger.debug(
                    f"📊 Completed task with {len(self.agent.memory.steps)} total memory steps"
                )

            # Component registration removed - using native smolagents memory instead

            logger.info("✅ Task completed successfully with persistent smolagents geometry agent")
            return result

        except Exception as e:
            logger.error(f"❌ Persistent smolagents geometry agent execution failed: {e}")
            raise RuntimeError(f"Geometry agent requires active MCP connection: {e}")

    def run_with_manual_steps(self, task: str, enable_memory_tracking: bool = True) -> Any:
        """
        Execute task with manual step control for enhanced memory management.

        Follows smolagents documentation pattern for manual execution.
        Allows memory modification between steps for precise design state tracking.

        Args:
            task: Task description to execute
            enable_memory_tracking: Whether to enable enhanced memory tracking between steps

        Returns:
            Final answer from agent execution

        Reference:
            Smolagents manual execution pattern from memory.mdx#_snippet_5
        """
        from smolagents import ActionStep, TaskStep

        logger.info(f"🔧 Starting manual execution with memory tracking: {enable_memory_tracking}")
        logger.debug(f"Task: {task[:100]}...")

        try:
            # Add task to memory following smolagents pattern
            self.agent.memory.steps.append(TaskStep(task=task, task_images=[]))

            final_answer = None
            step_number = 1
            max_steps = 10

            while final_answer is None and step_number <= max_steps:
                memory_step = ActionStep(
                    step_number=step_number,
                    observations_images=[],
                )

                logger.debug(f"🔸 Executing manual step {step_number}/{max_steps}")

                # Run one step using native smolagents pattern
                final_answer = self.agent.step(memory_step)
                self.agent.memory.steps.append(memory_step)

                # CRITICAL: Memory modification between steps (smolagents native pattern)
                if enable_memory_tracking and hasattr(memory_step, "observations"):
                    if memory_step.observations and "parameter update" in str(
                        memory_step.observations
                    ):
                        # Save design state before next step
                        memory_step.observations += "\n[MANUAL_MEMORY] Design state tracked"
                        logger.debug(f"💾 Enhanced memory tracking applied to step {step_number}")

                step_number += 1

            logger.info(
                f"✅ Manual execution completed with {len(self.agent.memory.steps)} memory steps"
            )
            return final_answer

        except Exception as e:
            logger.error(f"❌ Manual execution failed: {e}")
            raise RuntimeError(f"Manual execution error: {e}")

    # REMOVED: Manual memory parsing functions that fight against smol-agents patterns
    #
    # As described in the critique, these functions manually parse agent.memory.steps
    # treating it like a database, which is brittle and unreliable. The smol-agents
    # native solution is context-based recall where the triage agent fetches history
    # and provides it as context for the geometry agent to reason over.
    #
    # The following functions have been removed:
    # - rollback_to_previous_state() -> Use context-based rollback via triage agent
    # - get_element_original_values() -> Use get_element_history() from triage agent
    #
    # NEW PATTERN: Triage agent uses get_element_history() tool, then provides context:
    # history = get_element_history(element_id="002")
    # task = f"Based on this history: {history}, restore element 002 to original state"
    # geometry_agent(task=task)

    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about geometry agent memory usage and design activity.

        Returns:
            Dictionary with memory statistics and design metrics
        """
        try:
            from ..memory import get_memory_statistics

            stats = get_memory_statistics(self.agent)

            # Add geometry-specific context
            stats["agent_type"] = "geometry_agent"
            stats["mcp_integration"] = "enabled"
            stats["connection_status"] = (
                "persistent" if hasattr(self, "mcp_connection") else "disconnected"
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting memory statistics: {e}")
            return {"error": str(e)}

    def _create_self_history_tool(self):
        """
        Create self-history tool that allows geometry agent to access its own memory.

        This implements the true smol-agents native solution where the agent
        accesses its own memory directly rather than having external tools
        manually parse it.
        """
        from smolagents import tool

        @tool
        def get_my_element_history(element_id: str) -> str:
            """
            Get my own memory history for a specific element.

            This tool allows me to access my own conversation memory and provide
            context about previous work with an element. No manual parsing -
            I reason over my raw memory steps.

            Args:
                element_id: Element identifier to get history for (e.g., "002", "021")

            Returns:
                My own memory and reasoning about this element's history
            """
            try:
                # Access my own memory directly (no external parsing)
                if not hasattr(self.agent, "memory") or not hasattr(self.agent.memory, "steps"):
                    return f"I don't have any memory history yet."

                memory_steps = self.agent.memory.steps
                relevant_steps = []

                # Find steps that mention this element
                for step in memory_steps:
                    if hasattr(step, "observations") and step.observations:
                        if element_id in step.observations:
                            relevant_steps.append(step)

                if not relevant_steps:
                    return f"I don't have any memory about element {element_id}."

                # Let the LLM reason over the raw context instead of manual parsing
                context = f"MY MEMORY ABOUT ELEMENT {element_id}:\n\n"

                for i, step in enumerate(relevant_steps, 1):
                    context += f"Memory Step {i} (Step #{step.step_number}):\n"
                    context += f"{step.observations}\n\n"

                context += (
                    f"Found {len(relevant_steps)} memory entries about element {element_id}.\n"
                )
                context += "I can reason over this context to answer questions about this element's history."

                return context

            except Exception as e:
                return f"Error accessing my memory: {str(e)}"

        return get_my_element_history

    def __del__(self):
        """Cleanup persistent MCP connection on agent destruction."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("🔌 Persistent MCP connection closed for geometry agent")
        except Exception as e:
            logger.warning(f"⚠️ Error closing MCP connection in geometry agent: {e}")


def create_geometry_agent(
    model_name: str = "geometry",
    monitoring_callback: Optional[Any] = None,
    **kwargs,
) -> ToolCallingAgent:
    """
    Factory for creating MCP-enabled geometry agent using smolagents managed_agents pattern.

    This creates a wrapper that properly manages MCPAdapt lifecycle and returns
    a ToolCallingAgent configured for use with smolagents multi-agent coordination.

    Args:
        model_name: Model configuration name from settings
        monitoring_callback: Optional callback for real-time monitoring
        **kwargs: Additional arguments (for compatibility)

    Returns:
        ToolCallingAgent configured for managed_agents pattern
    """
    wrapper = SmolagentsGeometryAgent(
        model_name=model_name,
        monitoring_callback=monitoring_callback,
    )

    # Get the internal ToolCallingAgent
    internal_agent = wrapper.agent

    # Store reference to wrapper for cleanup purposes
    internal_agent._wrapper = wrapper

    # Agent configured for managed_agents pattern with proper name/description in constructor

    logger.info("✅ Created geometry agent configured for managed_agents pattern")
    return internal_agent


def get_geometry_system_prompt() -> str:
    """Get custom system prompt for geometry agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "geometry_agent.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")
