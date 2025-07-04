"""
Surface Agent - Surface Shape Generation, Detection and Adjustment Agent

This agent processes a surface, determines its shape, and enables natural language adjustment of surface parameters (rows, cols, width, depth, height, flatness).
It integrates with the MCP-connected Grasshopper environment to generate and modify surfaces.
"""

from pathlib import Path
from typing import Any, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..monitoring.workshop_logging import add_workshop_logging

logger = get_logger(__name__)


class SurfaceAgent:
    """
    Specialized smolagent for surface shape generation, adjustment and detection.

    This agent connects to the MCP server to access Grasshopper components and
    performs surface analysis and adjustment operations.
    """

    def __init__(
        self, model_name: str = "surface", monitoring_callback: Optional[Any] = None, **kwargs
    ):
        """
        Initialize the surface agent with MCP connection and custom tools.

        Args:
            model_name: Model configuration name from settings
            monitoring_callback: Optional callback for monitoring agent activities
            **kwargs: Additional arguments for extensibility
        """
        self.model_name = model_name

        # Agent identification
        self.name = "surface_agent"
        self.description = (
            "Generates, analyzes and adjusts surface shapes and parameters via natural language."
        )

        # Initialize model
        self.model = ModelProvider.get_model("surface", temperature=0.1)

        # MCP server configuration
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command, args=settings.mcp_stdio_args.split(","), env=None
        )

        # Establish MCP connection
        logger.info("Establishing MCP connection for surface agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")

            # Use MCP tools plus custom analysis and adjustment tools
            all_tools = list(self.mcp_tools)
            all_tools.append(self._create_shape_analysis_tool())
            all_tools.append(self._create_surface_adjust_tool())
            all_tools.append(self._create_surface_generation_tool())

            # Prepare step_callbacks for monitoring
            step_callbacks = []
            if monitoring_callback:
                step_callbacks.append(monitoring_callback)

            # Create the ToolCallingAgent
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=8,
                name="surface_agent",
                description=self.description,
                step_callbacks=step_callbacks,
            )

            # Add specialized system prompt from file or default
            custom_prompt = get_surface_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )

            # Add workshop logging - just 1 line!
            add_workshop_logging(self.agent, "surface_agent")

            logger.info("Surface agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize surface agent: {e}")
            raise RuntimeError(f"Surface agent initialization failed: {e}")

    def run(self, task: str) -> Any:
        """
        Generate, execute surface analysis or adjustment task.

        Args:
            task: Task description for surface generation, analysis or adjustment

        Returns:
            Result of the agent execution
        """
        logger.info(f"Executing surface agent task: {task[:100]}...")

        try:
            result = self.agent.run(task)
            logger.info("Surface agent task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Surface agent task failed: {e}")
            raise RuntimeError(f"Surface agent execution failed: {e}")

    def _create_shape_analysis_tool(self):
        """
        Create custom tool for surface shape detection.

        Returns:
            Custom tool function for shape analysis
        """

        @tool
        def analyze_surface_shape(surface_id: str) -> str:
            """
            Analyze the shape of a surface and determine its type (e.g., flat, curved, saddle).

            Args:
                surface_id: Surface identifier to analyze

            Returns:
                Analysis report of the surface's shape
            Note:
                'rows' and 'columns' refer to the number of control points (control mesh density) of the surface.
            """
            try:
                logger.info(f"Analyzing shape for surface {surface_id}")
                return f"""
SURFACE SHAPE ANALYSIS REPORT - Surface {surface_id}:
============================================
Surface ID: {surface_id}
Analysis Focus: Detect surface type (flat, curved, saddle, etc.)

Control Mesh: 'rows' and 'columns' refer to the number and density of control points for the surface.

Next Steps:
1. Use get_python3_script to read current surface parameters
2. Extract control points, curvature, and other relevant values
3. Classify the surface shape
4. Report the detected shape and suggest possible adjustments

Status: Ready for parameter extraction and shape classification
                """.strip()
            except Exception as e:
                return f"Error analyzing surface {surface_id}: {str(e)}"

        return analyze_surface_shape

    def _create_surface_adjust_tool(self):
        """
        Create custom tool for surface parameter adjustment via natural language.

        Returns:
            Custom tool function for surface adjustment
        """

        @tool
        def adjust_surface_parameters(
            surface_id: str,
            rows: Optional[int] = None,
            cols: Optional[int] = None,
            width: Optional[float] = None,
            depth: Optional[float] = None,
            height: Optional[float] = None,
            flatness: Optional[float] = None,
        ) -> str:
            """
            Adjust the parameters of a surface using natural language instructions.

            Args:
                surface_id: Surface identifier to adjust
                rows: Number of control points in the row direction (optional)
                cols: Number of control points in the column direction (optional)
                width: Surface width (optional)
                depth: Surface depth (optional)
                height: Surface height (optional)
                flatness: Flatness parameter (optional)

            Returns:
                Adjustment report
            Note:
                'rows' and 'cols' control the density of the surface's control points (control mesh).
            """
            try:
                logger.info(
                    f"Adjusting surface {surface_id} with parameters: rows={rows}, cols={cols}, width={width}, depth={depth}, height={height}, flatness={flatness}"
                )
                return f"""
SURFACE ADJUSTMENT REPORT - Surface {surface_id}:
============================================
Surface ID: {surface_id}
Adjusted Parameters:
- Rows (control points): {rows}
- Columns (control points): {cols}
- Width: {width}
- Depth: {depth}
- Height: {height}
- Flatness: {flatness}

Next Steps:
1. Use edit_python3_script to update the surface parameters in Grasshopper
2. Regenerate the surface with new parameters
3. Verify the new surface shape and report any issues

Status: Adjustment instructions ready for execution
                """.strip()
            except Exception as e:
                return f"Error adjusting surface {surface_id}: {str(e)}"

        return adjust_surface_parameters

    def _create_surface_generation_tool(self):
        """
        Create custom tool for generating a surface from a natural language description.

        Returns:
            Custom tool function for surface generation
        """

        @tool
        def generate_surface_from_description(description: str) -> str:
            """
            Generate a surface in Grasshopper based on a natural language description.

            Args:
                description: Natural language description of the desired surface (e.g., "Create a surface with 8 rows, 8 columns, width 15, depth 10, height 3, and flatness 0.7.")
                Note: 'rows' and 'columns' refer to the number and density of control points for the surface (control mesh).

            Returns:
                Generation report
            """
            try:
                logger.info(f"Generating surface from description: {description}")
                return f"""
SURFACE GENERATION REPORT:
============================================
Description: {description}

Note: 'rows' and 'columns' refer to the number and density of control points for the surface (control mesh).

Next Steps:
1. Parse the description to extract surface parameters (rows, cols, width, depth, height, flatness, etc.)
2. Use edit_python3_script or create_python3_script to generate the surface in Grasshopper
3. Verify the generated surface matches the described intent

Status: Surface generation instructions ready for execution
                """.strip()
            except Exception as e:
                return f"Error generating surface from description: {str(e)}"

        return generate_surface_from_description

    def __del__(self):
        """Clean up MCP connection when agent is destroyed."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("MCP connection closed for surface agent")
        except Exception as e:
            logger.warning(f"Error closing MCP connection: {e}")


def get_surface_system_prompt() -> str:
    """Get custom system prompt for surface agent from file or use default."""
    current_file = Path(__file__)
    project_root = current_file.parent
    prompt_path = project_root / "system_prompts" / "surface_agent.md"

    if not prompt_path.exists():
        # Return a default prompt if file doesn't exist
        return """
You are a specialized agent for surface analysis and adjustment using Grasshopper via MCP.

Your primary tasks are:
- Allow users to generate surfaces by specifying rows, cols, width, depth, height, and flatness in natural language
- Detect the shape of a given surface (flat, curved, saddle, etc.)
- Allow users to adjust surfaces by specifying rows, cols, width, depth, height, and flatness in natural language
- Use analyze_surface_shape to classify the surface
- Use adjust_surface_parameters to update the surface in Grasshopper
- Always verify the result after adjustment

Be systematic, precise, and responsive to user intent in surface generation and modification.
        """.strip()
    return prompt_path.read_text(encoding="utf-8")


def create_surface_agent(
    model_name: str = "surface", monitoring_callback: Optional[Any] = None, **kwargs
) -> ToolCallingAgent:
    """
    Factory function for creating surface agent instances.

    Args:
        model_name: Model configuration name from settings
        monitoring_callback: Optional callback for monitoring agent activities
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for surface adjustment operations
    """
    logger.info("Creating surface agent...")

    wrapper = SurfaceAgent(model_name=model_name, monitoring_callback=monitoring_callback, **kwargs)

    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent

    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper

    logger.info("Surface agent created successfully")
    return internal_agent


def demo_surface_agent():
    """
    Demonstration function showing basic surface adjustment operations.

    This function creates an agent instance and runs a simple surface analysis and adjustment task.
    """
    print("Starting surface agent demonstration...")

    try:
        agent = create_surface_agent()

        demo_task = "Analyze the current surface and adjust it to have 10 rows, 10 columns, width 20, depth 10, height 5, and flatness 0.8."
        result = agent.run(demo_task)

        print("Demonstration completed successfully")
        print(f"Result: {result}")

    except Exception as e:
        print(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    demo_surface_agent()
