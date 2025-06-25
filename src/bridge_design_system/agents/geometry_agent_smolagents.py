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

            # Create persistent ToolCallingAgent with sufficient steps for error detection/fixing
            step_callbacks = [monitoring_callback] if monitoring_callback else []
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
