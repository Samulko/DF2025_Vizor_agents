"""
Rational Smolagent - Level Checking and Correction Agent

This agent validates and corrects bridge element levels to ensure proper horizontal alignment.
It integrates with the MCP-connected Grasshopper environment to access and modify component parameters.

The agent focuses on a specific engineering task: ensuring all bridge elements have correct
horizontal orientation by checking and adjusting their direction vectors.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings

logger = get_logger(__name__)


class RationalSmolagent:
    """
    Specialized smolagent for bridge element level validation and correction.

    This agent connects to the MCP server to access Grasshopper components and
    performs level checking operations to ensure elements are properly horizontal.
    """

    def __init__(
        self,
        model_name: str = "rational",
        **kwargs,
    ):
        """
        Initialize the rational smolagent with MCP connection and custom tools.

        Args:
            model_name: Model configuration name from settings
            **kwargs: Additional arguments for extensibility
        """
        self.model_name = model_name

        # Agent identification
        self.name = "rational_agent"
        self.description = "Validates and corrects bridge element levels for proper horizontal alignment"

        # Initialize model
        self.model = ModelProvider.get_model(model_name, temperature=0.1)

        # MCP server configuration
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )

        # Establish MCP connection
        logger.info("Establishing MCP connection for rational agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")

            # Use MCP tools plus one custom analysis tool
            all_tools = list(self.mcp_tools)
            all_tools.append(self._create_analysis_tool())

            # Create the ToolCallingAgent
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=8,
                name="rational_agent",
                description=self.description,
            )

            # Add specialized system prompt from file
            custom_prompt = get_rational_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )

            logger.info("Rational smolagent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize rational smolagent: {e}")
            raise RuntimeError(f"Rational smolagent initialization failed: {e}")

    def run(self, task: str) -> Any:
        """
        Execute level checking and correction task.

        Args:
            task: Task description for level validation or correction

        Returns:
            Result of the agent execution
        """
        logger.info(f"Executing level checking task: {task[:100]}...")

        try:
            result = self.agent.run(task)
            logger.info("Level checking task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Level checking task failed: {e}")
            raise RuntimeError(f"Rational smolagent execution failed: {e}")

    def _create_analysis_tool(self):
        """
        Create custom analysis tool for structured element level assessment.

        Returns:
            Custom tool function for level analysis
        """

        @tool
        def analyze_element_level(element_id: str) -> str:
            """
            Analyze the level status of a bridge element to determine if it's horizontal.

            This tool provides structured analysis of element orientation and generates
            a report on whether the element needs level correction.

            Args:
                element_id: Element identifier to analyze (e.g., "021", "022")

            Returns:
                Analysis report of element's horizontal alignment status
            """
            try:
                logger.info(f"Analyzing level status for element {element_id}")

                return f"""
LEVEL ANALYSIS REPORT - Element {element_id}:
============================================
Element ID: {element_id}
Analysis Focus: Direction vector Z-component validation
Required State: Z-component = 0 for horizontal alignment

Next Steps:
1. Use get_python3_script to read current element parameters
2. Extract direction vector values from the code
3. Check if Z-component is zero (horizontal)
4. If not zero, use edit_python3_script to correct the direction vector
5. Verify correction with get_python3_script_errors

Status: Ready for parameter extraction and validation
                """.strip()

            except Exception as e:
                return f"Error analyzing element {element_id}: {str(e)}"

        return analyze_element_level

    def __del__(self):
        """Clean up MCP connection when agent is destroyed."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("MCP connection closed for rational smolagent")
        except Exception as e:
            logger.warning(f"Error closing MCP connection: {e}")


def get_rational_system_prompt() -> str:
    """Get custom system prompt for rational agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "rational_agent.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def create_rational_agent(
    model_name: str = "rational",
    **kwargs,
) -> ToolCallingAgent:
    """
    Factory function for creating rational smolagent instances.

    Args:
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for level checking operations
    """
    logger.info("Creating rational smolagent...")

    wrapper = RationalSmolagent(model_name=model_name, **kwargs)

    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent

    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper

    logger.info("Rational smolagent created successfully")
    return internal_agent


def demo_level_checking():
    """
    Demonstration function showing basic level checking operations.

    This function creates an agent instance and runs a simple validation task
    to demonstrate the level checking capabilities.
    """
    print("Starting rational smolagent demonstration...")

    try:
        agent = create_rational_agent()

        demo_task = "Analyze the current bridge elements and identify any that need level correction"
        result = agent.run(demo_task)

        print("Demonstration completed successfully")
        print(f"Result: {result}")

    except Exception as e:
        print(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    demo_level_checking()