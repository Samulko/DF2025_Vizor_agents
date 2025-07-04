"""
Design Smolagent - Design Agent for Grasshopper

This agent is used for design tasks inside Rhino Grasshopper, leveraging MCP tools for component interaction.
"""

import json
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from src.bridge_design_system.config.logging_config import get_logger
from src.bridge_design_system.config.model_config import ModelProvider
from src.bridge_design_system.config.settings import settings

logger = get_logger(__name__)

print("[DEBUG] design_agent_test_smolagents.py loaded")


def load_found_objects_data():
    """Load found objects data from all_categories.json for use by the design agent."""
    data_path = Path(__file__).parent.parent / "data" / "all_categories.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def build_shapes_from_json(found_objects_data: dict, category: str) -> list:
    """
    Build shape vertex lists from found objects JSON data for a given category.
    Args:
        found_objects_data: The loaded JSON data.
        category: The category of shapes to extract (e.g., 'triangle', 'hexagon', etc.)
    Returns:
        List of shapes, each as a list of vertices.
    """
    if category not in found_objects_data:
        raise ValueError(f"Category '{category}' not found in data.")
    return [obj["vertices"] for obj in found_objects_data[category] if "vertices" in obj]


class DesignSmolagent:
    """
    Smolagent for bridge design tasks inside Rhino Grasshopper.

    This agent connects to the MCP server to access Grasshopper components and
    performs design operations using only the MCP tools.
    """

    def __init__(self, model_name: str = "design_smolagents", **kwargs):
        """
        Initialize the design smolagent with MCP connection and MCP tools only.

        Args:
            model_name: Model configuration name from settings
            **kwargs: Additional arguments for extensibility
        """
        self.model_name = model_name

        # Agent identification
        self.name = "design_smolagents"
        self.description = (
            "Design agent for bridge design tasks in Rhino Grasshopper using MCP tools."
        )

        # Initialize model
        self.model = ModelProvider.get_model("design", temperature=0.1)

        # MCP server configuration
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command, args=settings.mcp_stdio_args.split(","), env=None
        )

        # Establish MCP connection
        logger.info("Establishing MCP connection for design agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")

            # Load found objects data from JSON file
            self.found_objects_data = load_found_objects_data()

            # Register the new tool as-is (no functools.partial)
            all_tools = list(self.mcp_tools) + [build_shapes_from_json]

            # Create the ToolCallingAgent
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=8,
                name="design_smolagents",
                description=self.description,
            )

            # Add specialized system prompt from file
            custom_prompt = get_design_agent_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )

            # Optionally, make the data available to the agent (if needed by your framework)
            self.agent.found_objects_data = self.found_objects_data

            # Add workshop logging - just 1 line!
            from ..monitoring.workshop_logging import add_workshop_logging
            add_workshop_logging(self.agent, "design_agent")

            logger.info("Design smolagent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize design smolagent: {e}")
            raise RuntimeError(f"Design smolagent initialization failed: {e}")

    def run(self, task: str) -> Any:
        """
        Execute a design task using MCP tools.

        Args:
            task: Task description for design operation

        Returns:
            Result of the agent execution
        """
        logger.info(f"Executing design task: {task[:100]}...")

        try:
            result = self.agent.run(task)
            logger.info("Design task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Design task failed: {e}")
            raise RuntimeError(f"Design smolagent execution failed: {e}")

    def __del__(self):
        """Clean up MCP connection when agent is destroyed."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("MCP connection closed for design smolagent")
        except Exception as e:
            logger.warning(f"Error closing MCP connection: {e}")


def create_design_agent(model_name: str = "design_smolagents", **kwargs) -> ToolCallingAgent:
    """
    Factory function for creating design smolagent instances.

    Args:
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for design operations
    """
    logger.info("Creating design smolagent...")

    wrapper = DesignSmolagent(model_name=model_name, **kwargs)

    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent

    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper

    # Add workshop logging - just 1 line!
    from ..monitoring.workshop_logging import add_workshop_logging
    add_workshop_logging(internal_agent, "design_agent")

    logger.info("Design smolagent created successfully")
    return internal_agent


def demo_design_agent():
    """
    Demonstration function showing basic design agent operations.

    This function creates an agent instance and runs a simple design task
    to demonstrate the agent's capabilities.
    """
    print("Starting design smolagent demonstration...")

    try:
        agent = create_design_agent()

        demo_task = (
            "Design a structure that packs into a box form, using the provided found objects data."
        )
        result = agent.run(demo_task)

        print("Demonstration completed successfully")
        print(f"Result: {result}")

    except Exception as e:
        print(f"Demonstration failed: {e}")
        raise


def get_design_agent_system_prompt() -> str:
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "design_agent_test.md"
    if not prompt_path.exists():
        logger.warning("⚠️ Design agent system prompt not found, using default prompt")
        return """You are a design agent specialized in interactive 3D form exploration and assembly.\nYour role is to orchestrate the design-explore-refine-fabricate workflow, using a Python component in Grasshopper and the context7 database for memory/context.\n"""
    return prompt_path.read_text(encoding="utf-8")


# def get_design_agent_system_prompt() -> str:
#     """Get custom system prompt for design agent, referencing found objects data loaded from all_categories.json."""
#     return '''# Design Agent Test Scenario (with found objects data)

# ## Purpose
# This test demonstrates the design agent's ability to perform a design task using found objects data loaded from all_categories.json, without waiting for input from the geometry agent.

# ## Data Source
# The agent is provided with found objects data loaded from the file: src/bridge_design_system/data/all_categories.json. The data contains multiple categories (triangle, hexagon, other_polygons, etc.), each with a list of objects and their vertices.

# ## Design Task
# The agent is asked to:

# > Design a structure that packs into a box form, using the provided found objects data.

# ## Expected Behavior
# - The agent should use the loaded data to generate a design that arranges the pieces in a straight line.
# - The result should include a representation of the designed form (geometry and metadata).
# - No interaction with the geometry agent is required for this test.
# '''


def main():
    print("[DEBUG] main() called")
    demo_design_agent()


if __name__ == "__main__":
    main()

# Allow running as a module: python -m src.bridge_design_system.agents.design_agent_test_smolagents
if __name__.endswith("design_agent_test_smolagents"):
    main()
